from smartinspect.common.context import ListViewerContext
from smartinspect.common.viewer_id import ViewerId


class TableViewerContext(ListViewerContext):
    """
    Represents the table viewer in the Console which can display text
    data as a table.

    The table viewer in the Console interprets the
    data of a Log Entry as a table. This class
    takes care of the necessary formatting and escaping required by
    the corresponding table viewer in the Console.

    You can use the TableViewerContext class for creating custom
    log methods around Session.log_custom_context
    for sending custom data organized as tables.

    .. note::
       This class is not guaranteed to be threadsafe.
    """

    def __init__(self) -> None:
        """
        Initializes a TableViewerContext instance.
        """
        super().__init__(ViewerId.TABLE)
        self.__line_start: bool = True

    def append_header(self, header: str) -> None:
        """
        Appends a header to the text data.
      
        :param header: The header to append."""

        self.append_line(header)
        self.append_line("")

    def add_row_entry(self, entry: str) -> None:
        """
            Adds a string entry to the current row.

            :param entry: The string entry to add.
        """
        if self.__line_start:
            self.__line_start = False
        else:
            self.append_text(", ")
        self.append_text(self.__escape_csv_entry(str(entry)))

    @staticmethod
    def __escape_csv_entry(entry: str) -> str:
        if len(entry) == 0:
            return entry

        result = ["\""]

        for letter in entry:
            if letter.isspace():
                # Newline characters need to be escaped,
                # they would break the csv format.
                result.append(" ")
            elif letter == '"':
                # '"' characters are used to surround entries
                # in the csv format, so they need to be escaped.
                result.append("\"\"")
            else:
                # This character is valid, so just append it.
                result.append(letter)

        result.append("\"")
        return "".join(result)

    def begin_row(self) -> None:
        """Begins a new row."""
        self.__line_start = True

    def end_row(self) -> None:
        """Ends the current row."""
        self.append_line("")
