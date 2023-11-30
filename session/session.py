import datetime
import fractions
import io
import os
import platform
import threading
import traceback

from common.binary_context import BinaryContext
from common.binary_viewer_context import BinaryViewerContext
from common.color import Color
from common.data_viewer_context import DataViewerContext
from common.inspector_viewer_context import InspectorViewerContext
from common.level import Level
from common.list_viewer_context import ListViewerContext
from common.text_context import TextContext
from common.value_list_viewer_context import ValueListViewerContext
from common.viewer_context import ViewerContext
from common.viewer_id import ViewerId
from packets.control_command import ControlCommand
from packets.control_command_type import ControlCommandType
from packets.log_entry import LogEntryType, LogEntry
from packets.process_flow import ProcessFlowType, ProcessFlow
from packets.watch import Watch
from packets.watch_type import WatchType
from source_id import SourceId
from tableviewercontext import TableViewerContext


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

        self.__level: Level = Level.DEBUG
        self.__active: bool = True
        self.__counter: dict = dict()
        self.__checkpoints: dict = dict()
        self.__color = self.DEFAULT_COLOR

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
            self.parent._update_session(self, name, self.__name)

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

    def is_on(self, level: (Level, None) = None) -> bool:
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
        log_entry.set_timestamp(self.parent.now())
        log_entry.level = level

        if title is None:
            title = ""
        log_entry.set_title(title)

        if color is None:
            color = self.color

        # Here we skipped color variety management
        log_entry.set_color(color)
        log_entry.set_session_name(self.name)
        log_entry.set_data(data)
        self.parent.send_log_entry(log_entry)

    def log_separator(self, level: (Level, None) = None) -> None:
        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            self.__send_log_entry(level, None, LogEntryType.SEPARATOR, ViewerId.NO_VIEWER)

    def reset_call_stack(self, level: (Level, None) = None) -> None:
        if level is None:
            level = self.parent.default_level
            if self.is_on(level):
                self.__send_log_entry(level, None, LogEntryType.RESET_CALLSTACK, ViewerId.NO_VIEWER)

    # TODO check if we are working correctly winth None here
    def enter_method(self, method_name: str, *args, instance: (object, None) = None,
                     level: (Level, None) = None) -> None:
        if not isinstance(method_name, str):
            raise TypeError('Method name must be a string')

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if args:
                try:
                    method_name = method_name.format(args)
                except Exception as e:
                    self.__log_internal_error(f"enter_method {e.args[0]}")
            if instance:
                class_name = instance.__class__.__name__
                method_name = f"{class_name}.{method_name}"

            self.__send_log_entry(level, method_name, LogEntryType.ENTER_METHOD, ViewerId.TITLE)
            self.__send_process_flow(level, method_name, ProcessFlowType.ENTER_METHOD)

    # TODO check None theme
    def leave_method(self, method_name: str, *args, instance: (object, None) = None,
                     level: (Level, None) = None) -> None:
        if not isinstance(method_name, str):
            raise TypeError('Method name must be a string')

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if args:
                try:
                    method_name = method_name.format(args)
                except Exception as e:
                    self.__log_internal_error(f"leave_method {e.args[0]}")
            if instance:
                class_name = instance.__class__.__name__
                method_name = f"{class_name}.{method_name}"

            self.__send_log_entry(level, method_name, LogEntryType.LEAVE_METHOD, ViewerId.TITLE)
            self.__send_process_flow(level, method_name, ProcessFlowType.LEAVE_METHOD)

    def enter_thread(self, thread_name: str, *args, level: (Level, None) = None) -> None:
        if not isinstance(thread_name, str):
            raise TypeError('Thread name must be a string')

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if args:
                try:
                    thread_name = thread_name.format(args)
                except Exception as e:
                    self.__log_internal_error(f"enter_thread {e.args[0]}")

            self.__send_process_flow(level, thread_name, ProcessFlowType.ENTER_THREAD)

    def leave_thread(self, thread_name: str, *args, level: (Level, None) = None) -> None:
        if not isinstance(thread_name, str):
            raise TypeError('Thread name must be a string')

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if args:
                try:
                    thread_name = thread_name.format(args)
                except Exception as e:
                    self.__log_internal_error(f"leave_thread {e.args[0]}")

            self.__send_process_flow(level, thread_name, ProcessFlowType.LEAVE_THREAD)

    def enter_process(self, process_name: str, *args, level: (Level, None) = None) -> None:
        if not isinstance(process_name, str):
            raise TypeError('Process name must be a string')

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if process_name == "":
                process_name = self.parent.appname
            if args:
                try:
                    process_name = process_name.format(args)
                except Exception as e:
                    self.__log_internal_error(f"enter_process {e.args[0]}")

            self.__send_process_flow(level, process_name, ProcessFlowType.ENTER_PROCESS)
            self.__send_process_flow(level, "Main Thread", ProcessFlowType.ENTER_THREAD)

    def leave_process(self, process_name: str, *args, level: (Level, None) = None) -> None:
        if not isinstance(process_name, str):
            raise TypeError('Process name must be a string')

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if process_name == "":
                process_name = self.parent.appname
            if args:
                try:
                    process_name = process_name.format(args)
                except Exception as e:
                    self.__log_internal_error(f"leave_process {e.args[0]}")

            self.__send_process_flow(level, "Main Thread", ProcessFlowType.LEAVE_THREAD)
            self.__send_process_flow(level, process_name, ProcessFlowType.LEAVE_PROCESS)

    def log_colored(self, title: str, *args, color: Color, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError('Title must be a string')
        if not isinstance(color, Color):
            raise TypeError('color must be a Color')

        if self.is_on(level):
            if args:
                try:
                    title = title.format(args)
                except Exception as e:
                    self.__log_internal_error(f"log_colored {e.args[0]}")

            self.__send_log_entry(level, title, LogEntryType.MESSAGE, ViewerId.TITLE, color, None)

    def log_debug(self, title: str, *args) -> None:
        if not isinstance(title, str):
            raise TypeError('Title must be a string')

        if self.is_on(Level.DEBUG):
            if args:
                try:
                    title = title.format(args)
                except Exception as e:
                    self.__log_internal_error(f"log_debug {e.args[0]}")
            self.__send_log_entry(Level.DEBUG, title, LogEntryType.DEBUG, ViewerId.TITLE)

    def log_verbose(self, title: str, *args) -> None:
        if not isinstance(title, str):
            raise TypeError('Title must be a string')

        if self.is_on(Level.VERBOSE):
            if args:
                try:
                    title = title.format(args)
                except Exception as e:
                    self.__log_internal_error(f"log_verbose {e.args[0]}")
            self.__send_log_entry(Level.VERBOSE, title, LogEntryType.VERBOSE, ViewerId.TITLE)

    def log_message(self, title: (str, None), *args) -> None:
        if not isinstance(title, str) and not (title is None):
            raise TypeError("Title must be a string or None")

        if self.is_on(Level.MESSAGE):
            if args and isinstance(title, str):
                try:
                    title = title.format(args)
                except Exception as e:
                    self.__log_internal_error(f"log_message {e.args[0]}")
            self.__send_log_entry(Level.MESSAGE, title, LogEntryType.MESSAGE, ViewerId.TITLE)

    def log_warning(self, title: (str, None), *args) -> None:
        if not isinstance(title, str) and not (title is None):
            raise TypeError("Title must be a string or None")

        if self.is_on(Level.WARNING):
            if args and isinstance(title, str):
                try:
                    title = title.format(args)
                except Exception as e:
                    self.__log_internal_error(f"log_warning {e.args[0]}")
            self.__send_log_entry(Level.WARNING, title, LogEntryType.WARNING, ViewerId.TITLE)

    def log_error(self, title: (str, None), *args) -> None:
        if not isinstance(title, str) and not (title is None):
            raise TypeError("Title must be a string or None")

        if self.is_on(Level.ERROR):
            if args and isinstance(title, str):
                try:
                    title = title.format(args)
                except Exception as e:
                    self.__log_internal_error(f"log_error {e.args[0]}")
            self.__send_log_entry(Level.ERROR, title, LogEntryType.ERROR, ViewerId.TITLE)

    def log_fatal(self, title: (str, None), *args) -> None:
        if not isinstance(title, str) and not (title is None):
            raise TypeError("Title must be a string or None")

        if self.is_on(Level.FATAL):
            if args and isinstance(title, str):
                try:
                    title = title.format(args)
                except Exception as e:
                    self.__log_internal_error(f"log_fatal {e.args[0]}")
            self.__send_log_entry(Level.FATAL, title, LogEntryType.FATAL, ViewerId.TITLE)

    def __log_internal_error(self, title: str, *args):
        if not isinstance(title, str):
            raise TypeError('Title must be a string')

        if self.is_on(Level.ERROR):
            if args:
                try:
                    title = title.format(args)
                except Exception as e:
                    self.__log_internal_error(f"log_internal_error {e.args[0]}")
            self.__send_log_entry(Level.ERROR, title, LogEntryType.INTERNAL_ERROR, ViewerId.TITLE)

    def add_checkpoint(self, name: str = "", details: str = "", level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if not isinstance(details, str):
            raise TypeError("Name must be a string")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
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

            self.__send_log_entry(level, title, LogEntryType.CHECKPOINT, ViewerId.TITLE)

    def reset_checkpoint(self, name: str = "") -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if name:
            key = name.lower()
            with self.__checkpoint_lock:
                if key in self.__checkpoints:
                    del self.__checkpoints[key]

        else:
            self.__checkpoint_counter = 0

    def log_assert(self, condition: bool, title: str, *args):
        if not isinstance(condition, bool):
            raise TypeError("Condition must be a boolean")
        if not isinstance(title, str):
            raise TypeError("Title must be a string")

        if self.is_on(Level.ERROR):
            if args:
                try:
                    title = title.format(args)
                except Exception as e:
                    self.__log_internal_error(f"log_assert {e.args[0]}")
            if not condition:
                self.__send_log_entry(Level.ERROR, title, LogEntryType.ASSERT, ViewerId.TITLE)

    # this is to solve the log_assigned() task with checking for null
    def log_is_None(self, title: str, instance: object, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("Title must be a string")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if instance is None:
                self.log_message(title + "is None")
            else:
                self.log_message(title + "is not None")

    def log_conditional(self, condition: bool, title: str, *args, level: (Level, None) = None) -> None:
        if not isinstance(condition, bool):
            raise TypeError("Condition must be a boolean")
        if not isinstance(title, str):
            raise TypeError("Title must be a string")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if condition:
                if args:
                    try:
                        title = title.format(args)
                    except Exception as e:
                        self.__log_internal_error(f"log_conditional {e.args[0]}")

                self.__send_log_entry(level, title, LogEntryType.CONDITIONAL, ViewerId.TITLE)

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

    def log_bool_value(self, name: str, value: bool, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, bool):
            raise TypeError("Value must be a boolean")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = {['False', 'True'][value]}"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_str_value(self, name: str, value: str, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, str):
            raise TypeError("Value must be a string")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = \"{value}\""
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_byte_value(self, name: str, value: (bytes, bytearray),
                       include_hex: bool = False, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, bytes) and not isinstance(value, bytearray):
            raise TypeError("Value must be a bytes sequence - bytes or bytearray")
        if not isinstance(include_hex, bool):
            raise TypeError("include_hex must be a bool")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = '{value}'"
            if include_hex:
                title += f" (0x{self.__to_hex(value, 2)})"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_int_value(self, name: str, value: int, include_hex: bool = False, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, int):
            raise TypeError("Value must be an int")
        if not isinstance(include_hex, bool):
            raise TypeError("include_hex must be a bool")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = '{value}'"
            if include_hex:
                title += f" (0x{self.__to_hex(value, 16)})"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_float_value(self, name: str, value: float, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, float):
            raise TypeError("Value must be a float")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = '{value}'"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_object_value(self, name: str, value: object, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            try:
                title = f"{name} = {str(value)}"
                self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)
            except Exception as e:
                self.__log_internal_error(f"log_object: {e.args[0]}")

    def log_time_value(self, name: str, value: datetime.time, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, datetime.time):
            raise TypeError("Value must be a datetime.time object")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = {str(value)}"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_datetime_value(self, name: str, value: datetime.datetime, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, datetime.datetime):
            raise TypeError("Value must be a datetime.datetime object")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = {str(value)}"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_list_value(self, name: str, value: list, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, list):
            raise TypeError("Value must be a list")
        if level is None:
            level = self.parent.default_level
        if not isinstance(level, Level):
            raise TypeError("Level must be a Level")

        if self.is_on(level):
            title = f"{name} = {str(value)}"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_tuple_value(self, name: str, value: tuple, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, tuple):
            raise TypeError("Value must be a tuple")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = {str(value)}"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_set_value(self, name: str, value: set, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, set):
            raise TypeError("Value must be a set")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = {str(value)}"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_dict_value(self, name: str, value: dict, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, dict):
            raise TypeError("Value must be a dict")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = {str(value)}"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_complex_value(self, name: str, value: complex, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, complex):
            raise TypeError("Value must be a complex")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = {str(value)}"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_fraction_value(self, name: str, value: fractions.Fraction, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, fractions.Fraction):
            raise TypeError("Value must be a Fraction")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            title = f"{name} = {str(value)}"
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_value(self, name: str, value, level: (Level, None) = None) -> None:
        if not isinstance(name, str):
            raise TypeError("Name must be a string")

        if level is None:
            level = self.parent.default_level

        if isinstance(value, bool):
            self.log_bool_value(name, value, level)
        if isinstance(value, str):
            self.log_str_value(name, value, level)
        if isinstance(value, bytes) or isinstance(value, bytearray):
            self.log_byte_value(name, value, level)
        if isinstance(value, int):
            self.log_int_value(name, value, level)
        if isinstance(value, float):
            self.log_float_value(name, value, level)
        if isinstance(value, datetime.time):
            self.log_time_value(name, value, level)
        if isinstance(value, datetime.datetime):
            self.log_datetime_value(name, value, level)
        if isinstance(value, list):
            self.log_list_value(name, value, level)
        if isinstance(value, object):
            self.log_object_value(name, value, level)
        if isinstance(value, datetime.time):
            self.log_time_value(name, value, level)
        if isinstance(value, datetime.datetime):
            self.log_datetime_value(name, value, level)
        if isinstance(value, list):
            self.log_list_value(name, value, level)
        if isinstance(value, tuple):
            self.log_tuple_value(name, value, level)
        if isinstance(value, set):
            self.log_set_value(name, value, level)
        if isinstance(value, dict):
            self.log_dict_value(name, value, level)
        if isinstance(value, complex):
            self.log_complex_value(name, value, level)
        if isinstance(value, fractions.Fraction):
            self.log_fraction_value(name, value, level)

    def log_custom_context(self, title: str, logentry_type: LogEntryType,
                           context: ViewerContext, level: (Level, None) = None) -> None:
        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if not isinstance(logentry_type, LogEntryType) or not isinstance(context, ViewerContext):
                self.__log_internal_error("log_custom_context: Invalid arguments")
            else:
                self.__send_context(level, title, logentry_type, context)

    def __send_context(self, level, title, logentry_type, context: ViewerContext):
        self.__send_log_entry(level, title, logentry_type, context.viewer_id, self.color, context.viewer_data)

    def __send_control_command(self, control_command_type: ControlCommandType, data: (bytes, bytearray)) -> None:
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

    def log_custom_text(self, title: str, text: str,
                        log_entry_type: LogEntryType, viewer_id: ViewerId,
                        level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("Title must be a string")
        if not isinstance(text, str):
            raise TypeError("Text must be a string")
        if not isinstance(log_entry_type, LogEntryType):
            raise TypeError("log_entry_type must be a LogEntryType")
        if not isinstance(viewer_id, ViewerId):
            raise TypeError("viewer_id must be a ViewerId")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            context = TextContext(viewer_id)
            try:
                try:
                    context.load_from_text(text)
                    self.__send_context(level, title, log_entry_type, context)
                except Exception as e:
                    self.__log_internal_error(f"log_custom_text {e.args[0]}")
            finally:
                context.close()

    def log_custom_file(self, filename: str,
                        log_entry_type: LogEntryType, viewer_id: ViewerId,
                        title: str = "", level: (Level, None) = None) -> None:
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

        if level is None:
            level = self.parent.default_level

        context = BinaryContext(viewer_id)
        try:
            try:
                context.load_from_file(filename)
                self.__send_context(level, title, log_entry_type, context)
            except Exception as e:
                self.__log_internal_error(f"log_custom_file {e.args[0]}")
        finally:
            context.close()

    def log_custom_stream(self, title: str, stream,
                          log_entry_type: LogEntryType, viewer_id: ViewerId,
                          level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("Title must be a string")
        if not isinstance(log_entry_type, LogEntryType):
            raise TypeError("log_entry_type must be a LogEntryType")
        if not isinstance(viewer_id, ViewerId):
            raise TypeError("viewer_id must be a ViewerId")

        if level is None:
            level = self.parent.default_level
        context = BinaryContext(viewer_id)
        try:
            try:
                context.load_from_stream(stream)
                self.__send_context(level, title, log_entry_type, context)
            except Exception as e:
                self.__log_internal_error(f"log_custom_context {e.args[0]}")
        finally:
            context.close()

    def log_custom_reader(self):
        # seems to be no sense for such a method in Python
        pass

    def log_text(self, title: str, text: str, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("Title must be a string")
        if not isinstance(text, str):
            raise TypeError("Text must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_text(title, text, LogEntryType.TEXT, ViewerId.DATA, level)

    def log_text_file(self, filename: str, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        if not isinstance(title, str):
            raise TypeError("Title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_file(filename, LogEntryType.TEXT, ViewerId.DATA, title=title, level=level)

    def log_text_stream(self, title: str, stream, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_stream(title, stream, LogEntryType.TEXT, ViewerId.DATA, level)

    def log_html(self, title: str, html: str, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if not isinstance(html, str):
            raise TypeError("stream must be a BytesIO")

        if level is None:
            level = self.parent.default_level

        self.log_custom_text(title, html, LogEntryType.WEBCONTENT, ViewerId.WEB, level)

    def log_html_file(self, filename: str, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        if not isinstance(title, str):
            raise TypeError("title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_file(filename, LogEntryType.WEBCONTENT, ViewerId.WEB, title=title, level=level)

    def log_html_stream(self, title: str, stream: io.BytesIO, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if not isinstance(stream, io.BytesIO):
            raise TypeError("stream must be a BytesIO")

        if level is None:
            level = self.parent.default_level

        self.log_custom_stream(title, stream, LogEntryType.WEBCONTENT, ViewerId.WEB, level=level)

    def log_binary(self, title: str, value: (bytes, bytearray),
                   offset: int = 0, length: int = 0, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("Name must be a string")
        if not isinstance(value, bytes) and not isinstance(value, bytearray):
            raise TypeError("Value must be a bytes sequence - bytes or bytearray")
        if not isinstance(offset, int):
            raise TypeError("offset must be an int")
        if not isinstance(length, int):
            raise TypeError("length must be an int")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            context = BinaryViewerContext()
            try:
                context.append_bytes(value, offset, length)
                self.__send_context(level, title, LogEntryType.BINARY, context)
            except Exception as e:
                self.__log_internal_error(f"log_custom_context {e.args[0]}")

    def log_binary_file(self, filename: str, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        if not isinstance(title, str):
            raise TypeError("title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_file(filename, LogEntryType.BINARY, ViewerId.BINARY, title=title, level=level)

    def log_binary_stream(self, title: str, stream: io.BytesIO, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if not isinstance(stream, io.BytesIO):
            raise TypeError("stream must be a BytesIO")

        if level is None:
            level = self.parent.default_level

        self.log_custom_stream(title, stream, LogEntryType.BINARY, ViewerId.BINARY, level=level)

    def log_bitmap_file(self, filename: str, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        if not isinstance(title, str):
            raise TypeError("title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_file(filename, LogEntryType.GRAPHIC, ViewerId.BITMAP, title, level)

    def log_bitmap_stream(self, title: str, stream, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("Title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.BITMAP, level)

    def log_jpeg_file(self, filename: str, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        if not isinstance(title, str):
            raise TypeError("title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_file(filename, LogEntryType.GRAPHIC, ViewerId.JPEG, title, level)

    def log_jpeg_stream(self, title: str, stream, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("Title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.JPEG, level)

    def log_icon_file(self, filename: str, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        if not isinstance(title, str):
            raise TypeError("title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_file(filename, LogEntryType.GRAPHIC, ViewerId.ICON, title, level)

    def log_icon_stream(self, title: str, stream, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("Title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.ICON, level)

    def log_metafile_file(self, filename: str, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        if not isinstance(title, str):
            raise TypeError("title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_file(filename, LogEntryType.GRAPHIC, ViewerId.METAFILE, title, level)

    def log_metafile_stream(self, title: str, stream, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("Title must be a string")

        if level is None:
            level = self.parent.default_level

        self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.METAFILE, level)

    def log_sql(self, title: str, source: str, level: (Level, None) = None) -> None:
        self.log_source(title, source, SourceId.SQL, level)

    def log_source(self, title: str, source: str, source_id: SourceId, level):
        if not isinstance(title, str):
            raise TypeError("Title must be a string")
        if not isinstance(source, str):
            raise TypeError("Source must be a string")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if not isinstance(source_id, SourceId):
                self.__log_internal_error("source_id must be a SourceId")
            else:
                self.log_custom_text(title, source, LogEntryType.SOURCE, source_id.viewer_id, level)

    def log_source_file(self, filename: str, source_id: SourceId, title: str = "", level: (Level, None) = None) -> None:
        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if not isinstance(source_id, SourceId):
                self.__log_internal_error("log_source_file: source_id must be a SourceId")
            else:
                self.log_custom_file(filename, LogEntryType.SOURCE, source_id.viewer_id, title, level)

    def log_source_stream(self, title: str, stream, source_id: SourceId, level: (Level, None) = None) -> None:
        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if not isinstance(source_id, SourceId):
                self.__log_internal_error("log_source_stream: source_id must be a SourceId")
            else:
                self.log_custom_stream(title, stream, LogEntryType.SOURCE, source_id.viewer_id, level)

    def log_object(self, title: str, instance: object, non_public: bool = False, level: (Level, None) = None) -> None:
        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            if instance is None:
                self.__log_internal_error("log_object: instance argument is None")
            else:
                cls = instance.__class__
                context = InspectorViewerContext()
                if non_public is True:
                    allowed_prefixes = ["_", "__"]
                    # TODO bases

    def log_exception(self, exception: BaseException, title: str = ""):
        if self.is_on(Level.ERROR):
            if not isinstance(exception, BaseException):
                self.__log_internal_error("log_exception: exception must be an Exception")
            if not isinstance(title, str):
                self.__log_internal_error("log_exception: title must be a string")

            if title == "":
                title = getattr(exception, "message", repr(exception))

            context = DataViewerContext()
            try:
                try:
                    file = io.StringIO()
                    try:
                        raise exception
                    except BaseException:
                        traceback.print_exc(file=file)

                    context.load_from_text(file.getvalue())
                    self.__send_context(Level.ERROR, title, LogEntryType.ERROR, context)
                    del file

                except Exception as e:
                    exc_message = getattr(e, "message", repr(e))
                    self.__log_internal_error(f"log_exception: {exc_message}")
            finally:
                context.close()

    def log_current_thread(self, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if level is None:
            level = self.parent.default_level
        if not isinstance(level, Level):
            raise TypeError("level must be a Level")

        if self.is_on(level):
            current_thread = threading.current_thread()
            if title == "":
                if current_thread.name:
                    title = f"Current thread: {current_thread.name}"
                else:
                    title = "Current thread"
            self.log_thread(title, current_thread, level)

    def log_thread(self, title: str, thread: threading.Thread, level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if not isinstance(level, Level):
            raise TypeError("level must be a Level")
        if not isinstance(thread, threading.Thread):
            self.__log_internal_error("log_thread: thread argument is not a threading.Thread")

        if level is None:
            level = self.parent.default_level

        if self.is_on(level):
            context = ValueListViewerContext()
            try:
                try:
                    context.append_key_value("Name", thread.name)
                    context.append_key_value("Ident", thread.ident)
                    context.append_key_value("Alive", thread.is_alive())
                    context.append_key_value("Daemon", thread.daemon)
                    self.__send_context(level, title, LogEntryType.TEXT, context)
                except Exception as e:
                    exc_message = getattr(e, "message", repr(e))
                    self.__log_internal_error(f"log_thread: {exc_message}")
            finally:
                context.close()

    def log_iterable(self, iterable, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if level is None:
            level = self.parent.default_level
        if not isinstance(level, Level):
            raise TypeError("level must be a Level")

        if self.is_on(level):
            context = ListViewerContext()

            try:
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
                exc_message = getattr(e, "message", repr(e))
                self.__log_internal_error(f"log_iterable: {exc_message}")

            finally:
                context.close()

    def log_dict(self, dictionary: dict, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if not isinstance(title, str):
            raise TypeError("dictionary must be a dict")
        if level is None:
            level = self.parent.default_level
        if not isinstance(level, Level):
            raise TypeError("level must be a Level")

        if self.is_on(level):
            context = ValueListViewerContext()

            try:
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
                exc_message = getattr(e, "message", repr(e))
                self.__log_internal_error(f"log_dictionary: {exc_message}")

            finally:
                context.close()

    @staticmethod
    def __build_stacktrace() -> ViewerContext:
        context = ListViewerContext()
        try:
            raise Exception("Current stacktrace")
        except Exception:
            stacktrace = traceback.format_stack()
            for frame in stacktrace[:-2]:
                context.append_line(frame.strip())
            return context

    def log_current_stacktrace(self, title: str = "", level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if not isinstance(title, str):
            raise TypeError("dictionary must be a dict")
        if level is None:
            level = self.parent.default_level
        if not isinstance(level, Level):
            raise TypeError("level must be a Level")

        if self.is_on(level):
            context = self.__build_stacktrace()
            if title == "":
                title = "Current stack trace"
            try:
                self.__send_context(level, title, LogEntryType.TEXT, context)
            finally:
                context.close()

    def log_system(self, title: str = "System information", level: (Level, None) = None) -> None:
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if level is None:
            level = self.parent.default_level
        if not isinstance(level, Level):
            raise TypeError("level must be a Level")

        if self.is_on(level):
            # context = ValueListViewerContext()
            context = InspectorViewerContext()
            try:
                try:
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
                    exc_message = getattr(e, "message", repr(e))
                    self.__log_internal_error(f"log_dictionary: {exc_message}")

            finally:
                context.close()

    def log_cursor_metadata(self, cursor, title: str = "", level: (Level, None) = None) -> None:
        if not self.__is_cursor(cursor):
            raise TypeError("cursor does not pass compliance check with Python DB API 2.0")
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if level is None:
            level = self.parent.default_level
        if not isinstance(level, Level):
            raise TypeError("level must be a Level")

        if self.is_on(level):
            if not cursor.description:
                self.__log_internal_error("log_cursor_data: cursor is empty")
                return

            context = TableViewerContext()
            try:
                try:
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
                    exc_message = getattr(e, "message", repr(e))
                    self.__log_internal_error(f"log_cursor_data: {exc_message}")
            finally:
                context.close()

    def log_cursor_data(self, cursor, title: str = "Table data", level: (Level, None) = None) -> None:
        if not self.__is_cursor(cursor):
            raise TypeError("cursor does not pass compliance check with Python DB API 2.0")
        if not isinstance(title, str):
            raise TypeError("title must be a string")
        if level is None:
            level = self.parent.default_level
        if not isinstance(level, Level):
            raise TypeError("level must be a Level")

        if self.is_on(level):
            if not cursor.description:
                self.__log_internal_error("log_cursor_data: cursor is empty")
                return
            context = TableViewerContext()
            try:
                try:
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
                    exc_message = getattr(e, "message", repr(e))
                    self.__log_internal_error(f"log_cursor_data: {exc_message}")
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
