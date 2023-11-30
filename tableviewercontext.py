from common.list_viewer_context import ListViewerContext
from common.viewer_id import ViewerId


class TableViewerContext(ListViewerContext):
    def __init__(self) -> None:
        super().__init__(ViewerId.TABLE)
        self.__line_start: bool = True

    def append_header(self, header: str) -> None:
        self.append_line(header)
        self.append_line("")

    def add_row_entry(self, entry: str) -> None:
        if self.__line_start:
            self.__line_start = False
        else:
            self.append_text(", ")
        self.append_text(self.__escape_CSV_entry(str(entry)))

    @staticmethod
    def __escape_CSV_entry(entry: str) -> str:
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
        self.__line_start = True

    def end_row(self) -> None:
        self.append_line("")
