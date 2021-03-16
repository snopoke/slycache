import base64
import datetime
import decimal
import hashlib
import inspect
import json
import uuid
from inspect import Parameter
from numbers import Number
from string import Formatter

from pytz import utc

from slycache.exceptions import KeyFormatException, NamespaceException

MUTABLE_TYPES = (list, dict, set, bytearray)

try:
    from _string import formatter_field_name_split
except ImportError:

    def formatter_field_name_split(field_name):
        return field_name._formatter_field_name_split()  # pylint: disable=protected-access


class StringFormatKeyGenerator:
    """Key Generator that generates a key from a string template
    using the Python string Formatter class.
    """

    def __init__(self, max_key_length=250, max_namespace_length=60):
        self.max_key_length = max_key_length
        self.max_namespace_length = max_namespace_length

    def validate(self, template, func):  # pylint: disable=unused-argument
        if template is None:
            return

        sig = inspect.signature(func)
        sig_str = f"{func.__name__}{sig}"
        if not isinstance(template, str):
            raise KeyFormatException(f"'key' must be None or a string: {template}")

        if not template:
            raise KeyFormatException(f"'key' must not be empty: function='{sig_str}'")

        args = get_arg_names(sig=sig)
        for literal_text, field_name, _, _ in Formatter().parse(template):
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

    def generate(self, namespace, key_template, func, call_args) -> str:
        args = get_arg_names(func=func)
        valid_args = {name: call_args[name] for name in args if name in call_args}
        if namespace is None:
            namespace = generate_namespace(func, args, self.max_namespace_length)
        elif not namespace:
            raise NamespaceException("Namespace must not be empty")
        return generate_key(namespace, key_template, valid_args, max_len=self.max_key_length)


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

    def format_field(self, value, format_spec):
        if not format_spec:
            return self._format_field(value)
        return super().format_field(value, format_spec)

    def _format_field(self, value):
        if value is None:
            return "None"
        if isinstance(value, (str, bool, Number, bytes)):
            return super().format_field(value, "")
        ret = handle_basic_types(value)
        if ret is not None:
            return ret
        return hash_data(value)


def hash_data(data):
    serialized = json.dumps(data, sort_keys=True, cls=SlycacheJSONEncoder)
    hashed = hashlib.sha1(serialized.encode("utf8"))
    return base64.urlsafe_b64encode(hashed.digest()).decode().rstrip("=")


class SlycacheJSONEncoder(json.JSONEncoder):

    def default(self, o):
        r = handle_basic_types(o)
        if r is not None:
            return r

        if isinstance(o, (set, frozenset)):
            return ["__set__"] + sorted(list(o))

        try:
            return super().default(o)
        except TypeError:
            raise ValueError(f"Objects of type '{type(o)}' can not be used in keys")


def handle_basic_types(o):  # pylint: disable=too-many-return-statements
    if isinstance(o, datetime.datetime):
        if o.utcoffset() is not None:
            return o.astimezone(utc).isoformat()
        return o.isoformat()
    if isinstance(o, datetime.date):
        return o.isoformat()
    if isinstance(o, datetime.time):
        if o.utcoffset() is not None:
            raise ValueError("Timezone-aware times can not be used in keys")
        return o.isoformat()
    if isinstance(o, datetime.timedelta):
        return str(o.total_seconds())
    if isinstance(o, (decimal.Decimal, uuid.UUID)):
        return str(o)
    return None
