from typing import Any, Protocol


class CacheInterface(Protocol):

    def get(self, key: str, default: Any = None) -> Any:
        raise NotImplementedError

    def set(self, key: str, value: Any, timeout: int = None):
        raise NotImplementedError

    def delete(self, key: str):
        raise NotImplementedError
