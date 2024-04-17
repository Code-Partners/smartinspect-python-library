from smartinspect.common.context.list_viewer_context import ListViewerContext
from smartinspect.common.viewer_id import ViewerId


class ValueListViewerContext(ListViewerContext):
    """
    Represents the value list viewer in the Console which can display data as a key/value list.
    .. note::
        The value list viewer in the Console interprets the data of a Log Entry as a
        simple key/value list. Every line in the text data is interpreted as
        one key/value item of the list. This class takes care of the necessary
        formatting and escaping required by the corresponding value list viewer of the
        Console.
        You can use the ValueListViewerContext class for creating custom log methods
        around Session.log_custom_context for sending custom data organized as key/value lists.
    .. note::
        This class is not guaranteed to be threadsafe.
    """

    def __init__(self, viewer_id: ViewerId = ViewerId.VALUE_LIST):
        """
        Overloaded. Initializes a ValueListViewerContext
        instance using a ViewerId.
        :param viewer_id: The viewer ID to use.
        .. note::
            This constructor is intended for derived classes, such
            as the InspectorViewerContext class, which extend the
            capabilities of this class and use a different ViewerId.
        """
        super().__init__(viewer_id)

    def append_key_value(self, key: str, value) -> None:
        """
        Appends a string value and its key.
        :param key: The key to use.
        :param value: The string value to use.
        """
        if (
                not isinstance(key, str)
        ):
            raise TypeError("arguments must be str")

        if key != "":
            self.append_text(self.escape_item(key))
            self.append_text("=")
            self.append_text(self.escape_item(value))
        self.append_text("\r\n")

    def escape_item(self, item) -> str:
        """
        Escapes a key or a value.
        This method ensures that the escaped key or value does not
        contain any newline characters, such as the carriage return
        or linefeed characters. Furthermore, it escapes the '\' and
        '=' characters.
        :param item: The key or value to escape.
        :returns: The escaped key or value.
        """
        try:
            item = str(item)
        except TypeError as e:
            item = e.args[0]
        return self.escape_line(item, "\\=")
