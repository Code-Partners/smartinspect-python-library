# import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
# from datetime import datetime
import re
import collections
import logging
import threading
import uuid

from common.file_rotate import FileRotate
from common.file_rotater import FileRotater
from connections.builders import ConnectionsBuilder
from packets.log_header import LogHeader
from packets.packet import Packet
# from packets.packet_type import PacketType
from protocols.cloud.chunk import Chunk
from protocols.tcp_protocol import TcpProtocol

logger = logging.getLogger(__name__)


class CloudProtocol(TcpProtocol):
    # Default Cloud region to connect to.
    _DEFAULT_REGION: str = "eu-central-1"

    # Max size of a packet that can be stored in the Cloud as a single DB record.
    # When exceeded, the packet is partitioned.
    # Chunks must be smaller than this limit.
    _MIN_ALLOWED_CHUNK_MAX_SIZE: int = 10 * 1024
    _MAX_ALLOWED_CHUNK_MAX_SIZE: int = 395 * 1024
    _DEFAULT_CHUNK_MAX_SIZE: int = 395 * 1024

    _MIN_ALLOWED_CHUNK_MAX_AGE: int = 500
    _DEFAULT_CHUNK_MAX_AGE: int = 1000

    # Size of a log file
    _MIN_ALLOWED_VIRTUAL_FILE_MAX_SIZE: int = 1 * 1024 * 1024
    _MAX_ALLOWED_VIRTUAL_FILE_MAX_SIZE: int = 50 * 1024 * 1024
    _DEFAULT_VIRTUAL_FILE_MAX_SIZE: int = 1 * 1024 * 1024

    _MAX_ALLOWED_CUSTOM_LABEL_COUNT: int = 5
    _MAX_ALLOWED_CUSTOM_LABEL_COMPONENT_LENGTH: int = 100

    _DEFAULT_TLS_CERTIFICATE_LOCATION: str = "resource"
    _DEFAULT_TLS_CERTIFICATE_FILEPATH: str = "client.trust"
    _DEFAULT_TLS_CERTIFICATE_PASSWORD: str = "xyh8PCNcLDVx4ZHm"

    def __init__(self) -> None:
        super().__init__()
        self._reconnect_allowed: bool = True
        self._write_key: str = ""
        self._virtual_file_id: uuid.UUID = uuid.uuid4()
        self._custom_labels: collections.OrderedDict = collections.OrderedDict()
        self._packet_count: int = 0
        self._virtual_file_size: int = 0
        self._chunking_enabled: bool = True
        self._chunk_max_size: int = self._DEFAULT_CHUNK_MAX_SIZE
        self._chunk_max_age: int = 1000  # milliseconds
        self._virtual_file_max_size: int = self._DEFAULT_VIRTUAL_FILE_MAX_SIZE
        self._chunk: Chunk | None = None
        self._chunking_lock = threading.Lock()
        self._rotater: FileRotater | None = None
        self._rotate: FileRotate | None = None
        self._tls_enabled: bool = False
        self._tls_certificate_location: str = ""
        self._tls_certificate_filepath: str = ""
        self._tls_certificate_password: str = ""
        self._chunk_flush_executor: ThreadPoolExecutor | None = None

    def is_reconnect_allowed(self) -> bool:
        return self._reconnect_allowed

    def _reset_chunk(self) -> None:
        logger.debug("Resetting chunk")
        self._chunk = Chunk(self._chunk_max_size)

    def _get_name(self) -> str:
        return "cloud"

    def _is_valid_option(self, option_name: str) -> bool:
        is_valid = (bool(option_name in ("writekey",
                                         "customlabels",
                                         "region",
                                         "chunking.enabled",
                                         "chunking.maxsize",
                                         "chunking.maxagems",
                                         "maxsize",
                                         "rotate",
                                         "tls.enabled",
                                         "tls.certificate.location",
                                         "tls.certificate.filepath",
                                         "tls.certificate.password"))
                    or super()._is_valid_option(option_name))
        return is_valid

    def _load_options(self) -> None:
        super()._load_options()
        self._write_key = self._get_string_option("writekey", "")

        region = self._get_string_option("region", self._DEFAULT_REGION)
        if self._get_string_option("host", "") == "":
            self._hostname = "packet-receiver.{region}.cloud.smartinspect.com".format(region=region)

        self._load_chunking_options()
        self._load_virtual_file_rotation_options()
        self._load_tls_options()

        custom_labels_option = self._get_string_option("customlabels", "")
        self._parse_custom_labels_option(custom_labels_option)

    @staticmethod
    def _get_reconnect_default_value() -> bool:
        return True

    @staticmethod
    def _get_async_enabled_default_value() -> bool:
        return True

    @staticmethod
    def _get_async_queue_default_value() -> int:
        return 20 * 1024

    def _load_chunking_options(self) -> None:
        self._chunking_enabled = self._get_boolean_option("chunking.enabled", True)

        self._chunk_max_size = self._get_size_option("chunking.maxsize", self._DEFAULT_CHUNK_MAX_SIZE)
        self._chunk_max_size = max(self._chunk_max_size, self._MIN_ALLOWED_CHUNK_MAX_SIZE)
        self._chunk_max_size = min(self._chunk_max_size, self._MAX_ALLOWED_CHUNK_MAX_SIZE)

        self._chunk_max_age = self._get_integer_option("chunking.maxagems", self._DEFAULT_CHUNK_MAX_AGE)
        self._chunk_max_age = max(self._chunk_max_age, self._MIN_ALLOWED_CHUNK_MAX_AGE)

    def _load_virtual_file_rotation_options(self) -> None:
        self._virtual_file_max_size = self._get_size_option("maxsize", self._DEFAULT_VIRTUAL_FILE_MAX_SIZE)
        self._virtual_file_max_size = max(self._virtual_file_max_size, self._MIN_ALLOWED_VIRTUAL_FILE_MAX_SIZE)
        self._virtual_file_max_size = min(self._virtual_file_max_size, self._MAX_ALLOWED_VIRTUAL_FILE_MAX_SIZE)

        self._rotate = self._get_rotate_option("rotate", FileRotate.NO_ROTATE)
        rotater = FileRotater()
        rotater.mode = self._rotate
        self._rotater = rotater

    def _load_tls_options(self) -> None:
        self._tls_enabled = self._get_boolean_option("tls.enabled", True)

        self._tls_certificate_location = self._get_string_option(
            "tls.certificate.location", self._DEFAULT_TLS_CERTIFICATE_LOCATION)

        self._tls_certificate_filepath = self._get_string_option(
            "tls.certificate.filepath", self._DEFAULT_TLS_CERTIFICATE_FILEPATH)

        self._tls_certificate_password = self._get_string_option(
            "tls.certificate.password", self._DEFAULT_TLS_CERTIFICATE_PASSWORD)

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        super()._build_options(builder)
        builder.add_option("writekey", self._write_key)
        builder.add_option("customlabels", self.compose_custom_labels_string(self._custom_labels))

        builder.add_option("chunking.enabled", self._chunking_enabled)
        builder.add_option("chunking.maxsize", int(self._chunk_max_size / 1024))
        builder.add_option("chunking.maxagems", self._chunk_max_age)

        builder.add_option("maxsize", int(self._virtual_file_max_size / 1024))
        builder.add_option("rotate", self._rotate)

        builder.add_option("tls.enabled", self._tls_enabled)
        builder.add_option("tls.certificate.location", self._tls_certificate_location)
        builder.add_option("tls.certificate.filepath", self._tls_certificate_filepath)
        builder.add_option("tls.certificate.password", self._tls_certificate_password)

    def _compose_log_header_packet(self) -> LogHeader:
        log_header = super()._compose_log_header_packet()
        log_header.add_value("writekey", self._write_key)
        log_header.add_value("virtualfileid", str(self._virtual_file_id))
        log_header.add_value("customlabels", self.compose_custom_labels_string(self._custom_labels))

        return log_header

    def _parse_custom_labels_option(self, option: str) -> None:
        try:
            getattr(self, "_custom_labels")
        except AttributeError:
            return

        for key_value_pair in re.split(r'\s*;\s*', option):
            pair = re.split(r'\s*=\s*', key_value_pair, 2)
            if len(pair) == 2:
                name, value = pair

                if (
                        len(name) <= self._MAX_ALLOWED_CUSTOM_LABEL_COMPONENT_LENGTH
                        and len(value) <= self._MAX_ALLOWED_CUSTOM_LABEL_COMPONENT_LENGTH
                ):
                    self._custom_labels[name] = value

            if len(self._custom_labels) == self._MAX_ALLOWED_CUSTOM_LABEL_COUNT:
                break

    @staticmethod
    def compose_custom_labels_string(custom_labels: collections.OrderedDict) -> str:
        result = []

        for key, value in custom_labels.items():
            if result:
                result.append(";")

            result.append(f"{key}={value}")

        return "".join(result)

    def _do_handshake(self) -> None:
        self._send_client_banner()
        self._read_server_banner()

    def write_packet(self, packet: Packet) -> None:
        if not isinstance(packet, Packet):
            raise TypeError("packet must be a Packet")

        if not self._connected and not self._reconnect_allowed:
            logger.debug("Connection is closed and reconnect is forbidden, skip packet processing")
            return

        # self._maybe_rotate_virtual_file_id(packet)

        if not self._chunking_enabled:
            if self._validate_packet_size(packet):
                super().write_packet(packet)
            else:
                logger.debug("Packet exceed the max size and is ignored")
        else:
            pass

        if self._validate_packet_size(packet):
            self._virtual_file_size += packet.size

        self._packet_count += 1

    def connect(self) -> None:
        super().connect()

    def disconnect(self) -> None:
        super().disconnect()

    # noinspection PyUnusedLocal
    @staticmethod
    def _validate_packet_size(packet: Packet) -> bool:
        """
         Validates size of an individual packet. After partitioning was implemented, the upper limit of the packet size
         is no longer set as a hard limit in the clients, but in case it'll be done in the future, this method
         is left here undeleted.

         :param packet: The packet to validate

         :return: `True` if packet size <= max allowed size
        """
        return True
