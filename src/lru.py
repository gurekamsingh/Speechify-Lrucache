#!/usr/bin/env python3
from collections import OrderedDict
from typing import Any, Optional

class LRUCache:
    """
    A Least Recently Used (LRU) cache keeps items in the cache until it reaches its size
    and/or item limit (only item in our case). In which case, it removes an item that was accessed
    least recently.
    An item is considered accessed whenever `has`, `get`, or `set` is called with its key.

    Implement the LRU cache here and use the unit tests to check your implementation.
    """

    def __init__(self, item_limit: int):
        self.cache = OrderedDict()
        self.item_limit = item_limit

    def has(self, key: str) -> bool:
        if key in self.cache:
            self.cache.move_to_end(key)
            return True 
        return False

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
            self.cache[key] = value
        else:
            if len(self.cache) >= self.item_limit:
                self.cache.popitem(last=False)
            self.cache[key] = value
