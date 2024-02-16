import time
from math import ceil

from .._gtk4 import GLib

class Refresher:
    def __init__(self, refresh_rate_ms : int = 1000):
        self.__refresh_rate_ms = refresh_rate_ms
        self.__last_refresh = time.time()

    def set_refresh_rate(self, v : int):
        v = int(v)
        assert v > 0
        self.__refresh_rate_ms = v

    def refresh(self):
        """User code here!"""
        raise NotImplementedError(f"Subclass {type(self).__name__} does not implement the refresh function")

    def _refresh_entrypoint(self):
        self.refresh()
        self.start_refresh()

    def start_refresh(self):
        next_refresh = self.__last_refresh
        now = time.time()
        while next_refresh < now:
            next_refresh += (float(self.__refresh_rate_ms) / 1000.0)

        refresh_time_ms = int(ceil(1000.0 * (next_refresh - now)))
        self.__last_refresh = next_refresh

        GLib.timeout_add(refresh_time_ms, self._refresh_entrypoint)
