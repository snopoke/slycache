"""In memory cache backed by a dictionary. Only used for testing. Not thread safe."""
from datetime import datetime, timedelta
from typing import Any, NamedTuple, Optional


class Entry(NamedTuple):
    key: str
    value: Any
    timeout: Optional[int]
    cutoff: Optional[datetime]

    @property
    def expired(self):
        return self.cutoff and self.cutoff <= datetime.utcnow()


class DictCache:
    missing = object()

    def __init__(self, alias: str):
        self._alias = alias
        self._cache = {}
        self.hits = 0
        self.misses = 0

    def clear(self):
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    def init(self, data: dict):
        for key, value in data.items():
            self.set(key, value)

    def get_entry(self, key):
        return self._cache[key]

    def get(self, key: str, default: Any = None) -> Any:
        entry = self._cache.get(key, self.missing)
        if entry is self.missing or entry.expired:
            self.misses += 1
            return default
        self.hits += 1
        return entry.value

    def set(self, key: str, value: Any, timeout: int = None):
        entry = Entry(key, value, timeout, timeout and datetime.utcnow() + timedelta(seconds=timeout))
        self._cache[key] = entry

    def delete(self, key: str):
        try:
            del self._cache[key]
        except KeyError:
            pass

    def __repr__(self):
        return f"DictCache({self._alias}, {self._cache})"

    def __contains__(self, key):
        return key in self._cache
