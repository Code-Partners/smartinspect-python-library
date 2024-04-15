from smartinspect.common.context.value_list_viewer_context import ValueListViewerContext
from smartinspect.common.viewer_id import ViewerId


class InspectorViewerContext(ValueListViewerContext):
    """
    Represents the inspector viewer in the Console which displays
    key/value pairs in an object inspector control.

    The inspector viewer in the Console interprets the
    `data of a Log Entry <LogEntry.data>` as a key/value list with
    group support like object inspectors from popular IDEs. This class
    takes care of the necessary formatting and escaping required by the
    corresponding inspector viewer in the Console.

    You can use the InspectorViewerContext class for creating custom
    log methods around Session.log_custom_context
    for sending custom data organized as grouped key/value pairs.

    .. note::
       This class is not guaranteed to be threadsafe.
    """

    def __init__(self):
        """
        Initializes an InspectorViewerContext instance.
        """
        super().__init__(ViewerId.INSPECTOR)

    def start_group(self, group: str):
        """
        Starts a new group.

        :param group: The name of the group to use.
        """
        if isinstance(group, str):
            self.append_text("[")
            self.append_text(self.escape_item(group))
            self.append_text("]\r\n")

    def escape_item(self, item: str) -> str:
        """
        Overridden. Escapes a key or a value.

        This method ensures that the escaped key or value does not contain any newline characters,
        such as the carriage return or linefeed characters.
        Furthermore, it escapes the '\\', '=', '[' and ']' characters.

        :param item: The key or value to escape.
        :returns: The escaped key or value.
        """
        return self.escape_line(item, "\\=[]")
