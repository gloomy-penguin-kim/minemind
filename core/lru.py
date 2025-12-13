# core/lru.py
from collections import OrderedDict  

class LRUCache():
    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self._data = OrderedDict()

    def get(self, key): 
        if key not in self._data:
            return None
        value = self._data.pop(key)
        self._data[key] = value
        return value 

    def put(self, key, value) -> None:
        if key in self._data:
            self._data.pop(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)
