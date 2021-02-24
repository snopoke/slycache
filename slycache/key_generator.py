import inspect


class StringFormatKeyGenerator:
    """Key"""

    @staticmethod
    def validate(template, fn):  # pylint: disable=unused-argument
        # TODO: parse key to check params  # pylint: disable=fixme
        # arg_names = inspect.getfullargspec(func).args
        # vary_on = [part.split('.') for part in vary_on]
        # vary_on = [(part[0], tuple(part[1:])) for part in vary_on]
        # for arg, attrs in vary_on:
        #     if arg not in arg_names:
        #         raise ValueError(
        #             'We cannot vary on "{}" because the function {} has '
        #             'no such argument'.format(arg, self.fn.__name__)
        #         )

        if template and not isinstance(template, str):
            raise ValueError(f"'key' must be None or a string: {template}")

    @staticmethod
    def generate(namespace, key_template, fn, call_args) -> str:
        arg_names = inspect.getfullargspec(fn).args
        valid_args = {name: call_args[name] for name in arg_names}
        return generate_key(namespace, key_template, valid_args)


def generate_key(namespace, key_template, call_args):
    template_format = key_template.format(**call_args)
    return template_format if namespace is None else f"{namespace}:{template_format}"
