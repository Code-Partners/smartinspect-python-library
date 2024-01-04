from io import StringIO

from common.context.viewer_context import ViewerContext
from common.viewer_id import ViewerId


class TextContext(ViewerContext):
    __BOM = b'\xef\xbb\xbf'

    def __init__(self, viewer_id: ViewerId):
        super().__init__(viewer_id)
        self.__data: str = ""

    @property
    def viewer_data(self) -> bytes:
        try:
            data = bytes(self.__data, encoding="UTF-8")
            result = self.__BOM + data
            return result
        except TypeError:
            return bytes()

    def reset_data(self) -> None:
        self.__data = ""

    def load_from_file(self, file_name: str) -> None:
        if not isinstance(file_name, str):
            raise TypeError("file_name argument must be a string")

        else:
            with open(file_name, 'r', encoding="utf-8") as file:
                string = file.read()
                self.__data += string

    def load_from_stream(self, input_stream):
        if not isinstance(input_stream, StringIO):
            raise TypeError("input_stream argument must be a StringIO")
        else:
            with input_stream as stream:
                string = stream.read()
                self.__data += string

    @staticmethod
    def _escape_line(line: str):
        if not isinstance(line, str):
            raise TypeError("line must be a string")
        return line

    def append_line(self, line: str):
        if not isinstance(line, str):
            raise TypeError("line must be a string")

        self.__data += line + "\r\n"

    def append_text(self, text: str):
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        self.__data += text

    def load_from_text(self, text: str):
        if not isinstance(text, str):
            raise TypeError("escape line must be a string")
        self.reset_data()
        self.__data += text

    def close(self) -> None:
        self.reset_data()
