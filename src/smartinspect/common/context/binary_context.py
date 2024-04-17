from io import BytesIO

from smartinspect.common.context.viewer_context import ViewerContext
from smartinspect.common.viewer_id import ViewerId


class BinaryContext(ViewerContext):
    """
    This is the base class for all viewer contexts, which deal with
    binary data. A viewer context is the library-side representation
    of a viewer in the Console.

    .. note::
       This class is not guaranteed to be threadsafe.
    """

    def __init__(self, viewer_id: ViewerId):
        """
        Initializes a BinaryContext instance.

        :param viewer_id: The viewer ID to use.
        """
        super().__init__(viewer_id)
        self.__data: BytesIO = BytesIO()

    @property
    def viewer_data(self) -> bytes:
        """
        Overridden. Returns the actual binary data which will be
        displayed in the viewer specified by the ViewerId.

        :rtype: binary
        """
        return self.__data.getvalue()

    def reset_data(self):
        """
        Resets the internal data stream.

        .. note::
            This method is intended to reset the internal data stream
            if custom handling of data is needed by derived classes.
        """

        self.__data.seek(0)
        self.__data.truncate()

    def load_from_file(self, filename: str):
        """
        Loads the binary data from a file.

        :param filename: The name of the file to load the binary data from.
        :raises ValueError: The filename string is empty.
        """

        if filename == "":
            raise ValueError("filename not provided")
        else:
            with open(filename, "rb") as file:
                content = file.read()
                self.reset_data()
                self.__data.write(content)

    def append_bytes(self, bytestring: (bytes, bytearray), offset: int = 0, length: int = 0):
        """
        Overloaded. Appends a buffer. Lets you specify the offset in
        the buffer and the amount of bytes to append.

        :param bytestring: The buffer to append.
        :param offset: The offset at which to begin appending.
        :param length: The number of bytes to append.

        :raises TypeError: if type requirements are not met by the arguments
        """

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
        """
        Overridden. Releases any resources.
        """

        if not self.__data.closed:
            try:
                self.__data.close()
            except OSError:
                pass
        # we are not expecting an exception

    def load_from_stream(self, stream):
        """
            Loads the binary data from a stream.

            :param stream: The stream to load the binary data from.
        """

        self.reset_data()
        self.__data.write(stream)
