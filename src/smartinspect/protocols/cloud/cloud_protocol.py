import collections
import importlib.util
import logging
import os
import re
import socket
import ssl
import threading
import time
import typing
import uuid
from datetime import datetime

from smartinspect.common.file_rotate import FileRotate
from smartinspect.common.file_rotater import FileRotater
from smartinspect.connections.connections_builder import ConnectionsBuilder
from smartinspect.packets.log_header import LogHeader
from smartinspect.packets.packet import Packet
from smartinspect.packets.packet_type import PacketType
from smartinspect.protocols.cloud.chunk import Chunk
from smartinspect.protocols.cloud.exceptions import *
from smartinspect.protocols.cloud.scheduled_executor import ScheduledExecutor
from smartinspect.protocols.tcp_protocol import TcpProtocol

logger = logging.getLogger(__name__)


class CloudProtocol(TcpProtocol):
    """
    Used for sending packets to the SmartInspect Cloud.
    This class is used for sending packets to the Cloud. Cloud protocol
    implementation is an extension of the TCP protocol.
    It is used when the 'cloud' protocol is specified in
    the SmartInspect connections string. Please
    see the is_valid_option() method for a list of available Protocol
    options.
    """
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
    _DEFAULT_TLS_CERTIFICATE_FILEPATH: str = "client.pem"

    _PREFACE_BYTES = bytes([0x29, 0x17, 0x73, 0x50])

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
        self._chunk_max_age: int = self._DEFAULT_CHUNK_MAX_AGE  # milliseconds
        self._virtual_file_max_size: int = self._DEFAULT_VIRTUAL_FILE_MAX_SIZE
        self._chunk: typing.Union[Chunk, None] = None
        self._chunking_lock = threading.Lock()
        self._rotater: typing.Union[FileRotater, None] = None
        self._rotate: typing.Union[FileRotate, None] = None
        self._tls_enabled: bool = False
        self._tls_certificate_location: str = ""
        self._tls_certificate_filepath: str = ""
        self._chunk_flush_executor: typing.Union[ScheduledExecutor, None] = None

    def is_reconnect_allowed(self) -> bool:
        return self._reconnect_allowed

    def _reset_chunk(self) -> None:
        logger.debug("Resetting chunk")
        self._chunk = Chunk(self._chunk_max_size)

    @staticmethod
    def _get_name() -> str:
        """
        Overridden. Returns 'cloud'.
        :return: 'cloud'
        """
        return "cloud"

    def _is_valid_option(self, option_name: str) -> bool:
        """
        Overrides parent method. Validates if a protocol option is supported.
        The following table lists all valid options, their default values
        and descriptions for the TCP protocol.

        ============== =============== =================================================================================
        Valid Options  Default Value   Description
        ============== =============== =================================================================================
        writekey       none            Write key of your SmartInspect Cloud license.
        customlabels   none            Up to 5 labels. See example below.
        region         eu-central-1    SiCloud region.
        maxsize        '1 MB'          Specifies the maximum size of a log file in kilobytes. When this size is reached,
                                       the current log file is closed and a new file is opened. It is possible to
                                       specify size units like this: "1 MB". Supported units are "KB", "MB" and "GB".
                                       Min value - "1 MB", max value - "50 MB".
        rotate         none            Specifies the rotate mode for log files. Please see below for a list of
                                       available values. A value of "none" disables this feature.
        ============== =============== =================================================================================

        For further options which affect the behavior of this protocol,
        please have a look at the documentation of
        Protocol.is_valid_option and TcpProtocol.is_valid_option methods of the parent classes.

        Example::

            SmartInspect.set_connections(
                CloudConnectionStringBuilder().add_cloud_protocol()
                    .set_region("eu-central-1")
                    .set_write_key("INSERT_YOUR_WRITE_KEY_HERE")
                    .add_custom_label("User", "Bob")
                    .add_custom_label("Version", "0.0.1")
                    .end_protocol().build()
                )

        :param option_name: The option name to validate.
        :return: True if the option is supported and False otherwise.
        """
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
                                         )
                         )
                    or super()._is_valid_option(option_name))
        return is_valid

    def _load_options(self) -> None:
        """
        Overridden. Loads and inspects Cloud specific options.

        This method loads all relevant options and ensures their
        correctness. See is_valid_option() for a list of options which
        are recognized by the Cloud protocol.
        """
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
        """
        Defines the default value for `reconnect` option as True.
        :return: True
        """
        return True

    @staticmethod
    def _get_async_enabled_default_value() -> bool:
        """
        Defines the default value for `async_enabled` option as True.
        :returns: True
        """
        return True

    @staticmethod
    def _get_async_queue_default_value() -> int:
        """
        Defines the default value for `async.queue` option as 20 megabytes.
        Double the size of the max packet size supported by the cloud. We want async queue to fit the largest packet,
        as have some spare space.
        :return: 20480
        """
        return 20 * 1024

    def _load_chunking_options(self) -> None:
        self._chunking_enabled = self._get_boolean_option("chunking.enabled", True)

        self._chunk_max_size = self._get_size_option("chunking.maxsize", int(self._DEFAULT_CHUNK_MAX_SIZE / 1024))
        self._chunk_max_size = max(self._chunk_max_size, self._MIN_ALLOWED_CHUNK_MAX_SIZE)
        self._chunk_max_size = min(self._chunk_max_size, self._MAX_ALLOWED_CHUNK_MAX_SIZE)

        self._chunk_max_age = self._get_integer_option("chunking.maxagems", self._DEFAULT_CHUNK_MAX_AGE)
        self._chunk_max_age = max(self._chunk_max_age, self._MIN_ALLOWED_CHUNK_MAX_AGE)

    def _load_virtual_file_rotation_options(self) -> None:
        self._virtual_file_max_size = self._get_size_option("maxsize",
                                                            int(self._DEFAULT_VIRTUAL_FILE_MAX_SIZE / 1024))
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

    def _build_options(self, builder: ConnectionsBuilder) -> None:
        """
        Overridden. Fills a ConnectionsBuilder instance with the
        options currently used by this Cloud protocol.
        :param builder: ConnectionsBuilder object to fill with the current options of this protocol.
        """
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

    def _compose_log_header_packet(self) -> LogHeader:
        """
        Overrides TCP header packet composition, adds cloud-specific fields,
        such as writekey, virtualfileid, customlabels.
        :return: LogHeader packet
        """
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
        """
        Overrides TCP protocol handshake by reversing the order,
        for compatibility with TLS.

        """
        self._send_client_banner()
        self._read_server_banner()

    def write_packet(self, packet: Packet) -> None:
        if not isinstance(packet, Packet):
            raise TypeError("packet must be a Packet")

        if not self._connected and not self._reconnect_allowed:
            logger.debug("Connection is closed and reconnect is forbidden, skip packet processing")
            return

        self._maybe_rotate_virtual_file_id(packet)

        if not self._chunking_enabled:
            if self._validate_packet_size(packet):
                super().write_packet(packet)
            else:
                logger.debug("Packet exceed the max size and is ignored")
        else:
            with self._chunking_lock:
                if self._chunk is None:
                    self._reset_chunk()

                if packet.packet_type == PacketType.LOG_HEADER:
                    logger.debug("Chunking is enabled, but log header packet must be sent separately")

                    super().write_packet(packet)
                else:
                    try:
                        self._chunk.compile_packet(packet)

                        if self._chunk.can_fit_formatted_packet():
                            logger.debug("Adding packet #%d to the chunk",
                                         self._packet_count)

                            self._chunk.chunk_formatted_packet()
                        else:
                            logger.debug("Bundle is full, packet #%d won't fit, compiling the chunk and writing it",
                                         self._packet_count)

                            if self._chunk.packet_count > 0:
                                super().write_packet(self._chunk)
                            else:
                                logger.debug("Do not flush chunk when packet does not fit, the chunk is empty")

                            self._reset_chunk()
                            self._chunk.compile_packet(packet)

                            if self._chunk.can_fit_formatted_packet():
                                logger.debug("Adding packet #%d to the chunk",
                                             self._packet_count)

                                self._chunk.chunk_formatted_packet()
                            else:
                                logger.debug("Packet #%d won't fit even in an empty chunk, writing it raw",
                                             self._packet_count)

                                if self._validate_packet_size(packet):
                                    super().write_packet(packet)
                                else:
                                    logger.debug("Packet exceeds the max size and is ignored")
                    except Exception as e:
                        logger.warning("Exception while handling chunk: %s - %s", type(e), str(e))

                        raise RuntimeError(e)

        if self._validate_packet_size(packet):
            self._virtual_file_size += packet.size

        self._packet_count += 1

    def _maybe_rotate_virtual_file_id(self, packet: Packet) -> None:
        packet_size = packet.size
        logger.debug("Check if packet of size %d can fit into virtual file, remaining space - %d",
                     packet_size, self._virtual_file_max_size - self._virtual_file_size - packet_size)

        if self._virtual_file_size + packet_size > self._virtual_file_max_size:
            logger.debug("Rotating virtual file by max size - %d",
                         self._virtual_file_max_size)

            self._do_rotate_virtual_file_id()
        elif self._rotate != FileRotate.NO_ROTATE:
            try:
                if self._rotater.update(datetime.now()):
                    logger.debug("Rotating virtual file by datetime")

                    self._do_rotate_virtual_file_id()
            except Exception as e:
                raise RuntimeError(e)

    def _do_rotate_virtual_file_id(self) -> None:
        if self._chunking_enabled and self._chunk is not None:
            with self._chunking_lock:
                if self._chunk.packet_count > 0:
                    logger.debug("Flushing chunk before rotating virtual file id")

                    try:
                        super().write_packet(self._chunk)
                    except Exception as e:
                        logger.debug("Exception caught {} - {}".format(type(e), str(e)))

                    self._reset_chunk()

        self._virtual_file_id = uuid.uuid4()
        self._virtual_file_size = 0

        log_header = self._compose_log_header_packet()
        super().write_packet(log_header)

    def connect(self) -> None:
        self._rotater.initialize(datetime.now())

        if self._chunking_enabled:
            self._chunk_flush_executor = ScheduledExecutor(lambda: self._flush_chunk_by_age(False), 100)
            self._chunk_flush_executor.start()
        super().connect()

    def disconnect(self) -> None:
        self._flush_chunk_by_age(True)

        if self._chunk_flush_executor is not None:
            try:
                self._chunk_flush_executor.stop(1000)
            except InterruptedError as e:
                raise RuntimeError(e)

        super().disconnect()

    def _internal_validate_write_packet_answer(self, server_answer: bytes) -> None:
        answer_length = len(server_answer)
        answer = server_answer.decode("UTF-8")

        logger.debug("Answer = {}; byte read count = {}".format(answer, answer_length))

        if answer_length == 2 and answer == "OK":
            pass
        elif answer.startswith("SmartInspectProtocolException"):
            try:
                self._handle_error_reply(answer)
            except CloudProtocolErrorWarning as e:
                logger.warning("SmartInspect cloud protocol warning - {}".format(str(e)))

            except CloudProtocolErrorReconnectAllowed as e:
                logger.warning("SmartInspect cloud protocol error allowing reconnects - {}".format(str(e)))

                super()._internal_validate_write_packet_answer(server_answer)
            except CloudProtocolErrorReconnectForbidden as e:
                logger.warning("SmartInspect cloud protocol error forbidding reconnects - {}".format(str(e)))

                self._reconnect_allowed = False
                super()._internal_validate_write_packet_answer(server_answer)

        else:
            super()._internal_validate_write_packet_answer(server_answer)

    def _internal_initialize_socket(self):
        if self._tls_enabled:
            location = self._tls_certificate_location

            cert_path = None

            # if location is marked as 'resource', then we search for the cert
            # in 'resources' package
            if location == "resource":
                pkg_path = importlib.util.find_spec("smartinspect.resources").origin
                # if there is a 'resources' package, we resolve its absolute path
                # and add filepath to it
                if pkg_path is not None:
                    resource_dir = os.path.dirname(pkg_path)
                    cert_path = os.path.join(resource_dir, self._tls_certificate_filepath)
            else:
                # otherwise we are looking for the cert by its path
                cert_path = self._tls_certificate_filepath

            # we check if a file is available by cert_path
            try:
                with open(cert_path):
                    ...
            except FileNotFoundError:
                cert_path = None
            except OSError:
                cert_path = None
            logger.debug("Certificate path is: {}".format(cert_path))

            if cert_path is None:
                logger.debug("SSL certificate resource loading failed")
                raise Exception("SSL certificate resource loading failed")

            timestamp = time.perf_counter()

            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.load_verify_locations(cert_path)
            context.verify_mode = ssl.CERT_REQUIRED

            socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            ssl_sock = context.wrap_socket(socket_)

            elapsed_ms = round((time.perf_counter() - timestamp) * 1000, 2)
            logger.debug("SSL Socket created in {} ms".format(elapsed_ms))

            try:
                ssl_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                ssl_sock.settimeout(self._timeout)
            except Exception:
                logger.debug("SSL socket creation failed")
                raise Exception("SSL socket creation failed")
            logger.debug("Returning SSL Socket {}".format(ssl_sock))
            ssl_sock.connect((self._hostname, self._port))

            return ssl_sock
        else:
            return super()._internal_initialize_socket()

    def _internal_write_packet(self, packet: Packet) -> None:
        self._get_stream().write(self._PREFACE_BYTES)
        super()._internal_write_packet(packet)

    def _internal_reconnect(self) -> bool:
        if self._reconnect_allowed:
            logger.debug("Trying to reconnect")
            return super()._internal_reconnect()
        else:
            logger.debug("Reconnect forbidden")

            return False

    @staticmethod
    def _handle_error_reply(error_msg: str) -> None:
        error_msg_parts = error_msg.split(" - ", 1)

        if len(error_msg_parts) != 2:
            logger.warning(error_msg_parts)
            raise TypeError("error_msg must split into 2 parts by ' - ' separator")

        exception_type = error_msg_parts[0]
        exception_msg = error_msg_parts[1]

        if exception_type.startswith("SmartInspectProtocolExceptionWarning"):
            raise CloudProtocolErrorWarning(exception_msg)
        elif exception_type.startswith("SmartInspectProtocolExceptionReconnectAllowed"):
            raise CloudProtocolErrorReconnectAllowed(exception_msg)
        elif exception_type.startswith("SmartInspectProtocolExceptionReconnectForbidden"):
            raise CloudProtocolErrorReconnectForbidden(exception_msg)
        else:
            raise TypeError("Unknown protocol exception type prefix")

    def _flush_chunk_by_age(self, force_flush: bool) -> None:
        with self._chunking_lock:
            if self._chunking_enabled and self._chunk is not None:
                time_to_flush = self._chunk.milliseconds_since_the_first_packet() > self._chunk_max_age
                if self._chunk.packet_count > 0:
                    if time_to_flush or force_flush:
                        if time_to_flush:
                            logger.debug("More than %dms passed since the chunk was started, time to flush it",
                                         self._chunk_max_age)
                        else:
                            logger.debug("Forced chunk flush")

                        # noinspection PyBroadException
                        try:
                            super().write_packet(self._chunk)
                        except Exception:
                            logger.debug("Exception caught")

                        self._reset_chunk()

    # noinspection PyUnusedLocal
    @staticmethod
    def _validate_packet_size(packet: Packet) -> bool:
        """
        Validate size of an individual packet. After partitioning was implemented, the upper limit of the packet size
        is no longer set as a hard limit in the clients, but in case it'll be done in the future, this method is left
        here undeleted.
        :param packet: Packet
        :return: True if packet size <= max allowed size
        """
        return True
