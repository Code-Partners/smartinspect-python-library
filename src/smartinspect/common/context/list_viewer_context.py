from smartinspect.common.context.text_context import TextContext
from smartinspect.common.viewer_id import ViewerId


class ListViewerContext(TextContext):
    """
    Represents the list viewer in the Console which can display simple lists of text data.

    The list viewer in the Console interprets the data of a Log Entry as a list. Every line in the text data
    is interpreted as one item of the list. This class takes care of the necessary formatting and escaping required
    by the corresponding list viewer in the Console.

    You can use the ListViewerContext class for creating custom log methods around LogCustomContext for sending
    custom data organized as simple lists.

    .. note::
       This class is not guaranteed to be threadsafe.
    """

    def __init__(self, viewer_id: ViewerId = ViewerId.LIST) -> None:
        """
        Initializes a ListViewerContext instance using a viewer ID.

        This constructor is intended for derived classes, such as the ValueListViewerContext class,
        which extend the capabilities of this class and use a different viewer ID.

        :param viewer_id: The viewer ID to use.
        """
        super().__init__(viewer_id)

    @staticmethod
    def escape_line(line: str = "", escape_chars: str = "") -> str:

        """
        Escapes a line.

        This method ensures that the escaped line does not
        contain characters listed in the escape_chars parameter plus
        any newline characters, such as the carriage return or
        linefeed characters.

        :param line: The line to escape.
        :param escape_chars: A string of characters which should be escaped in addition to the newline characters.
        Can be empty.
        :returns: The escaped line.
        """
        if (
                not isinstance(line, str) or
                not isinstance(escape_chars, str)
        ):
            raise TypeError("line and to_escape must be strings")

        if len(line) == 0:
            return line

        prev = ""
        result = ""

        for curr in line:
            if curr in "\r\n":
                if prev not in "\r\n":
                    # Newline characters need to be removed,
                    # they would break the list format.
                    result += " "
            elif curr in escape_chars:
                # The current character needs to be escaped as well (with the \ character).
                result += "\\" + curr
            else:
                # This character is valid, so just append it.
                result += curr
            prev = curr

        return result
