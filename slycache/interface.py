from typing import Any, Callable, Dict, Optional, Protocol


class CacheInterface(Protocol):
    """Protocol class for the cache interface required by Slycache"""

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a value from the cache and return it or else the default value"""
        raise NotImplementedError

    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        """Set a value in the cache with the given key and timeout.

        Arguments:
            key: the cache key
            value: the cache value
            timeout: cache item timeout in seconds or None
        """
        raise NotImplementedError

    def delete(self, key: str):
        """Delete value from cache"""
        raise NotImplementedError


class KeyGenerator(Protocol):
    """Protocol for a key generator class."""

    @staticmethod
    def validate(template: str, func: Callable):
        """Validate a key template.

        Arguments:
            template: key template
            func: the decorated function

        Raises:
            ValueError: if the template is not validated
        """
        raise NotImplementedError

    @staticmethod
    def generate(prefix: Optional[str], template: str, func: Callable, call_args: Dict) -> str:
        """Generate a key for use in a cache operation.

        Arguments:
            prefix: the prefix to suffix the key with
            template: the key template
            func: the decorated function
            call_args: dictionary of arguments that were used in the function invocation

        Returns:
            str: The generated key
        """
