class SlycacheException(Exception):
    pass


class InvalidCacheError(SlycacheException):
    pass


class KeyFormatException(SlycacheException):
    pass


class NamespaceException(SlycacheException):
    pass
