from common.context.text_context import TextContext
from common.viewer_id import ViewerId


class ListViewerContext(TextContext):
    def __init__(self, viewer_id: ViewerId = ViewerId.LIST) -> None:
        super().__init__(viewer_id)

    @staticmethod
    def escape_line(line: str = "", escape_chars: str = "") -> str:
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
