import threading

from common.color import Color
from common.level import Level
from common.viewer_id import ViewerId
from packets.log_entry import LogEntryType, LogEntry
from packets.process_flow import ProcessFlowType, ProcessFlow


class Session:
    __DEFAULT_COLOR = Color.TRANSPARENT

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
        self.__color = self.__DEFAULT_COLOR

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
        self.color = self.__DEFAULT_COLOR

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

    def __send_process_flow(self, level: Level, title: str, process_flow_type: ProcessFlowType) -> None:
        process_flow = ProcessFlow(process_flow_type)
        process_flow.timestamp = self.parent.now()
        process_flow.level = level
        process_flow.title = title
        self.parent.send_process_flow(process_flow)

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
                