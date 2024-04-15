from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    pass

from smartinspect.common.level import Level
from smartinspect.common.lookup_table import LookupTable

Self = TypeVar("Self", bound="ProtocolConnectionStringBuilder")


class ProtocolConnectionStringBuilder:
    def __init__(self, parent: "ConnectionStringBuilder"):
        self._parent = parent

    def end_protocol(self) -> "ConnectionStringBuilder":
        self._parent.cb.end_protocol()
        return self._parent

    def set_level(self, level: Level) -> Self:
        self._parent.cb.add_option("level", level)
        return self

    def set_caption(self, caption: str) -> Self:
        self._parent.cb.add_option("caption", caption)
        return self

    def set_reconnect(self, reconnect: bool) -> Self:
        self._parent.cb.add_option("reconnect", reconnect)
        return self

    def set_reconnect_interval(self, reconnect_interval: int) -> Self:
        self._parent.cb.add_option("reconnect.interval", reconnect_interval)
        return self

    def set_backlog_enabled(self, backlog_enabled: bool) -> Self:
        self._parent.cb.add_option("backlog.enabled", backlog_enabled)
        return self

    def set_backlog_queue(self, backlog_queue: str) -> Self:
        size_in_bytes = LookupTable.size_to_int(backlog_queue, 0)
        self._parent.cb.add_option("backlog.queue", int(size_in_bytes / 1024))
        return self

    def set_backlog_flushon(self, backlog_flushon: Level) -> Self:
        self._parent.cb.add_option("backlog.flushon", backlog_flushon)
        return self

    def set_backlog_keepopen(self, backlog_keepopen: bool) -> Self:
        self._parent.cb.add_option("backlog.keepopen", backlog_keepopen)
        return self

    def set_async_enabled(self, async_enabled: bool) -> Self:
        self._parent.cb.add_option("async.enabled", async_enabled)
        return self

    def set_async_throttle(self, async_throttle: bool) -> Self:
        self._parent.cb.add_option("async.throttle", async_throttle)
        return self

    def set_async_queue(self, async_queue: str) -> Self:
        size_in_bytes = LookupTable.size_to_int(async_queue, 0)
        self._parent.cb.add_option("async.queue", int(size_in_bytes / 1024))
        return self

    def set_async_clear_on_disconnect(self, async_clear_on_disconnect: bool) -> Self:
        self._parent.cb.add_option("async.clearondisconnect", async_clear_on_disconnect)
        return self
