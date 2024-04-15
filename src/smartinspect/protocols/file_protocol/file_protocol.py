import logging
import os
import struct
import time
import typing
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes

from smartinspect.common.exceptions import ProtocolError
from smartinspect.common.file_helper import FileHelper
from smartinspect.common.file_rotate import FileRotate
from smartinspect.common.file_rotater import FileRotater
from smartinspect.connections.connections_builder import ConnectionsBuilder
from smartinspect.formatters.binary_formatter import BinaryFormatter
from smartinspect.packets.packet import Packet
from smartinspect.protocols.file_protocol.ciphered_io import CipheredIO
from smartinspect.protocols.file_protocol.si_cipher import SICipher
from smartinspect.protocols.protocol import Protocol

logger = logging.getLogger(__name__)


class FileProtocol(Protocol):
    """The standard SmartInspect protocol for writing log packets to a log file.
    FileProtocol is the base class for all protocol classes which deal with log files.
    By default, it uses the binary log file format which is compatible to the Console.
    Derived classes can change this behavior. For example, for a simple protocol which
    is capable of creating plain text files, see the TextProtocol class.
    The file protocol supports a variety of options, such as log rotation (by size and date),
    encryption and I/O buffers. For a complete list of available protocol options, please
    have a look at the .is_valid_option() method.
    The public members of this class are threadsafe.
    """
    _KEY_SIZE: int = 16
    _BUFFER_SIZE: int = 0x2000
    _SILE: bytes = b"SILE"
    _SILF: bytes = b"SILF"

    def __init__(self):
        """
        Initializes a FileProtocol instance. For a list
        of available file protocol options, please refer to the
        is_valid_option() method.
        """
        super().__init__()
        self._stream: typing.Optional[typing.BinaryIO] = None
        self._rotater: FileRotater = FileRotater()
        self._formatter: typing.Optional[BinaryFormatter] = None
        self._filename: str = ""
        self._append: bool = False
        self._io_buffer: int = 0
        self._io_buffer_counter: int = 0
        self._max_size: int = 0
        self._rotate: FileRotate = FileRotate.NO_ROTATE
        self._max_parts: int = 0
        self._key: typing.Optional[bytes] = None

    @staticmethod
    def _get_name() -> str:
        """
        Overridden.Returns "file".
        Derived classes can change this behavior by overriding this method.
        :return "file"
        """
        return "file"

    def _get_formatter(self) -> BinaryFormatter:
        """
        Returns the formatter for this log file protocol.
        Notes:
            The standard implementation of this method returns an instance
            of the BinaryFormatter class. Derived classes can change this
            behavior by overriding this method.
        """
        if self._formatter is None:
            self._formatter = BinaryFormatter()

        return self._formatter

    @staticmethod
    def _get_default_filename() -> str:
        """
        Returns the default filename for this log file protocol.
        .. note::
           The standard implementation of this method returns the string "log.sil".
           Derived classes can change this behavior by overriding this method.
        :return: The default filename for this log file protocol.
        """
        return "log.sil"

    @staticmethod
    def _get_stream(stream: typing.BinaryIO) -> typing.BinaryIO:
        """
        Intended to provide a wrapper stream for the underlying file stream.
        This method can be used by custom protocol implementers to wrap
        the underlying file stream into a filter stream.
        By default, this method simply returns the passed stream argument.
        :param stream: The underlying file stream.
        :return: The wrapper stream.
        """
        return stream

    def _is_valid_option(self, option_name: str) -> bool:
        """
        Overridden. Validates if a protocol option is supported.
        The following table lists all valid options, their default
        values and descriptions for the file protocol.

        ===============  ==========  ===================================================================================
        Valid Options    Default     Description
        ===============  ==========  ===================================================================================
        append           False       Specifies if new packets should be appended to the destination file instead of
                                     overwriting the file first.
        buffer           0           Specifies the I/O buffer size in kilobytes. It is possible to specify size units
                                     like this: "1 MB". Supported units are "KB",
                                     "MB" and "GB". A value of 0 disables this feature. Enabling the I/O buffering
                                     greatly improves the logging performance but has
                                     the disadvantage that log packets are temporarily stored in memory and are not
                                     immediately written to disk.
        encrypt          False       Specifies if the resulting log file should be encrypted. Note
                                     that the 'append' option cannot be used with encryption enabled.
                                     If encryption is enabled the 'append' option has no effect.
        filename         [varies]    Specifies the filename of the log.
        key              [empty]     Specifies the secret encryption key as string if the 'encrypt' option is enabled.
        maxparts         [varies]    Specifies the maximum amount of log files at any given time when log rotating is
                                     enabled or the maxsize option is set. Specify
                                     0 for no limit. See below for information on the default value for this option.
        maxsize          0           Specifies the maximum size of a log file in kilobytes. When this size is reached,
                                     the current log file is closed and a new file is opened. The maximum amount of
                                     log files can be set with the maxparts option.
                                     It is possible to specify size units
                                     like this: "1 MB". Supported units are "KB", "MB" and "GB". A value of 0 disables
                                     this feature.
        rotate           none        Specifies the rotate mode for log files. Please see below for a list of available
                                     values. A value of "none" disables this feature. The maximum amount of
                                     log files can be set with the maxparts option.
        ===============  ==========  ===================================================================================

        The reset of the docstring contains useful contextual information on how to use File Protocol.

        Examples:
        -------
            - connection_string = "file()"
            - connection_string = "file(filename='log.sil', append=True)"
            - connection_string = "file(filename='log.sil')"
            - connection_string = "file(maxsize='16MB', maxparts=5)"
            - connection_string = "file(rotate=weekly)" 
            - connection_string = "file(encrypt=True, key='sixteen_byte_key')"

        :param option_name: The option name to validate.
        :return: True if the option is supported and False otherwise.
        """
        is_valid = bool(option_name in ("append",
                                        "buffer",
                                        "encrypt",
                                        "filename",
                                        "key",
                                        "maxsize",
                                        "maxparts",
                                        "rotate"
                                        )
                        or super()._is_valid_option(option_name))
        return is_valid

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        """
        Overridden. Fills a ConnectionsBuilder instance with the
        options currently used by this file protocol.
        :param builder: The ConnectionsBuilder object to fill with the current options
           of this protocol.
        """
        super()._build_options(builder)
        builder.add_option("append", self._append)
        builder.add_option("buffer", int(self._io_buffer / 1024))
        builder.add_option("filename", self._filename)
        builder.add_option("maxsize", int(self._max_size / 1024))
        builder.add_option("maxparts", self._max_parts)
        builder.add_option("rotate", self._rotate)

    def _load_options(self) -> None:
        """
        Overridden. Loads and inspects file specific options.
        This method loads all relevant options and ensures their correctness.
        See ._is_valid_option() for a list of options which are recognized by the file protocol.
        """

        super()._load_options()
        self._filename = self._get_string_option("filename", self._get_default_filename())
        self._append = self._get_boolean_option("append", False)
        self._io_buffer = int(self._get_size_option("buffer", 0))
        self._max_size = self._get_size_option("maxsize", 0)
        self._rotate = self._get_rotate_option("rotate", FileRotate.NO_ROTATE)

        if self._max_size > 0 and self._rotate == FileRotate.NO_ROTATE:
            # backwards compatibility
            self._max_parts = self._get_integer_option("maxparts", 2)
        else:
            self._max_parts = self._get_integer_option("maxparts", 0)

        self._key = self._get_bytes_option("key", self._KEY_SIZE, b"")
        self._encrypt = self._get_boolean_option("encrypt", False)

        if self._encrypt:
            self._append = False

        self._rotater.mode = self._rotate

    def _internal_connect(self) -> None:
        """
        Overridden. Opens the destination file.
        This method tries to open the destination file, which can be specified
        by passing the 'filename' option to the initialize method. For other valid
        options which might affect the behavior of this method, please see the
        is_valid_option method.
        """
        self._internal_do_connect(self._append)

    @staticmethod
    def _raise_exception(message: str) -> None:
        raise ProtocolError(message)

    def _internal_before_connect(self) -> None:
        if self._encrypt:
            if self._key == b"" or self._key is None:
                self._raise_exception("No encryption key")
            else:
                if len(self._key) != self._KEY_SIZE:
                    self._raise_exception("Invalid key size")

    def _internal_do_connect(self, append: bool) -> None:
        self._internal_before_connect()

        if self._is_rotating:
            filename = FileHelper.get_filename(self._filename, append)
        else:
            filename = self._filename

        if self._io_buffer > 0:
            logger.debug("IO buffer parameter is set by connection string.")
            buffer = self._io_buffer
            self._io_buffer_counter = 0
        else:
            logger.debug("IO buffer parameter is set by FileProtocol basic configuration.")
            buffer = self._BUFFER_SIZE
        logger.debug("BinaryIO buffering is set at parameter is set at: {} bytes".format(buffer))
        if append:
            self._stream = open(filename, "ab", buffering=buffer)
        else:
            self._stream = open(filename, "wb", buffering=buffer)

        self._file_size = os.path.getsize(filename)
        if self._encrypt:
            self._stream = self._get_cipher(self._stream)

        self._stream = self._get_stream(self._stream)
        self._file_size = self._write_header(self._stream, self._file_size)
        self._internal_after_connect(filename)

    def _internal_after_connect(self, filename: str) -> None:
        if not self._is_rotating:
            return

        if self._rotate != FileRotate.NO_ROTATE:
            file_date = FileHelper.get_file_date(self._filename, filename)
            self._rotater.initialize(file_date)
        if self._max_parts == 0:
            return

        FileHelper.delete_files(self._filename, self._max_parts)

    @property
    def _is_rotating(self):
        is_rotating = (self._rotate != FileRotate.NO_ROTATE or
                       self._max_size > 0)

        return is_rotating

    @staticmethod
    def _long_to_bytes(long_int: int) -> bytes:
        return struct.pack("q", long_int)

    def _get_i_vector(self) -> bytes:
        timestamp = int(time.time() * 1000)
        timestamp_bytes = self._long_to_bytes(timestamp)
        digest = hashes.Hash(hashes.MD5())
        digest.update(timestamp_bytes)
        return digest.finalize()

    def _get_cipher(self, stream: typing.BinaryIO) -> typing.BinaryIO:
        if not self._encrypt:
            return stream

        iv = self._get_i_vector()
        stream.write(self._SILE)
        stream.write(iv)
        stream.flush()

        cipher = SICipher(self._key, iv)
        ciphered_stream = CipheredIO(stream, cipher)
        return ciphered_stream

    def _write_header(self, stream: typing.BinaryIO, size: int) -> int:
        """Intended to write the header of a log file.
        This default implementation of this method writes the standard
        binary protocol header to the supplied stream instance.
        Derived classes may change this behavior by overriding this
        method.
        :param stream: The stream to which the header should be written to.
        :param size: Specifies the current size of the supplied stream.
        :return: The new size of the stream after writing the header. If no
            header is written, the supplied size argument is returned.
        """
        if size == 0:
            stream.write(self._SILF)
            stream.flush()
            return len(self._SILF)
        else:
            return size

    def _write_footer(self, stream: typing.BinaryIO) -> None:
        """
        Intended to write the footer of a log file.
        :param stream: The stream to which the footer should be written to.
        The implementation of this method does nothing. Derived class may change this
        behavior by overriding this method.
        """
        pass

    def _do_rotate(self) -> None:
        self._internal_disconnect()
        self._internal_do_connect(append=False)

    def _internal_write_packet(self, packet: Packet) -> None:
        """
        Overridden. Writes a packet to the destination file.
        If the "maxsize" option is set and the supplied packet would
        exceed the maximum size of the destination file, then the
        current log file is closed and a new file is opened.
        Additionally, if the "rotate" option is active, the log file
        is rotated if necessary. Please see the documentation of the
        is_valid_option method for more information.
        :param packet: The packet to write.
        """
        formatter = self._get_formatter()
        packet_size = formatter.compile(packet)

        if self._rotate != FileRotate.NO_ROTATE:
            if self._rotater.update(datetime.now(timezone.utc)):
                logger.debug("Rotating log file by time")
                self._do_rotate()

        if self._max_size > 0:
            self._file_size += packet_size
            if self._file_size > self._max_size:
                logger.debug("Rotating log file by size")
                self._do_rotate()

                if packet_size > self._max_size:
                    return

                self._file_size += packet_size

        formatter.write(self._stream)

        if self._io_buffer > 0:
            self._io_buffer_counter += packet_size
            logger.debug("Buffer counter size is {}".format(self._io_buffer_counter))
            if self._io_buffer_counter > self._io_buffer:
                self._io_buffer_counter = 0
                logger.debug("Reached IO buffer limit. Flushing stream.")
                self._stream.flush()
        else:
            self._stream.flush()

    def _internal_disconnect(self) -> None:
        """
        Overridden. Closes the destination file.
        """
        if self._stream is not None:
            try:
                self._write_footer(self._stream)
            finally:
                try:
                    self._stream.close()
                finally:
                    self._stream = None
