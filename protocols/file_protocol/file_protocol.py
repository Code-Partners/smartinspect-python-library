import logging
import os
import struct
import time
import typing
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes

from common.exceptions import ProtocolError
from common.file_helper import FileHelper
from common.file_rotate import FileRotate
from common.file_rotater import FileRotater
from connections.builders import ConnectionsBuilder
from formatters import BinaryFormatter
from packets.packet import Packet
from protocols.file_protocol.ciphered_io import CipheredIO
from protocols.file_protocol.si_cipher import SICipher
from protocols.protocol import Protocol

logger = logging.getLogger(__name__)


class FileProtocol(Protocol):
    _KEY_SIZE: int = 16
    _BUFFER_SIZE: int = 0x2000
    _SILE: bytes = b"SILE"
    _SILF: bytes = b"SILF"

    def __init__(self):
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

    def _get_name(self) -> str:
        return "file"

    def _get_formatter(self) -> BinaryFormatter:
        if self._formatter is None:
            self._formatter = BinaryFormatter()

        return self._formatter

    @staticmethod
    def _get_default_filename() -> str:
        return "log.sil"

    @staticmethod
    def _get_stream(stream: typing.BinaryIO) -> typing.BinaryIO:
        return stream

    def _is_valid_option(self, option_name: str) -> bool:
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
        super()._build_options(builder)
        builder.add_option("append", self._append)
        builder.add_option("buffer", int(self._io_buffer / 1024))
        builder.add_option("filename", self._filename)
        builder.add_option("maxsize", int(self._max_size / 1024))
        builder.add_option("maxparts", self._max_parts)
        builder.add_option("rotate", self._rotate)

    def _load_options(self) -> None:
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
        if size == 0:
            stream.write(self._SILF)
            stream.flush()
            return len(self._SILF)
        else:
            return size

    def _write_footer(self, stream: typing.BinaryIO) -> None:
        pass

    def _do_rotate(self) -> None:
        self._internal_disconnect()
        self._internal_do_connect(append=False)

    def _internal_write_packet(self, packet: Packet) -> None:
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
        if self._stream is not None:
            try:
                self._write_footer(self._stream)
            finally:
                try:
                    self._stream.close()
                finally:
                    self._stream = None
