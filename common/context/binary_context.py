from io import BytesIO

from common.context.viewer_context import ViewerContext
from common.viewer_id import ViewerId


class BinaryContext(ViewerContext):
    def __init__(self, viewer_id: ViewerId):
        super().__init__(viewer_id)
        self.__data: BytesIO = BytesIO()

    @property
    def viewer_data(self):
        return self.__data.getvalue()

    def reset_data(self):
        self.__data.seek(0)
        self.__data.truncate()

    def load_from_file(self, filename: str):
        if filename == "":
            raise ValueError("filename not provided")
        else:
            with open(filename, "rb") as file:
                content = file.read()
                self.reset_data()
                self.__data.write(content)

    def append_bytes(self, bytestring: (bytes, bytearray), offset: int = 0, length: int = 0):
        if not isinstance(bytestring, bytes) and \
                not isinstance(bytestring, bytes):
            raise TypeError("bytestring must be bytes sequence")
        if not isinstance(offset, int):
            raise TypeError("offset must be an integer")
        if not isinstance(length, int):
            raise TypeError("length must be an integer")

        if length == 0:
            length = len(bytestring)

        self.__data.write(bytestring[offset: offset + length])

    def close(self) -> None:
        if not self.__data.closed:
            try:
                self.__data.close()
            except OSError as e:
                pass
        # we are not expecting an exception

    def load_from_stream(self, stream):
        self.reset_data()
        self.__data.write(stream)
