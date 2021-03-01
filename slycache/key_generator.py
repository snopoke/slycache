import base64
import datetime
import hashlib
import inspect
from inspect import Parameter
from string import Formatter

from pytz import utc

from slycache.exceptions import KeyFormatException, NamespaceException

MUTABLE_TYPES = (list, dict, set, bytearray)

try:
    from _string import formatter_field_name_split
except ImportError:

    def formatter_field_name_split(field_name):
        return field_name._formatter_field_name_split()


class StringFormatKeyGenerator:
    """Key Generator that generates a key from a string template
    using the Python string Formatter class.
    """

    @staticmethod
    def validate(template, func):  # pylint: disable=unused-argument
        if template is None:
            return

        sig = inspect.signature(func)
        sig_str = f"{func.__name__}{sig}"
        if not isinstance(template, str):
            raise KeyFormatException(f"'key' must be None or a string: {template}")

        if not template:
            raise KeyFormatException(f"'key' must not be empty: function='{sig_str}'")

        args = get_arg_names(sig=sig)
        for literal_text, field_name, format_spec, conversion in Formatter().parse(template):
            if literal_text:
                continue

            if field_name is not None:
                if not field_name:
                    raise KeyFormatException(f"Blank field in key: function='{template}'")

                if field_name.isdigit():
                    raise KeyFormatException("Field numbering not supported. Use field names.")

                first, _ = formatter_field_name_split(field_name)
                if first not in args:
                    raise KeyFormatException(f"Argument '{first}' is not present in function: '{sig_str}'")

                param = sig.parameters[first]
                default = param.default
                if default is not None and default is not Parameter.empty and isinstance(default, MUTABLE_TYPES):
                    raise KeyFormatException(
                        f"Mutable argument type not permitted for caching: '{first}={default}'. Function='{sig_str}'"
                    )

    @staticmethod
    def generate(namespace, key_template, func, call_args) -> str:
        args = get_arg_names(func=func)
        valid_args = {name: call_args[name] for name in args if name in call_args}
        if namespace is None:
            namespace = generate_namespace(func, args)
        elif not namespace:
            raise NamespaceException("Namespace must not be empty")
        return generate_key(namespace, key_template, valid_args, max_len=250)


def get_arg_names(func=None, sig=None):
    sig = sig or inspect.signature(func)
    return _get_named_args(sig)


def _get_named_args(sig):
    args = []
    for param in sig.parameters.values():
        kind = param.kind
        name = param.name

        if kind is Parameter.POSITIONAL_ONLY:
            args.append(name)
        if kind is Parameter.POSITIONAL_OR_KEYWORD:
            args.append(name)
        elif kind is Parameter.KEYWORD_ONLY:
            args.append(name)

    return args


def generate_namespace(func, named_args: list, max_len=60) -> str:
    """Generate a namespace for the given function"""
    args = ",".join(named_args)
    full_namespace = f"{func.__name__}:{args}"
    if len(full_namespace) <= max_len:
        return full_namespace
    return full_namespace[:max_len - 8] + _hash(full_namespace, 8)


def _hash(value, length=8):
    return hashlib.md5(value.encode('utf-8')).hexdigest()[-length:]


def generate_key(namespace, key_template, call_args, max_len=250):
    key = StringFormatter().format(key_template, **call_args)
    if len(key) + len(namespace) > int(max_len):
        key = base64.urlsafe_b64encode(hashlib.sha1(key.encode("utf8")).digest()).decode().rstrip("=")
    return key if namespace is None else f"{namespace}:{key}"


class StringFormatter(Formatter):
    """Custom formatter to provide more sensible default format for datetimes.
    """

    def convert_field(self, value, conversion):
        if conversion is None:
            if isinstance(value, datetime.datetime):
                if value.tzinfo:
                    return value.astimezone(utc).isoformat()
            return value
        return super().convert_field(value, conversion)

    def format_field(self, value, format_spec):
        if not format_spec:
            return self._format_field(value)
        return super().format_field(value, format_spec)

    def _format_field(self, value):
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        if isinstance(value, (tuple, list, set, frozenset, dict)):
            return make_hash(value)
        return super().format_field(value, "")


def make_hash(o, hash_factory=hashlib.sha1):
    # https://stackoverflow.com/a/42151923/632517
    hasher = hash_factory()
    hasher.update(repr(make_hashable(o)).encode())
    return base64.urlsafe_b64encode(hasher.digest()).decode().rstrip("=")


def make_hashable(o):
    if isinstance(o, (tuple, list)):
        return (type(o),) + tuple(make_hashable(e) for e in o)

    if isinstance(o, dict):
        return (type(o),) + tuple(sorted((k, make_hashable(v)) for k, v in o.items()))

    if isinstance(o, (set, frozenset)):
        return (type(o),) + tuple(sorted(make_hashable(e) for e in o))

    return format(o)
