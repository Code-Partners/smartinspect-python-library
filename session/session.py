import datetime
import fractions
import inspect
import io
import os
import platform
import threading
import traceback
from typing import Optional, Union

from common.context.binary_context import BinaryContext
from common.context.binary_viewer_context import BinaryViewerContext
from common.color.color import Color
from common.context.data_viewer_context import DataViewerContext
from common.context.inspector_viewer_context import InspectorViewerContext
from common.level import Level
from common.context.list_viewer_context import ListViewerContext
from common.locked_dictionary import LockedDictionary
from common.context.text_context import TextContext
from common.context.value_list_viewer_context import ValueListViewerContext
from common.context.viewer_context import ViewerContext
from common.viewer_id import ViewerId
from packets.control_command import ControlCommand
from packets.control_command_type import ControlCommandType
from packets.log_entry import LogEntryType, LogEntry
from packets.process_flow import ProcessFlowType, ProcessFlow
from packets.watch import Watch
from packets.watch_type import WatchType
from common.source_id import SourceId
from common.context.tableviewercontext import TableViewerContext


class Session:
    DEFAULT_COLOR = Color.TRANSPARENT

    def __init__(self, parent, name: str):
        self.__checkpoint_lock: threading.Lock = threading.Lock()

        self.__parent = parent
        self.__checkpoint_counter: int = 0

        if isinstance(name, str):
            self.__name = name
        else:
            self.__name = ""

        self.level: Level = Level.DEBUG
        self.active: bool = True
        self.__counter: LockedDictionary = LockedDictionary()
        self.__checkpoints: dict = dict()
        self.color = self.DEFAULT_COLOR

    @property
    def is_on(self) -> bool:
        return self.is_active and self.parent.is_enabled

    @property
    def active(self) -> bool:
        return self.__active

    @active.setter
    def active(self, active: bool) -> None:
        if isinstance(active, bool):
            self.__active = active

    @property
    def is_active(self) -> bool:
        return self.active

    @property
    def parent(self):
        return self.__parent

    def reset_color(self) -> None:
        self.color = self.DEFAULT_COLOR

    @property
    def color(self):
        return self.__color

    @color.setter
    def color(self, color: Color) -> None:
        if isinstance(color, Color):
            self.__color = color

    @property
    def _is_stored(self) -> bool:
        return self.__stored

    @_is_stored.setter
    def _is_stored(self, stored: bool) -> None:
        if isinstance(stored, bool):
            self.__stored = stored

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        if not isinstance(name, str):
            name = ""

        if self.__stored:
            self.parent.update_session(self, name, self.__name)

        self.__name = name

    @property
    def level(self) -> Level:
        return self.__level

    @level.setter
    def level(self, level: Level) -> None:
        """ Sets the log level of this Session instance.
        
        :param level: The level to set. If level does not belong to Level class, nothing is done.
        """
        if isinstance(level, Level):
            self.__level = level

    def is_on_level(self, level: (Level, None) = None) -> bool:
        if level is None:
            return self.active and self.parent.is_enabled
        if not isinstance(level, Level):
            return False

        is_on_level = (self.active and
                       self.parent.is_enabled and
                       level.value >= self.level.value and
                       level.value >= self.parent.level.value)

        return is_on_level

    def __send_log_entry(self,
                         level: Level,
                         title: (str, None),
                         log_entry_type: LogEntryType,
                         viewer_id: ViewerId,
                         color: (Color, None) = None,
                         data: (bytes, bytearray, None) = None):
        log_entry = LogEntry(log_entry_type, viewer_id)
        log_entry.timestamp = self.parent.now()
        log_entry.level = level

        if title is None:
            title = ""
        log_entry.title = title

        if color is None:
            color = self.color

        # Here we skipped color variety management
        log_entry.color = color
        log_entry.session_name = self.name
        log_entry.data = data
        self.parent.send_log_entry(log_entry)

    def log_separator(self, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            self.__send_log_entry(level, None, LogEntryType.SEPARATOR, ViewerId.NO_VIEWER)

    def reset_call_stack(self, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            self.__send_log_entry(level, None, LogEntryType.RESET_CALLSTACK, ViewerId.NO_VIEWER)

    def enter_method(self, method_name: str, *args, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):

            try:
                if not isinstance(method_name, str):
                    raise TypeError('Method name must be a string')
                method_name = method_name.format(*args, **kwargs)

                instance = kwargs.get("instance")
                if instance is not None:
                    class_name = instance.__class__.__name__
                    method_name = f"{class_name}.{method_name}"
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_log_entry(level, method_name, LogEntryType.ENTER_METHOD, ViewerId.TITLE)
            self.__send_process_flow(level, method_name, ProcessFlowType.ENTER_METHOD)

    def __process_internal_error(self, e: Exception) -> None:
        tb = e.__traceback__
        calling_method_name = traceback.extract_tb(tb)[-1].name

        exc_message = getattr(e, "message", repr(e))
        return self.__log_internal_error(f"{calling_method_name}: {exc_message}")

    def __get_level(self, **kwargs):
        level = kwargs.get("level")

        if level is None:
            return self.parent.default_level
        if not isinstance(level, Level):
            self.__log_internal_error("level must be a Level")

        return level

    def leave_method(self, method_name: str, *args, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        if self.is_on_level(level):

            try:
                if not isinstance(method_name, str):
                    raise TypeError('Method name must be a string')
                method_name = method_name.format(*args)
                instance = kwargs.get("instance")
                if instance is not None:
                    class_name = instance.__class__.__name__
                    method_name = f"{class_name}.{method_name}"
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_log_entry(level, method_name, LogEntryType.LEAVE_METHOD, ViewerId.TITLE)
            self.__send_process_flow(level, method_name, ProcessFlowType.LEAVE_METHOD)

    def enter_thread(self, thread_name: str, *args, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(thread_name, str):
                    raise TypeError('Thread name must be a string')

                thread_name = thread_name.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_process_flow(level, thread_name, ProcessFlowType.ENTER_THREAD)

    def leave_thread(self, thread_name: str, *args, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(thread_name, str):
                    raise TypeError('Thread name must be a string')
                thread_name = thread_name.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_process_flow(level, thread_name, ProcessFlowType.LEAVE_THREAD)

    def enter_process(self, process_name: str = "", *args, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(process_name, str):
                    raise TypeError('Process name must be a string')
                if process_name == "":
                    process_name = self.parent.appname
                process_name = process_name.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_process_flow(level, process_name, ProcessFlowType.ENTER_PROCESS)
            self.__send_process_flow(level, "Main Thread", ProcessFlowType.ENTER_THREAD)

    def leave_process(self, process_name: str = "", *args, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(process_name, str):
                    raise TypeError('Process name must be a string')
                if process_name == "":
                    process_name = self.parent.appname
                process_name = process_name.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_process_flow(level, "Main Thread", ProcessFlowType.LEAVE_THREAD)
            self.__send_process_flow(level, process_name, ProcessFlowType.LEAVE_PROCESS)

    def log_colored(self, color: Color, title: str, *args, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(title, str):
                    raise TypeError('Title must be a string')
                if not isinstance(color, Color):
                    raise TypeError('color must be a Color')
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_log_entry(level, title, LogEntryType.MESSAGE, ViewerId.TITLE, color, None)

    def log_debug(self, title: str, *args, **kwargs) -> None:
        if self.is_on_level(Level.DEBUG):
            try:
                if not isinstance(title, str):
                    raise TypeError('Title must be a string')
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.DEBUG, title, LogEntryType.DEBUG, ViewerId.TITLE)

    def log_verbose(self, title: str, *args, **kwargs) -> None:
        if self.is_on_level(Level.VERBOSE):
            try:
                if not isinstance(title, str):
                    raise TypeError('Title must be a string')
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.VERBOSE, title, LogEntryType.VERBOSE, ViewerId.TITLE)

    def log_message(self, title: str, *args, **kwargs) -> None:
        if self.is_on_level(Level.MESSAGE):
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string")
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.MESSAGE, title, LogEntryType.MESSAGE, ViewerId.TITLE)

    def log_warning(self, title: str, *args, **kwargs) -> None:
        if self.is_on_level(Level.WARNING):
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string")
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.WARNING, title, LogEntryType.WARNING, ViewerId.TITLE)

    def log_error(self, title: str, *args, **kwargs) -> None:
        if self.is_on_level(Level.ERROR):
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string ")
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.ERROR, title, LogEntryType.ERROR, ViewerId.TITLE)

    def log_fatal(self, title: str, *args, **kwargs) -> None:
        if self.is_on_level(Level.FATAL):
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string or None")
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.FATAL, title, LogEntryType.FATAL, ViewerId.TITLE)

    def __log_internal_error(self, title: str, *args, **kwargs):
        if self.is_on_level(Level.ERROR):
            try:
                if not isinstance(title, str):
                    raise TypeError('Title must be a string')
                title = title.format(args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.ERROR, title, LogEntryType.INTERNAL_ERROR, ViewerId.TITLE)

    def add_checkpoint(self, name: str = "", details: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")

                if not isinstance(details, str):
                    raise TypeError("Name must be a string")

                if name:
                    key = name.lower()
                    value = self.__checkpoints.get(key)
                    if value is None:
                        value = 0
                    value += 1
                    self.__checkpoints[key] = value

                    title = name + " #" + str(value)
                    if details:
                        title += "(" + details + ")"

                else:
                    with self.__checkpoint_lock:

                        self.__checkpoint_counter += 1
                        counter = self.__checkpoint_counter

                        title = f"Checkpoint #{counter}"
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_log_entry(level, title, LogEntryType.CHECKPOINT, ViewerId.TITLE)

    def reset_checkpoint(self, name: str = "") -> None:
        try:
            if not isinstance(name, str):
                raise TypeError("Name must be a string")

            if name:
                key = name.lower()
                with self.__checkpoint_lock:
                    if key in self.__checkpoints:
                        del self.__checkpoints[key]

            else:
                self.__checkpoint_counter = 0

        except Exception as e:
            return self.__process_internal_error(e)

    def log_assert(self, condition: bool, title: str, *args, **kwargs):
        if self.is_on_level(Level.ERROR):
            try:
                if not isinstance(condition, bool):
                    raise TypeError("Condition must be a boolean")
                if not isinstance(title, str):
                    raise TypeError("Title must be a string")
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            if not condition:
                self.__send_log_entry(Level.ERROR, title, LogEntryType.ASSERT, ViewerId.TITLE)

    def log_is_None(self, title: str, instance: object, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        if self.is_on_level(level):
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string")
            except Exception as e:
                return self.__process_internal_error(e)

            if instance is None:
                self.log_message(title + " is None")
            else:
                self.log_message(title + " is not None")

    def log_conditional(self, condition: bool, title: str, *args, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(condition, bool):
                    raise TypeError("Condition must be a boolean")
                if not isinstance(title, str):
                    raise TypeError("Title must be a string")
                if condition:
                    title = title.format(*args, **kwargs)
                    self.__send_log_entry(level, title, LogEntryType.CONDITIONAL, ViewerId.TITLE)
            except Exception as e:
                return self.__process_internal_error(e)

    @staticmethod
    def __to_hex(value: (int, bytes, bytearray), max_chars: int) -> str:
        # this method currently suports only ints and bytes/bytearrays
        # if we received an int we get hex value and cut off the '0x' prefix
        if isinstance(value, int):
            hex_value = hex(value)[2:]
        # if we received a bytes/bytearray sequence, we convert to hex representation
        elif isinstance(value, bytes) or isinstance(value, bytearray):
            hex_value = value.hex()
        else:
            raise TypeError("Unsupported value type")

        length = len(hex_value)

        # for strings longer then <maxchar> we return <maxchar> rightmost symbols
        if length >= max_chars:
            return hex_value[length - max_chars:]
        # for shorter strings we pad them out with zeros from the left side
        else:
            return hex_value.zfill(max_chars)

    def log_bool_value(self, name: str, value: bool, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, bool):
                    raise TypeError("Value must be a boolean")
                title = f"{name} = {['False', 'True'][value]}"
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_str_value(self, name: str, value: str, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, str):
                    raise TypeError("Value must be a string")
                title = f"{name} = \"{value}\""
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_bytes_value(self, name: str, value: bytes, include_hex: bool = False, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, bytes):
                    raise TypeError("Value must be a bytes sequence")
                if not isinstance(include_hex, bool):
                    raise TypeError("include_hex must be a bool")
                title = f"{name} = '{value}'"
                if include_hex:
                    title += f" (0x{self.__to_hex(value, 2)})"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_bytearray_value(self, name: str, value: bytearray, include_hex: bool = False, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, bytearray):
                    raise TypeError("Value must be a bytearray")
                if not isinstance(include_hex, bool):
                    raise TypeError("include_hex must be a bool")
                title = f"{name} = '{value}'"
                if include_hex:
                    title += f" (0x{self.__to_hex(value, 2)})"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_int_value(self, name: str, value: int, include_hex: bool = False, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if level is None:
            level = self.parent.default_level

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, int):
                    raise TypeError("Value must be an int")
                if not isinstance(include_hex, bool):
                    raise TypeError("include_hex must be a bool")
                title = f"{name} = '{value}'"
                if include_hex:
                    title += f" (0x{self.__to_hex(value, 16)})"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_float_value(self, name: str, value: float, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, float):
                    raise TypeError("Value must be a float")
                title = f"{name} = '{value}'"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_object_value(self, name: str, value: object, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                title = f"{name} = {str(value)}"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_time_value(self, name: str, value: datetime.time, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, datetime.time):
                    raise TypeError("Value must be a datetime.time object")
                title = f"{name} = {str(value)}"
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_datetime_value(self, name: str, value: datetime.datetime, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, datetime.datetime):
                    raise TypeError("Value must be a datetime.datetime object")
                title = f"{name} = {str(value)}"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_list_value(self, name: str, value: list, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, list):
                    raise TypeError("Value must be a list")
                title = f"{name} = {str(value)}"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_tuple_value(self, name: str, value: tuple, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, tuple):
                    raise TypeError("Value must be a tuple")
                title = f"{name} = {str(value)}"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_set_value(self, name: str, value: set, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, set):
                    raise TypeError("Value must be a set")
                title = f"{name} = {str(value)}"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_dict_value(self, name: str, value: dict, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, dict):
                    raise TypeError("Value must be a dict")
                title = f"{name} = {str(value)}"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_complex_value(self, name: str, value: complex, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, complex):
                    raise TypeError("Value must be a complex")

                title = f"{name} = {str(value)}"
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_fraction_value(self, name: str, value: fractions.Fraction, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, fractions.Fraction):
                    raise TypeError("Value must be a Fraction")
                title = f"{name} = {str(value)}"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_value(self, name: str, value, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if isinstance(value, bool):
            return self.log_bool_value(name, value, level=level)
        if isinstance(value, int):
            return self.log_int_value(name, value, level=level)
        if isinstance(value, str):
            return self.log_str_value(name, value, level=level)
        if isinstance(value, bytes):
            return self.log_bytes_value(name, value, level=level)
        if isinstance(value, bytearray):
            return self.log_bytearray_value(name, value, level=level)
        if isinstance(value, float):
            return self.log_float_value(name, value, level=level)
        if isinstance(value, datetime.time):
            return self.log_time_value(name, value, level=level)
        if isinstance(value, datetime.datetime):
            return self.log_datetime_value(name, value, level=level)
        if isinstance(value, list):
            return self.log_list_value(name, value, level=level)
        if isinstance(value, object):
            return self.log_object_value(name, value, level=level)
        if isinstance(value, tuple):
            return self.log_tuple_value(name, value, level=level)
        if isinstance(value, set):
            return self.log_set_value(name, value, level=level)
        if isinstance(value, dict):
            return self.log_dict_value(name, value, level=level)
        if isinstance(value, complex):
            return self.log_complex_value(name, value, level=level)
        if isinstance(value, fractions.Fraction):
            return self.log_fraction_value(name, value, level=level)

    def log_custom_context(self, title: str, logentry_type: LogEntryType, context: ViewerContext, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(logentry_type, LogEntryType) or not isinstance(context, ViewerContext):
                    raise TypeError("Invalid arguments")
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_context(level, title, logentry_type, context)

    def __send_context(self, level, title, logentry_type, context: ViewerContext):
        self.__send_log_entry(level, title, logentry_type, context.viewer_id, self.color, context.viewer_data)

    def __send_control_command(self, control_command_type: ControlCommandType,
                               data: Optional[Union[bytes, bytearray]]) -> None:
        control_command = ControlCommand(control_command_type)
        control_command.level = Level.CONTROL
        control_command.data = data
        self.parent.send_control_command(control_command)

    def __send_process_flow(self, level: Level, title: str, process_flow_type: ProcessFlowType) -> None:
        process_flow = ProcessFlow(process_flow_type)
        process_flow.timestamp = self.parent.now()
        process_flow.level = level
        process_flow.title = title
        self.parent.send_process_flow(process_flow)

    def __send_watch(self, level: Level, name: str, value: str, watch_type: WatchType) -> None:
        watch = Watch(watch_type)
        watch.timestamp = self.parent.now()
        watch.level = level
        watch.name = name
        watch.value = value
        self.parent.send_watch(watch)

    def log_custom_text(self, title: str, text: str, log_entry_type: LogEntryType,
                        viewer_id: ViewerId, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            context = TextContext(viewer_id)
            try:
                try:
                    if not isinstance(title, str):
                        raise TypeError("Title must be a string")
                    if not isinstance(text, str):
                        raise TypeError("Text must be a string")
                    if not isinstance(log_entry_type, LogEntryType):
                        raise TypeError("log_entry_type must be a LogEntryType")
                    if not isinstance(viewer_id, ViewerId):
                        raise TypeError("viewer_id must be a ViewerId")
                    context.load_from_text(text)
                    self.__send_context(level, title, log_entry_type, context)
                except Exception as e:
                    return self.__process_internal_error(e)
            finally:
                context.close()

    def log_custom_file(self, filename: str,
                        log_entry_type: LogEntryType, viewer_id: ViewerId,
                        title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)
        context = BinaryContext(viewer_id)
        try:
            try:
                if not isinstance(filename, str):
                    raise TypeError("Filename must be a string")
                if not isinstance(title, str):
                    raise TypeError("Title must be a string")
                if not isinstance(log_entry_type, LogEntryType):
                    raise TypeError("log_entry_type must be a LogEntryType")
                if not isinstance(viewer_id, ViewerId):
                    raise TypeError("viewer_id must be a ViewerId")

                if title == "":
                    title = filename
                context.load_from_file(filename)
                self.__send_context(level, title, log_entry_type, context)
            except Exception as e:
                return self.__process_internal_error(e)
        finally:
            context.close()

    def log_custom_stream(self, title: str, stream, log_entry_type: LogEntryType, viewer_id: ViewerId,
                          **kwargs) -> None:
        level = self.__get_level(**kwargs)
        context = BinaryContext(viewer_id)

        try:
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string")
                if not isinstance(log_entry_type, LogEntryType):
                    raise TypeError("log_entry_type must be a LogEntryType")
                if not isinstance(viewer_id, ViewerId):
                    raise TypeError("viewer_id must be a ViewerId")
                context.load_from_stream(stream)
                self.__send_context(level, title, log_entry_type, context)
            except Exception as e:
                return self.__process_internal_error(e)
        finally:
            context.close()

    def log_custom_reader(self):
        # seems to be no sense for such a method in Python
        pass

    def log_text(self, title: str, text: str, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("Title must be a string")
            if not isinstance(text, str):
                raise TypeError("Text must be a string")
            self.log_custom_text(title, text, LogEntryType.TEXT, ViewerId.DATA, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_text_file(self, filename: str, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(filename, str):
                raise TypeError("filename must be a string")
            if not isinstance(title, str):
                raise TypeError("Title must be a string")

            self.log_custom_file(filename, LogEntryType.TEXT, ViewerId.DATA, title=title, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_text_stream(self, title: str, stream, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        try:
            if not isinstance(title, str):
                raise TypeError("title must be a string")
            self.log_custom_stream(title, stream, LogEntryType.TEXT, ViewerId.DATA, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_html(self, title: str, html: str, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("title must be a string")
            if not isinstance(html, str):
                raise TypeError("stream must be a BytesIO")

            self.log_custom_text(title, html, LogEntryType.WEBCONTENT, ViewerId.WEB, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_html_file(self, filename: str, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(filename, str):
                raise TypeError("filename must be a string")
            if not isinstance(title, str):
                raise TypeError("title must be a string")

            self.log_custom_file(filename, LogEntryType.WEBCONTENT, ViewerId.WEB, title=title, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_html_stream(self, title: str, stream: io.BytesIO, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("title must be a string")
            if not isinstance(stream, io.BytesIO):
                raise TypeError("stream must be a BytesIO")

            self.log_custom_stream(title, stream, LogEntryType.WEBCONTENT, ViewerId.WEB, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_binary(self, title: str, value: (bytes, bytearray),
                   offset: int = 0, length: int = 0, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        context = BinaryViewerContext()

        if self.is_on_level(level):
            try:
                if not isinstance(title, str):
                    raise TypeError("Name must be a string")
                if not isinstance(value, bytes) and not isinstance(value, bytearray):
                    raise TypeError("Value must be a bytes sequence - bytes or bytearray")
                if not isinstance(offset, int):
                    raise TypeError("offset must be an int")
                if not isinstance(length, int):
                    raise TypeError("length must be an int")
                context.append_bytes(value, offset, length)
                self.__send_context(level, title, LogEntryType.BINARY, context)
            except Exception as e:
                return self.__process_internal_error(e)

    def log_binary_file(self, filename: str, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        try:
            if not isinstance(filename, str):
                raise TypeError("filename must be a string")
            if not isinstance(title, str):
                raise TypeError("title must be a string")

            self.log_custom_file(filename, LogEntryType.BINARY, ViewerId.BINARY, title=title, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_binary_stream(self, title: str, stream: io.BytesIO, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        try:
            if not isinstance(title, str):
                raise TypeError("title must be a string")
            if not isinstance(stream, io.BytesIO):
                raise TypeError("stream must be a BytesIO")

            self.log_custom_stream(title, stream, LogEntryType.BINARY, ViewerId.BINARY, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_bitmap_file(self, filename: str, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(filename, str):
                raise TypeError("filename must be a string")
            if not isinstance(title, str):
                raise TypeError("title must be a string")

            self.log_custom_file(filename, LogEntryType.GRAPHIC, ViewerId.BITMAP, title, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_bitmap_stream(self, title: str, stream, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("Title must be a string")

            self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.BITMAP, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_jpeg_file(self, filename: str, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        try:
            if not isinstance(filename, str):
                raise TypeError("filename must be a string")
            if not isinstance(title, str):
                raise TypeError("title must be a string")

            self.log_custom_file(filename, LogEntryType.GRAPHIC, ViewerId.JPEG, title, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_jpeg_stream(self, title: str, stream, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        try:
            if not isinstance(title, str):
                raise TypeError("Title must be a string")

            self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.JPEG, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_ico_file(self, filename: str, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(filename, str):
                raise TypeError("filename must be a string")
            if not isinstance(title, str):
                raise TypeError("title must be a string")
            if title == "":
                title = filename
            self.log_custom_file(filename, LogEntryType.GRAPHIC, ViewerId.ICON, title, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_icon_stream(self, title: str, stream, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("Title must be a string")

            self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.ICON, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_metafile_file(self, filename: str, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(filename, str):
                raise TypeError("filename must be a string")
            if not isinstance(title, str):
                raise TypeError("title must be a string")

            self.log_custom_file(filename, LogEntryType.GRAPHIC, ViewerId.METAFILE, title, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_metafile_stream(self, title: str, stream, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("Title must be a string")
            self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.METAFILE, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_sql(self, title: str, source: str, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            self.log_source(title, source, SourceId.SQL, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_source(self, title: str, source: str, source_id: SourceId, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string")
                if not isinstance(source, str):
                    raise TypeError("Source must be a string")
                if not isinstance(source_id, SourceId):
                    raise TypeError("source_id must be a SourceId")
            except Exception as e:
                return self.__process_internal_error(e)
            self.log_custom_text(title, source, LogEntryType.SOURCE, source_id.viewer_id, level=level)

    def log_source_file(self, filename: str, source_id: SourceId, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(source_id, SourceId):
                    raise TypeError("source_id must be a SourceId")
            except Exception as e:
                return self.__process_internal_error(e)
            self.log_custom_file(filename, LogEntryType.SOURCE, source_id.viewer_id, title, level=level)

    def log_source_stream(self, title: str, stream, source_id: SourceId, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(source_id, SourceId):
                    raise TypeError("source_id must be a SourceId")
            except Exception as e:
                return self.__process_internal_error(e)
            self.log_custom_stream(title, stream, LogEntryType.SOURCE, source_id.viewer_id, level=level)

    def log_object(self, title: str, instance: object, include_non_public_fields: bool = False, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        context = InspectorViewerContext()

        if self.is_on_level(level):
            try:
                if not isinstance(level, Level):
                    raise TypeError("level must be a Level")
                if not isinstance(include_non_public_fields, bool):
                    raise TypeError("non_public must be True or False")
                if instance is None:
                    raise TypeError("instance argument is None")

                # we get field names from the instance
                instance_fields = set(self.__get_fields(instance))

                # we then get fields from all the parent classes
                cls = instance.__class__
                class_fields = set()

                class_fields.update(self.__get_fields(cls))
                for class_ in inspect.getmro(cls):
                    if class_ != object:
                        class_fields.update(self.__get_fields(class_))

                # we do not include fields which are derived from parent classes
                fields = instance_fields.difference(class_fields)

                # if non_public is False then we need to exclude fields, starting with '_' (thus, with '__' as well)
                if include_non_public_fields is False:
                    fields = list(filter(lambda f: not f[0].startswith("_"), fields))

                result = []
                current_field = []

                for name in fields:
                    current_field.append(context.escape_item(name))
                    current_field.append("=")
                    current_field.append(str(getattr(instance, name)))
                    result.append("".join(current_field))
                    current_field = []

                result.sort()

                context.start_group("Fields")

                for item in result:
                    context.append_line(item)

                self.__send_context(level, title, LogEntryType.OBJECT, context)
            except Exception as e:
                return self.__process_internal_error(e)

    @staticmethod
    def __get_fields(cls):
        # here we create a dummy object to make a list of all general fields present in all objects
        boring = dir(type('dummy', (object,), {}))
        # here we make a list of fields without 'boring' fields and without methods
        all_fields = inspect.getmembers(cls)
        fields = [item[0] for item in all_fields
                  if not (item[0] in boring or inspect.isroutine(item[1]))]
        return fields

    def log_exception(self, exception: BaseException, title: str = ""):
        if self.is_on_level(Level.ERROR):
            context = DataViewerContext()
            try:
                try:
                    if not isinstance(exception, BaseException):
                        raise TypeError("exception must be an Exception")
                    if not isinstance(title, str):
                        raise TypeError("title must be a string")

                    if title == "":
                        title = getattr(exception, "message", repr(exception))

                    file = io.StringIO()
                    # noinspection PyBroadException
                    try:
                        raise exception
                    except Exception:
                        traceback.print_exc(file=file)

                    context.load_from_text(file.getvalue())
                    self.__send_context(Level.ERROR, title, LogEntryType.ERROR, context)
                    del file

                except Exception as e:
                    return self.__process_internal_error(e)
            finally:
                context.close()

    def log_current_thread(self, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(title, str):
                    raise TypeError("title must be a string")
                current_thread = threading.current_thread()
                if title == "":
                    if current_thread.name:
                        title = f"Current thread: {current_thread.name}"
                    else:
                        title = "Current thread"
                self.log_thread(title, current_thread, level=level)
            except Exception as e:
                return self.__process_internal_error(e)

    def log_thread(self, title: str, thread: threading.Thread, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            context = ValueListViewerContext()
            try:
                try:
                    if not isinstance(title, str):
                        raise TypeError("title must be a string")
                    if not isinstance(thread, threading.Thread):
                        raise TypeError("thread argument is not a threading.Thread")
                    context.append_key_value("Name", thread.name)
                    context.append_key_value("Ident", thread.ident)
                    context.append_key_value("Alive", thread.is_alive())
                    context.append_key_value("Daemon", thread.daemon)
                    self.__send_context(level, title, LogEntryType.TEXT, context)
                except Exception as e:
                    return self.__process_internal_error(e)
            finally:
                context.close()

    def log_iterable(self, iterable, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            context = ListViewerContext()
            try:

                if not isinstance(title, str):
                    raise TypeError("title must be a string")
                it = iter(iterable)
                while True:
                    try:
                        nxt = next(it)

                        if nxt == iterable:
                            context.append_line("<cycle>")
                        else:
                            context.append_line(str(nxt))

                    except StopIteration:
                        break
                if title == "":
                    title = "iterable"
                self.__send_context(level, title, LogEntryType.TEXT, context)
            except Exception as e:
                return self.__process_internal_error(e)

            finally:
                context.close()

    def log_dict(self, dictionary: dict, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            context = ValueListViewerContext()

            try:
                if not isinstance(title, str):
                    raise TypeError("title must be a string")
                if not isinstance(title, str):
                    raise TypeError("dictionary must be a dict")

                for elem in dictionary:
                    key = str(elem)

                    value = dictionary[elem]
                    if value == dictionary:
                        value = "<cycle>"
                    value = str(value)

                    context.append_key_value(key, value)
                if title == "":
                    title = "dictionary"
                self.__send_context(level, title, LogEntryType.TEXT, context)
            except Exception as e:
                return self.__process_internal_error(e)

            finally:
                context.close()

    @staticmethod
    def __build_stacktrace() -> ViewerContext:
        context = ListViewerContext()
        # noinspection PyBroadException
        try:
            raise Exception("Current stacktrace")
        except Exception:
            stacktrace = traceback.format_stack()
            for frame in stacktrace[:-2]:
                context.append_line(frame.strip())
            return context

    def log_current_stacktrace(self, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            context = self.__build_stacktrace()
            try:
                if not isinstance(title, str):
                    raise TypeError("title must be a string")
                if not isinstance(title, str):
                    raise TypeError("dictionary must be a dict")
                if title == "":
                    title = "Current stack trace"

                self.__send_context(level, title, LogEntryType.TEXT, context)
            except Exception as e:
                return self.__process_internal_error(e)
            finally:
                context.close()

    def log_system(self, title: str = "System information", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            context = InspectorViewerContext()
            try:
                try:
                    if not isinstance(title, str):
                        raise TypeError("title must be a string")
                    context.start_group('Operating System')
                    context.append_key_value('Name', platform.system())
                    context.append_key_value('Version', platform.version())

                    context.start_group('User')
                    context.append_key_value('Name', os.getlogin())
                    context.append_key_value('Home', os.path.expanduser('~'))
                    context.append_key_value('Current directory', os.getcwd())

                    context.start_group("Python")
                    context.append_key_value('Version', platform.python_version())
                    context.append_key_value('Compiler', platform.python_compiler())
                    context.append_key_value('Implementation', platform.python_implementation())

                    self.__send_context(level, title, LogEntryType.SYSTEM, context)
                except Exception as e:
                    return self.__process_internal_error(e)
            finally:
                context.close()

    def log_cursor_metadata(self, cursor, title: str = "", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            context = TableViewerContext()
            try:
                try:
                    if not self.__is_cursor(cursor):
                        raise TypeError("cursor does not pass compliance check with Python DB API 2.0")
                    if not isinstance(title, str):
                        raise TypeError("title must be a string")
                    if not cursor.description:
                        raise ValueError("cursor is empty")
                    description = cursor.description
                    context.begin_row()
                    for column in description:
                        name = column[0]
                        context.add_row_entry(name)
                    context.end_row()

                    context.begin_row()
                    for column in description:
                        data_type = column[1]
                        context.add_row_entry(data_type)
                    context.end_row()
                    self.__send_context(level, title, LogEntryType.DATABASE_STRUCTURE, context)
                except Exception as e:
                    return self.__process_internal_error(e)
            finally:
                context.close()

    def log_cursor_data(self, cursor, title: str = "Table data", **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            context = TableViewerContext()
            try:
                try:

                    if not self.__is_cursor(cursor):
                        raise TypeError("cursor does not pass compliance check with Python DB API 2.0")
                    if not isinstance(title, str):
                        raise TypeError("title must be a string")
                    if not cursor.description:
                        raise ValueError("cursor is empty")

                    description = cursor.description

                    context.begin_row()
                    for column in description:
                        name = column[0]
                        context.add_row_entry(name)
                    context.end_row()

                    rows = cursor.fetchall()

                    for row in rows:
                        context.begin_row()
                        for cell in row:
                            context.add_row_entry(cell)
                        context.end_row()
                    self.__send_context(level, title, LogEntryType.DATABASE_STRUCTURE, context)

                except Exception as e:
                    return self.__process_internal_error(e)
            finally:
                context.close()

    @staticmethod
    def __is_cursor(cursor) -> bool:
        """This method performs an attempt to check for cursor compliance with
        Python DB API 2.0 by checking existence of mandatory methods and attributes
        according to PEP249 https://peps.python.org/pep-0249/ and returns False if any
        of them is missing"""

        required_methods = ('execute', 'close', 'fetchone', 'fetchall', 'fetchmany',
                            'executemany', 'setinputsizes', 'setoutputsize',)
        required_attributes = ('description', 'rowcount', 'arraysize',)

        for method in required_methods:
            if not hasattr(cursor, method) or not callable(getattr(cursor, method)):
                return False

        for attribute in required_attributes:
            if not hasattr(cursor, attribute):
                return False

        return True

    def log_string(self, title: str, string: str, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("Title must be a string")
            if not isinstance(string, str):
                raise TypeError("Text must be a string")
            self.log_text(title, string, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def clear_log(self) -> None:
        if self.is_on:
            self.__send_control_command(ControlCommandType.CLEAR_LOG, data=None)

    def clear_watches(self) -> None:
        if self.is_on:
            self.__send_control_command(ControlCommandType.CLEAR_AUTO_VIEWS, data=None)

    def clear_auto_views(self) -> None:
        if self.is_on:
            self.__send_control_command(ControlCommandType.CLEAR_AUTO_VIEWS, data=None)

    def clear_all(self) -> None:
        if self.is_on:
            self.__send_control_command(ControlCommandType.CLEAR_ALL, data=None)

    def clear_process_flow(self) -> None:
        if self.is_on:
            self.__send_control_command(ControlCommandType.CLEAR_PROCESS_FLOW, data=None)

    def __update_counter(self, name: str, increment: bool) -> int:
        key = name.lower()

        with self.__counter as counter:
            value = int(counter.get(key, 0))
            if increment:
                value += 1
            else:
                value -= 1
            counter[key] = value

        return value

    def inc_counter(self, name: str, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("name must be an str")
                value = self.__update_counter(name, increment=True)
                self.__send_watch(level, name, str(value), WatchType.INT)
            except Exception as e:
                return self.__process_internal_error(e)

    def dec_counter(self, name: str, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("name must be an str")
                value = self.__update_counter(name, increment=False)
                self.__send_watch(level, name, str(value), WatchType.INT)
            except Exception as e:
                return self.__process_internal_error(e)

    def reset_counter(self, name: str) -> None:
        try:
            if not isinstance(name, str):
                if not isinstance(name, str):
                    raise TypeError("name must be an str")
            key = name.lower()
            with self.__counter as counter:
                del counter[key]
        except Exception as e:
            return self.__process_internal_error(e)

    def send_custom_log_entry(self, title: str, log_entry_type: LogEntryType, viewer_id: ViewerId,
                              data: (bytes, bytearray), **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(title, str):
                    raise TypeError("title must be a str")
                if not isinstance(log_entry_type, LogEntryType):
                    raise TypeError("log_entry_type must be a LogEntryType")
                if not isinstance(viewer_id, ViewerId):
                    raise TypeError("viewer_id must be a ViewerId")
                if not isinstance(data, bytes) and not isinstance(data, bytearray):
                    raise TypeError("data must be a bytes or bytearray")

                self.__send_log_entry(level, title, log_entry_type, viewer_id, self.color, data)
            except Exception as e:
                return self.__process_internal_error(e)

    def send_custom_control_command(self, control_command_type: ControlCommandType,
                                    data: (bytes, bytearray), **kwargs) -> None:
        level = self.__get_level(**kwargs)
        if self.is_on_level(level):
            try:
                if not isinstance(control_command_type, ControlCommandType):
                    raise TypeError(
                        "control_command_type must be a ControlCommandType")
                if not isinstance(data, bytes) and not isinstance(data, bytearray):
                    raise TypeError("data must be a bytes or bytearray")
                self.__send_control_command(control_command_type, data)
            except Exception as e:
                return self.__process_internal_error(e)

    def send_custom_watch(self, name: str, value: str, watch_type: WatchType, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("name must be an str")
                if not isinstance(value, str):
                    raise TypeError("value must be an str")
                if not isinstance(watch_type, WatchType):
                    raise TypeError("watch_type must be a WatchType")

                self.__send_watch(level, name, value, watch_type)
            except Exception as e:
                return self.__process_internal_error(e)

    def send_custom_process_flow(self, title: str, process_flow_type: ProcessFlowType, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        if self.is_on_level(level):
            try:
                if not isinstance(title, str):
                    raise TypeError("title must be an str")
                if not isinstance(process_flow_type, ProcessFlowType):
                    raise TypeError("process_flow_type must be a ProcessFlowType")
                self.__send_process_flow(level, title, process_flow_type)
            except Exception as e:
                return self.__process_internal_error(e)

    def watch(self, name: str, value, **kwargs) -> None:
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(name, str):
                raise TypeError("name must be a str")
            if isinstance(value, bool):
                return self.watch_bool(name, value, level=level)
            if isinstance(value, int):
                return self.watch_int(name, value, False, level=level)
            if isinstance(value, str):
                return self.watch_str(name, value, level=level)
            if isinstance(value, bytes) or isinstance(value, bytearray):
                return self.watch_byte(name, value, level=level)
            if isinstance(value, float):
                return self.watch_float(name, value, level=level)
            if isinstance(value, datetime.time):
                return self.watch_time(name, value, level=level)
            if isinstance(value, datetime.datetime):
                return self.watch_datetime(name, value, level=level)
            if isinstance(value, object):
                return self.watch_object(name, value, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def watch_str(self, name: str, value: str, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("name must be an str")
                if not isinstance(value, str):
                    raise TypeError("value must be an str")
                self.__send_watch(level, name, value, WatchType.STR)
            except Exception as e:
                return self.__process_internal_error(e)

    def watch_byte(self, name: str, value: (bytes, bytearray), include_hex: bool = False, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("name must be an str")
                if not isinstance(value, bytes) and not isinstance(value, bytearray):
                    raise TypeError("value must be bytes or bytearray")
                if not isinstance(include_hex, bool):
                    raise TypeError("include_hex must be True or False")

                output = str(value)
                if include_hex:
                    output += f" (0x{self.__to_hex(value, 2)})"
                self.__send_watch(level, name, output, WatchType.INT)
            except Exception as e:
                return self.__process_internal_error(e)

    def watch_int(self, name: str, value: int, include_hex: bool = False, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("name must be an str")
                if not isinstance(value, int):
                    raise TypeError("value must be int")
                if not isinstance(include_hex, bool):
                    raise TypeError("include_hex must be True or False")

                output = str(value)

                if include_hex:
                    output += f" (0x{self.__to_hex(value, 16)})"

                self.__send_watch(level, name, output, WatchType.INT)
            except Exception as e:
                return self.__process_internal_error(e)

    def watch_float(self, name: str, value: float, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("name must be an str")
                if not isinstance(value, float):
                    raise TypeError("value must be float")

                self.__send_watch(level, name, str(value), WatchType.FLOAT)
            except Exception as e:
                return self.__process_internal_error(e)

    def watch_bool(self, name: str, value: bool, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("name must be an str")
                if not isinstance(value, bool):
                    raise TypeError("value must be boolean")

                self.__send_watch(level, name, str(value), WatchType.BOOL)
            except Exception as e:
                return self.__process_internal_error(e)

    def watch_time(self, name: str, value: datetime.time, **kwargs) -> None:
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("name must be an str")
                if not isinstance(value, datetime.time):
                    raise TypeError("value must be datetime.time")

                self.__send_watch(level, name, str(value), WatchType.TIMESTAMP)
            except Exception as e:
                return self.__process_internal_error(e)

    def watch_datetime(self, name: str, value: datetime.datetime, level: Optional[Level] = None) -> None:
        if level is None:
            level = self.parent.default_level
        if not isinstance(level, Level):
            self.__log_internal_error("watch_datetime: level must be a Level")

        if self.is_on_level(level):
            if not isinstance(name, str):
                self.__log_internal_error("watch_datetime: name must be an str")
            if not isinstance(value, datetime.datetime):
                self.__log_internal_error("watch_datetime: value must be datetime.datetime")

            self.__send_watch(level, name, str(value), WatchType.TIMESTAMP)

    def watch_object(self, name: str, value: object, level: Optional[Level] = None) -> None:
        if level is None:
            level = self.parent.default_level
        if not isinstance(level, Level):
            self.__log_internal_error("watch_object: level must be a Level")

        if self.is_on_level(level):
            if not isinstance(name, str):
                self.__log_internal_error("watch_object: name must be an str")
            try:
                self.__send_watch(level, name, str(value), WatchType.OBJECT)
            except Exception as e:
                exc_message = getattr(e, "message", repr(e))
                self.__log_internal_error(f"watch_object: {exc_message}")
