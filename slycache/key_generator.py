import datetime
import hashlib
import inspect
from inspect import Parameter
from string import Formatter

from pytz import utc

MUTABLE_TYPES = (list, dict, set, bytearray)

try:
    from _string import formatter_field_name_split
except ImportError:

    def formatter_field_name_split(field_name):
        return field_name._formatter_field_name_split()


class KeyFormatException(Exception):
    pass


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
                    raise KeyFormatException(f"Argument '{first}' in key not present in function: '{sig_str}'")

                param = sig.parameters[first]
                default = param.default
                if default is not None and default is not Parameter.empty and isinstance(default, MUTABLE_TYPES):
                    raise KeyFormatException(
                        f"Mutable argument type not permitted for caching: '{first}={default}'. Function='{sig_str}'"
                    )

    @staticmethod
    def generate(namespace, key_template, func, call_args) -> str:
        args = get_arg_names(func=func)
        valid_args = {name: call_args[name] for name in args}
        if namespace is None:
            namespace = generate_namespace(func, args)
        return generate_key(namespace, key_template, valid_args)


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


def generate_key(namespace, key_template, call_args):
    template_format = StringFormatter().format(key_template, **call_args)
    return template_format if namespace is None else f"{namespace}:{template_format}"


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
        if not format_spec and isinstance(value, datetime.datetime):
            return value.isoformat()
        return super().format_field(value, format_spec)
