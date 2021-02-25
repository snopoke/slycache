import hashlib
import inspect
from inspect import FullArgSpec
from string import Formatter


class StringFormatKeyGenerator:
    """Key Generator that generates a key from a string template
    using the Python string Formatter class.
    """

    @staticmethod
    def validate(template, func):  # pylint: disable=unused-argument
        # TODO: parse key to check params  # pylint: disable=fixme
        # Formatter().parse(template)

        if template and not isinstance(template, str):
            raise ValueError(f"'key' must be None or a string: {template}")

    @staticmethod
    def generate(namespace, key_template, func, call_args) -> str:
        arg_spec = inspect.getfullargspec(func)
        valid_args = {name: call_args[name] for name in arg_spec.args + arg_spec.kwonlyargs}
        if namespace is None:
            namespace = generate_namespace(func, arg_spec)
        return generate_key(namespace, key_template, valid_args)


def generate_namespace(func, arg_spec: FullArgSpec, max_len=60) -> str:
    """Generate a namespace for the given function"""
    args = ",".join(arg_spec.args + arg_spec.kwonlyargs)
    full_namespace = f"{func.__name__}:{args}"
    if len(full_namespace) <= max_len:
        return full_namespace
    return full_namespace[:max_len - 8] + _hash(full_namespace, 8)


def _hash(value, length=8):
    return hashlib.md5(value.encode('utf-8')).hexdigest()[-length:]


def generate_key(namespace, key_template, call_args):
    template_format = key_template.format(**call_args)
    return template_format if namespace is None else f"{namespace}:{template_format}"
