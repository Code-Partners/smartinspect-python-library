from io import StringIO

from smartinspect.common.context.viewer_context import ViewerContext
from smartinspect.common.viewer_id import ViewerId


class TextContext(ViewerContext):
    """Is the base class for all viewer contexts, which deal with text
    data. A viewer context is the library-side representation of a
    viewer in the Console.

    .. note::
       This class is not guaranteed to be threadsafe.
    """
    __BOM = b'\xef\xbb\xbf'

    def __init__(self, viewer_id: ViewerId):
        """
        Initializes a TextContent instance.
        :param viewer_id: The ViewerID to use.
        """
        super().__init__(viewer_id)
        self.__data: str = ""

    @property
    def viewer_data(self) -> bytes:
        """
        Overridden. Returns the actual data which will be displayed
        in the viewer specified by the ViewerId.
        """
        try:
            data = bytes(self.__data, encoding="UTF-8")
            result = self.__BOM + data
            return result
        except TypeError:
            return bytes()

    def reset_data(self) -> None:
        """
        Resets the internal data.
        This method is intended to reset the internal text data if
        custom handling of data is needed by derived classes.
        """
        self.__data = ""

    def load_from_file(self, file_name: str) -> None:
        """
        Loads the text from a file.
        :param file_name: The name of the file to load the text from.
        :raises TypeError: The file_name argument is not str.
        """
        if not isinstance(file_name, str):
            raise TypeError("file_name argument must be a string")

        else:
            with open(file_name, 'r', encoding="utf-8") as file:
                string = file.read()
                self.__data += string

    def load_from_stream(self, input_stream: StringIO):
        """
        Loads the text from a stream.
        If the supplied stream supports seeking then the entire
        stream content will be read and the stream position will be
        restored correctly. Otherwise, the data will be read from the
        current position to the end and the original position can not be restored.
        :param input_stream: The stream to load the text from.
        :raises TypeError: The stream argument is not a StringIO.
        """
        if not isinstance(input_stream, StringIO):
            raise TypeError("input_stream argument must be a StringIO")
        else:
            with input_stream as stream:
                string = stream.read()
                self.__data += string

    @staticmethod
    def _escape_line(line: str):
        """
        Escapes a line.
        If overridden in derived classes, this method escapes a
        line depending on the viewer format used. The default
        implementation does no escaping.
        :param line: The line to escape.
        :returns: The escaped line.
        """
        pass
        if not isinstance(line, str):
            raise TypeError("line must be a string")
        return line

    def append_line(self, line: str):
        """
        Appends a line to the text data.
        This method appends the supplied line and a carriage return
        + linefeed character to the internal text data after it has
        been escaped by the EscapeLine method.
        :param line: The line to append.
        :raises TypeError: The line argument is not str.
        """
        if not isinstance(line, str):
            raise TypeError("line must be a string")

        self.__data += line + "\r\n"

    def append_text(self, text: str):
        """
        Appends text.
        :param text: The text to append.
        :raises TypeError: The text argument is not str.
        """

        if not isinstance(text, str):
            raise TypeError("text must be a string")

        self.__data += text

    def load_from_text(self, text: str):
        """
        Loads the text.
        :param text: The text to load.
        :raises TypeError: The text argument is not str.
        """
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        self.reset_data()
        self.__data += text

    def close(self) -> None:
        """Overridden. Releases any resources."""
        self.reset_data()
