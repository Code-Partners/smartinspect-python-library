from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    pass

from smartinspect.connections.builders.protocol_connection_string_builder import ProtocolConnectionStringBuilder

Self = TypeVar("Self", bound="PipeProtocolConnectionStringBuilder")


class PipeProtocolConnectionStringBuilder(ProtocolConnectionStringBuilder):
    def __init__(self, parent: "ConnectionStringBuilder"):
        super().__init__(parent)

    def set_pipe_name(self, pipe_name: str) -> Self:
        self._parent.cb.add_option("pipename", pipe_name)
        return self
