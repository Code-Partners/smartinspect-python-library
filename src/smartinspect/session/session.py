import datetime
import fractions
import inspect
import io
import os
import platform
import threading
import traceback
from typing import Optional, Union

from smartinspect.common.color import Color, RGBAColor
from smartinspect.common.context import *
from smartinspect.common.level import Level
from smartinspect.common.locked_dictionary import LockedDictionary
from smartinspect.common.source_id import SourceId
from smartinspect.common.viewer_id import ViewerId
from smartinspect.packets import *


class Session:
    """
    Logs all kind of data and variables to the SmartInspect Console or to a log file.
    The Session class offers dozens of useful methods for sending any kind of data with the assistance of its parent.
    Sessions can send simple messages, warnings, errors and more complex things like pictures, objects, exceptions,
    system information and much more. They are even able to send variable watches, generate illustrated process and
    thread information or control the behavior of the SmartInspect Console. It is possible, for example, to clear the
    entire log in the Console by calling the clear_log() method.
    Please note that log methods of this class do nothing and return immediately if the session is currently inactive,
    its parent is disabled or the log level is not sufficient.
    This class is fully thread safe.
    """
    DEFAULT_COLOR = Color.TRANSPARENT

    def __init__(self, parent, name: str):
        """
        Initializes a new Session instance with the
        default color and the specified parent and name.
        :param parent: The parent of the new session.
        :param name: The name of the new session.
        """
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
        """
        Indicates if information can be logged or not.
        This method is used by the logging methods in this class to determine if information should be logged or not.
        When extending the Session class by adding new log methods to a derived class it is recommended
        to call this method first.
        :returns: True if information can be logged and False otherwise.
        """
        return self.is_active and self.parent.is_enabled

    @property
    def active(self) -> bool:
        """
        Specifies if the session is currently active.
        .. note::
            If this property is set to False, all logging methods of this class will return immediately and do nothing.
            Please note that the parent of this session also needs to be enabled in order to log information.
            This property is especially useful if you are using multiple sessions at once and want to deactivate
            a subset of these sessions. To deactivate all your sessions, you can use the enabled property
            of the parent.
        """
        return self.__active

    @active.setter
    def active(self, active: bool) -> None:
        """
        Specifies if the session is currently active.
        .. note::
            If this property is set to False, all logging methods of this class will return immediately and do nothing.
            Please note that the parent of this session also needs to be enabled in order to log information.
            This property is especially useful if you are using multiple sessions at once and want to deactivate
            a subset of these sessions. To deactivate all your sessions, you can use the enabled property
            of the parent.
        """
        if isinstance(active, bool):
            self.__active = active

    @property
    def is_active(self) -> bool:
        """
        Specifies if the session is currently active.
        .. note::
            If this property is set to False, all logging methods of this class will return immediately and do nothing.
            Please note that the parent of this session also needs to be enabled in order to log information.
            This property is especially useful if you are using multiple sessions at once and want to deactivate
            a subset of these sessions. To deactivate all your sessions, you can use the enabled property
            of the parent.
        """
        return self.active

    @property
    def parent(self):
        """
        Represents the parent of the session.
        The parent of a session is a SmartInspect instance. It is
        responsible for sending the packets to the SmartInspect Console
        or for writing them to a file. If the `SmartInspect.is_enabled
        property of the parent is False, all logging methods
        of this class will return immediately and do nothing.
        """
        return self.__parent

    def reset_color(self) -> None:
        """Resets the session color to its default value.
        .. note::
           The default color of a session is transparent.
        """
        self.color = self.DEFAULT_COLOR

    @property
    def color(self):
        """
        Returns the background color in the SmartInspect Console of this session.
        The session color helps you to identify Log Entries from different sessions
        in the SmartInspect Console by changing the background color.
        """
        return self.__color

    @color.setter
    def color(self, color: (Color, RGBAColor)) -> None:
        """
        Sets the background color in the SmartInspect Console of this session.
        The session color helps you to identify Log Entries from different sessions
        in the SmartInspect Console by changing the background color.
        """
        if isinstance(color, Color) or isinstance(color, RGBAColor):
            self.__color = color

    @property
    def _is_stored(self) -> bool:
        """
        Indicates if this session is stored in the session tracking
        list of its parent.
        .. note::
            See the SmartInspect.get_session() and SmartInspect.add_session()
            methods for more information about session tracking.
        :returns: True if this session is stored in the session tracking list
        and False otherwise.
        """
        return self.__stored

    @_is_stored.setter
    def _is_stored(self, stored: bool) -> None:
        """
        Sets if this session is stored in the session tracking
        list of its parent.
        .. note::
            See the SmartInspect.get_session() and SmartInspect.add_session()
            methods for more information about session tracking.
        """
        if isinstance(stored, bool):
            self.__stored = stored

    @property
    def name(self) -> str:
        """
        Represents the session name used for Log Entries.
        .. note::
            The session name helps you to identify Log Entries from
            different sessions in the SmartInspect Console. If you set
            this property to empty string, the session name will be empty when
            sending Log Entries.
        """
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        """
        Sets the session name used for Log Entries.
        .. note::
           The session name helps you to identify Log Entries from
           different sessions in the SmartInspect Console. If you set
           this property to empty string, the session name will be empty when
           sending Log Entries.
        """
        if not isinstance(name, str):
            name = ""

        if self.__stored:
            self.parent.update_session(self, name, self.__name)

        self.__name = name

    @property
    def level(self) -> Level:
        """
        Represents the log level of this Session object.
        Each Session object can have its own log level. A log message
        is only logged if its log level is greater than or equal to
        the log level of a session and the session parent. Log levels
        can thus be used to limit the logging output to important
        messages only.
        """
        return self.__level

    @level.setter
    def level(self, level: Level) -> None:
        """
        Sets the log level of this Session object.
        Each Session object can have its own log level. A log message
        is only logged if its log level is greater than or equal to
        the log level of a session and the session Parent. Log levels
        can thus be used to limit the logging output to important
        messages only.
        """
        if isinstance(level, Level):
            self.__level = level

    def is_on_level(self, level: (Level, None) = None) -> bool:
        """
        Indicates if information can be logged for a certain log level or not.
        This method is used by the logging methods in this class to determine if information should
        be logged or not. When extending the Session class by adding new log methods to a
        derived class it is recommended to call this method first.
        :param level: The log level to check for.
        :returns: True if information can be logged and False otherwise.
        """
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
        """
        Logs a simple separator using default level or custom log level (if provided via kwargs).
        This method instructs the Console to draw a separator. A separator is intended to group related Log Entries
        and to separate them visually from others. This method can help organising Log Entries in the Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        """
        level = self.__get_level(**kwargs)
        if self.is_on_level(level):
            self.__send_log_entry(level, None, LogEntryType.SEPARATOR, ViewerId.NO_VIEWER)

    def reset_call_stack(self, **kwargs) -> None:
        """
        Resets the call stack by using default level or custom log level (if provided via kwargs).
        This method instructs the Console to reset the call stack generated by the
        enter_method() and leave_method().
        It is especially useful if you want to reset the indentation in the method
        hierarchy without clearing all log entries.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        """
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            self.__send_log_entry(level, None, LogEntryType.RESET_CALLSTACK, ViewerId.NO_VIEWER)

    def enter_method(self, method_name: str = "", *args, **kwargs) -> None:
        """
        This method used to enter a method using default level or custom log level (if provided via kwargs).
        If a method name string is provided via method_name argument, the resulting method name consists
        of the method_name string formatted using optional args and kwargs.
        If the default value is used (empty string) for the method name, SmartInspect will try
        to get the calling method name out of the stack together with the module name and line of code where
        this method is located.
        The enter_method() method notifies the Console that a new method has been entered.
        The Console includes the method in the
        method hierarchy. If this method is used consequently, a full call stack
        is visible in the console which helps in locating bugs in the source code.
        Please see the leave_method() method as the counter piece to enter_method().

        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.

        :param method_name: The name (or format string) of the method.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string. If a level kwarg is provided it will be
                used to determine whether the Log Entry is to be shown in Console.
        """
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):

            try:
                if not isinstance(method_name, str):
                    raise TypeError('Method name must be a string')
                if method_name:
                    method_name = method_name.format(*args, **kwargs)

                    instance = kwargs.get("instance")
                    if instance is not None:
                        class_name = instance.__class__.__name__
                        method_name = f"{class_name}.{method_name}"
                else:
                    method_name = self._get_method_name()
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_log_entry(level, method_name, LogEntryType.ENTER_METHOD, ViewerId.TITLE)
            self.__send_process_flow(level, method_name, ProcessFlowType.ENTER_METHOD)

    # noinspection PyBroadException
    @staticmethod
    def _get_method_name() -> str:
        method_name = "<Unknown>"

        try:
            stack_frame = inspect.stack()[2]
            if stack_frame is None:
                return method_name

            # extract the parts of the stack frame.
            filepath, line, func_name = stack_frame[1:4]
            method_name = func_name.strip()
            module_name = os.path.basename(filepath)

            # add source position to method name.
            if module_name is not None:
                method_name += " ({0}, line {1})".format(module_name, line)

            return method_name

        except Exception:
            return method_name

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

    def leave_method(self, method_name: str = "", *args, **kwargs) -> None:
        """
        Leaves a method by using default level or custom log level (if provided via kwargs).
        If a method name string is provided via method_name argument, the resulting method name consists
        of the method_name string formatted using optional args and kwargs.
        If the default value is used (empty string) for the method name, SmartInspect will try
        to get the calling method name out of the stack together with the module name and line of code where
        this method is located.
        The leave_method() method notifies the Console that a method
        has been left. The Console closes the current method in the method hierarchy. If this method is used
        consequently, a full call stack is visible in the Console which helps locate bugs in the source code.
        Please see the enter_method() method as the counter piece to leave_method().
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.

        :param method_name: The name (or format string) of the method.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string. If a level kwarg is provided it will be
                used to determine whether the Log Entry is to be shown in Console.
        """
        level = self.__get_level(**kwargs)
        if self.is_on_level(level):

            try:
                if not isinstance(method_name, str):
                    raise TypeError('Method name must be a string')
                if method_name:
                    method_name = method_name.format(*args, **kwargs)
                    instance = kwargs.get("instance")
                    if instance is not None:
                        class_name = instance.__class__.__name__
                        method_name = f"{class_name}.{method_name}"
                else:
                    method_name = self._get_method_name()
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_log_entry(level, method_name, LogEntryType.LEAVE_METHOD, ViewerId.TITLE)
            self.__send_process_flow(level, method_name, ProcessFlowType.LEAVE_METHOD)

    def enter_thread(self, thread_name: str, *args, **kwargs) -> None:
        """
        Enters a new thread by using default level or custom log level (if provided via kwargs).
        The thread name consists of the thread_name string formatted using optional args and kwargs.
        The enter_thread method() notifies the Console that a new
        thread has been entered. The Console displays this thread in
        the Process Flow toolbox. If this method is used consequently,
        all threads of a process are displayed. Please see the
        leave_thread() method as the counter piece to enter_thread().
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param thread_name: The name (or format string) of the thread.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string. If a level kwarg is provided it will be
                used to determine whether the Log Entry is to be shown in Console.
        """
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
        """
        This method leaves a thread using default level or custom log level (if provided via kwargs).
        The thread name consists of the thread_name string formatted using optional args and kwargs.
        The leave_thread() method notifies the Console that a thread
        has been finished. The Console displays this change in the
        Process Flow toolbox. Please see the enter_thread() method as
        the counter piece to leave_thread().
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param thread_name: The name (or format string) of the thread.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string. If a level kwarg is provided it will be
                used to determine whether the Log Entry is to be shown in Console.
        """
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
        """
        Enters a process by using default level or custom log level (if provided via kwargs).
        The process name consists of a process_name string formatted using optional args and kwargs.
        The enter_process() method notifies the Console that a new
        process has been entered. The Console displays this process
        in the Process Flow toolbox. Please see the leave_process()
        method as the counter piece to enter_process().
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param process_name: The name (or format string) of the process.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string. If a level kwarg is provided it will be
                used to determine whether the Log Entry is to be shown in Console.
        """
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
        """
        Leaves a process using default level or custom log level (if provided via kwargs).
        The process name consists of a process_name string formatted using optional args and kwargs.
        TThe leave_process() method notifies the Console that a process has finished.
        The Console displays this change in the Process Flow toolbox.
        Please see the enter_process() method as the counter piece to leave_process().
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param process_name: The name (or format string) of the process.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string. If a level kwarg is provided it will be
                used to determine whether the Log Entry is to be shown in Console.
        """
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
        """
        Logs a colored message using default level or custom log level (if provided via kwargs).
        The message is created with a title string formatted using optional args and kwargs.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.

        :param color: The background color in the Console.
        :param title: A title (or format string) to create the message.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string. If a level kwarg is provided it will be
                used to determine whether the Log Entry is to be shown in Console.
        """
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
        """
         Logs a debug message with a log level of Level.DEBUG.
         The message is created with a title string formatted using optional args and kwargs.

        :param title: A title (or format sting) to create the message.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string.
        """
        if self.is_on_level(Level.DEBUG):
            try:
                if not isinstance(title, str):
                    raise TypeError('Title must be a string')
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.DEBUG, title, LogEntryType.DEBUG, ViewerId.TITLE)

    def log_verbose(self, title: str, *args, **kwargs) -> None:
        """
         Logs a debug message with a log level of Level.VERBOSE.
         The message is created with a title string formatted using optional args and kwargs.

        :param title: A title (or format sting) to create the message.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string.
        """
        if self.is_on_level(Level.VERBOSE):
            try:
                if not isinstance(title, str):
                    raise TypeError('Title must be a string')
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.VERBOSE, title, LogEntryType.VERBOSE, ViewerId.TITLE)

    def log_message(self, title: str, *args, **kwargs) -> None:
        """
         Logs a debug message with a log level of Level.MESSAGE.
         The message is created with a title string formatted using optional args and kwargs.

        :param title: A title (or format sting) to create the message.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string.
        """
        if self.is_on_level(Level.MESSAGE):
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string")
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.MESSAGE, title, LogEntryType.MESSAGE, ViewerId.TITLE)

    def log_warning(self, title: str, *args, **kwargs) -> None:
        """
         Logs a debug message with a log level of Level.WARNING.
         The message is created with a title string formatted using optional args and kwargs.

        :param title: A title (or format sting) to create the message.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string.
        """
        if self.is_on_level(Level.WARNING):
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string")
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.WARNING, title, LogEntryType.WARNING, ViewerId.TITLE)

    def log_error(self, title: str, *args, **kwargs) -> None:
        """
        Logs a debug message with a log level of Level.ERROR.
        The message is created with a title string formatted using optional args and kwargs.
        This method is ideally used in error handling code such as exception handlers.
        If this method is used consequently, it is easy to troubleshoot and solve bugs
        in applications or configurations. See log_exception() for a similar method.

        :param title: A title (or format sting) to create the message.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string.
        """
        if self.is_on_level(Level.ERROR):
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string ")
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.ERROR, title, LogEntryType.ERROR, ViewerId.TITLE)

    def log_fatal(self, title: str, *args, **kwargs) -> None:
        """
        Logs a debug message with a log level of Level.FATAL.
        The message is created with a title string formatted using optional args and kwargs.
        This method is ideally used in error handling code such as exception handlers.

        This method is ideally used in error handling code such as exception handlers.
        If this method is used consequently, it
        is easy to troubleshoot and solve bugs in applications or configurations.
        See log_error() for a method which does not
        describe fatal but recoverable errors.

        :param title: A title (or format sting) to create the message.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string.
        """
        if self.is_on_level(Level.FATAL):
            try:
                if not isinstance(title, str):
                    raise TypeError("Title must be a string or None")
                title = title.format(*args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.FATAL, title, LogEntryType.FATAL, ViewerId.TITLE)

    def __log_internal_error(self, title: str, *args, **kwargs):
        """
        Logs an internal error with a log level of Level.ERROR.
        The error message is created with a title string formatted using optional args and kwargs.
        This method logs an internal error. Such errors can occur if session methods are
        invoked with invalid arguments.
        For example, if you pass an invalid format string to log_message(), the exception
        will be caught and an internal error with the exception message will be sent.
        This method is also intended to be used in derived classes to report any errors in your own methods.

        :param title: A title (or format sting) to create the message.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string.
        """
        if self.is_on_level(Level.ERROR):
            try:
                if not isinstance(title, str):
                    raise TypeError('Title must be a string')
                title = title.format(args, **kwargs)
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(Level.ERROR, title, LogEntryType.INTERNAL_ERROR, ViewerId.TITLE)

    def add_checkpoint(self, name: str = "", details: str = "", **kwargs) -> None:
        """
        Increments the counter of a named checkpoint and
        logs a message with a custom log level and an optional
        message.
        This method increments the counter for the given checkpoint
        and then logs a message using "%checkpoint% #N" as title where
        %checkpoint% stands for the name of the checkpoint and N for
        the incremented counter value. The initial value of the counter
        for a given checkpoint is 0. Specify the details parameter to
        include an optional message in the resulting log entry. You
        can use the reset_checkpoint() method to reset the counter to 0 again.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the checkpoint to increment.
        :param details: An optional message to include in the resulting log entry. Can be empty string.
        """
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")

                if not isinstance(details, str):
                    raise TypeError("Name must be a string")

                with self.__checkpoint_lock:
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
                        self.__checkpoint_counter += 1
                        counter = self.__checkpoint_counter

                        title = f"Checkpoint #{counter}"
            except Exception as e:
                return self.__process_internal_error(e)

            self.__send_log_entry(level, title, LogEntryType.CHECKPOINT, ViewerId.TITLE)

    def reset_checkpoint(self, name: str = "") -> None:
        """
        Resets the counter of a named checkpoint.
        This method resets the counter of the given named checkpoint.
        Named checkpoints can be incremented and logged with the add_checkpoint() method.
        :param name: The name of the checkpoint to reset.
        """
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
        """
        Logs an assert message if a condition is False with a log level of Level.ERROR.
        The assert message is created with a title string formatted using optional args and kwargs.
        An assert message is logged if this method is called with a condition parameter of the value False.
        No Log Entry is generated if this method is called with a condition parameter of the value True.
        A typical usage of this method would be to test if a variable is None before you use it.
        To do this, you just need to insert a log_assert() call to the code section in question with
        "instance is not None" as first parameter. If the reference is None and thus the expression
        evaluates to False, a message is logged.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param condition: The condition to check.
        :param title: The title (or format string) to create the name of Log Entry.
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string. If a level kwarg is provided it will be
                used to determine whether the Log Entry is to be shown in Console.
        """
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

    def log_is_none(self, title: str, instance: object, **kwargs) -> None:
        """
        Logs whether a variable is None or not using default level or custom log level (if provided via kwargs).
        This method is useful to check source code for None references in places where you experienced or
        expect problems and want to log possible references to None.
        .. note::
            If the instance argument is None, then ": is None",
            otherwise ": is not None" will be appended to the title before
            the Log Entry is sent.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title of the variable.
        :param instance: The variable which should be checked for null.
        """
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
        """
        Logs a conditional message using default level or custom log level (if provided via kwargs).
        The message is created with a title string formatted using optional args and kwargs.
        This method only sends a message if the passed condition
        argument evaluates to True. If condition is False, this
        method has no effect and nothing is logged. This method is
        thus the counter piece to log_assert().
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.

        :param condition: The condition to evaluate.
        :param title: The title (or format string) to create the name of Log Entry..
        :param args: Args for the format string.
        :param kwargs: Kwargs for the format string. If a level kwarg is provided it will be
                used to determine whether the Log Entry is to be shown in Console.
        """
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

    def log_bool(self, name: str, value: bool, **kwargs) -> None:
        """
        Logs a bool value using default level or custom log level (if provided via kwargs).
        This method logs the name and value of a boolean variable.
        A title like "name = True" will be displayed in the Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The variable name.
        :param value: The variable value.
        """
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

    def log_str(self, name: str, value: str, **kwargs) -> None:
        """
        Logs a string value using default level or custom log level (if provided via kwargs).
        This method logs the name and value of a string variable.
        A title like "name = "string"" will be displayed in the
        Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The variable name.
        :param value: The variable value.
        """
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

    def log_bytes(self, name: str, value: bytes, include_hex: bool = False, **kwargs) -> None:
        """
        Logs a bytes value with an optional hexadecimal representation
        using default level or custom log level (if provided via kwargs).
        This method logs the name and value of a bytes variable.
        If you set the include_hex argument to True then the
        hexadecimal representation of the supplied variable value
        is included as well.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The variable name.
        :param value: The variable value.
        :param include_hex: Indicates if a hexadecimal representation should be included.
        """
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

    def log_bytearray(self, name: str, value: bytearray, include_hex: bool = False, **kwargs) -> None:
        """
        Logs a bytearray value with an optional hexadecimal
        representation using default level or custom log level (if provided via kwargs).
        This method logs the name and value of a bytearray variable.
        If you set the include_hex argument to True then the
        hexadecimal representation of the supplied variable value
        is included as well.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.

        :param name: The variable name.
        :param value: The variable value.
        :param include_hex: Indicates if a hexadecimal representation should be included.
        """
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

    def log_int(self, name: str, value: int, include_hex: bool = False, **kwargs) -> None:
        """
        Logs an integer value with an optional hexadecimal
        representation using default level or custom log level (if provided via kwargs).
        This method logs the name and value of an integer variable. If you set the include_hex argument to
        true then the hexadecimal representation of the supplied variable value
        is included as well.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.

        :param name: The variable name.
        :param value: The variable value.
        :param include_hex: Indicates if a hexadecimal representation should be included.
        """
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

    def log_float(self, name: str, value: float, **kwargs) -> None:
        """
        Logs a float value with a custom log level using default level or custom log level (if provided via kwargs).
        This method logs the name and value of a float variable.
        A title like "name = 3.1415" will be displayed in the Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.

        :param name: The variable name.
        :param value: The variable value.
        """
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
        """Logs an object value using default level or custom log level (if provided via kwargs).
        This method logs the name and value of an object. The title
        to display in the Console will consist of the name and the
        return value of the object string representation.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.

        :param name: The variable name.
        :param value: The variable value.
        """
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(name, str):
                    raise TypeError("Name must be a string")
                title = f"{name} = {str(value)}"
            except Exception as e:
                return self.__process_internal_error(e)
            self.__send_log_entry(level, title, LogEntryType.VARIABLE_VALUE, ViewerId.TITLE)

    def log_time(self, name: str, value: datetime.time, **kwargs) -> None:
        """
        A method to log a datetime.time value using default level or custom log level (if provided via kwargs).
        This method logs the name and value of a datetime.time variable.
        A title like "name = 16:47:49" will be displayed in the Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The variable name.
        :param value: The variable value.
        """
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

    def log_datetime(self, name: str, value: datetime.datetime, **kwargs) -> None:
        """
        A method to log a datetime.datetime value using default level or custom log level (if provided via kwargs).
        This method logs the name and value of a datetime.datetime variable.
        A title like "name = 26.11.2004 16:47:49" will be displayed in the Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The variable name.
        :param value: The variable value.
        """
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

    def log_list(self, name: str, value: list, **kwargs) -> None:
        """
        Logs the content of a list using default level or custom log level (if provided via kwargs).
        This method displays the list's string representation in a listview in the console. See log_iterable() for
        a more general method which can handle any kind of collection.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name to display in the console.
        :param value: The list to log.
        """
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

    def log_tuple(self, name: str, value: tuple, **kwargs) -> None:
        """
        Logs the content of a tuple using default level or custom log level (if provided via kwargs).
        This method displays the tuple's string representation in a listview in the console. See log_iterable() for
        a more general method which can handle any kind of collection.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name to display in the console.
        :param value: The tuple to log.
        """
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

    def log_set(self, name: str, value: set, **kwargs) -> None:
        """
        Logs the content of a set using default level or custom log level (if provided via kwargs).
        This method displays the set's string representation in a listview in the console. See log_iterable() for
        a more general method which can handle any kind of collection.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name to display in the console.
        :param value: The set to log.
        """
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
        """
        Logs the content of a dictionary using default level or custom log level (if provided via kwargs).
        This method displays the dictionary's string representation in a listview in the console. See log_iterable() for
        a more general method which can handle any kind of collection.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name to display in the console.
        :param value: The dictionary to log.
        """
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

    def log_complex(self, name: str, value: complex, **kwargs) -> None:
        """
        A method to log a complex value using default level or custom log level (if provided via kwargs).
        This method logs the name and value of a complex variable.
        A title like "name = value" will be displayed in the Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The variable name.
        :param value: The variable value.
        """
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

    def log_fraction(self, name: str, value: fractions.Fraction, **kwargs) -> None:
        """
        A method to log a fraction value using default level or custom log level (if provided via kwargs).
        This method logs the name and value of a fraction variable.
        A title like "name = value" will be displayed in the Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The variable name.
        :param value: The variable value.
        """
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

    def log(self, name: str, value, **kwargs) -> None:
        """
        This convenience method dispatches the logging to the specific method responsible for logging
        the provided object type. Logging is performed using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The variable name.
        :param value: The variable value.
        """
        level = self.__get_level(**kwargs)

        if isinstance(value, bool):
            return self.log_bool(name, value, level=level)
        if isinstance(value, int):
            return self.log_int(name, value, level=level)
        if isinstance(value, str):
            return self.log_str(name, value, level=level)
        if isinstance(value, bytes):
            return self.log_bytes(name, value, level=level)
        if isinstance(value, bytearray):
            return self.log_bytearray(name, value, level=level)
        if isinstance(value, float):
            return self.log_float(name, value, level=level)
        if isinstance(value, datetime.time):
            return self.log_time(name, value, level=level)
        if isinstance(value, datetime.datetime):
            return self.log_datetime(name, value, level=level)
        if isinstance(value, list):
            return self.log_list(name, value, level=level)
        if isinstance(value, object):
            return self.log_object_value(name, value, level=level)
        if isinstance(value, tuple):
            return self.log_tuple(name, value, level=level)
        if isinstance(value, set):
            return self.log_set(name, value, level=level)
        if isinstance(value, dict):
            return self.log_dict_value(name, value, level=level)
        if isinstance(value, complex):
            return self.log_complex(name, value, level=level)
        if isinstance(value, fractions.Fraction):
            return self.log_fraction(name, value, level=level)

    def log_custom_context(self, title: str, logentry_type: LogEntryType, context: ViewerContext, **kwargs) -> None:
        """
        Logs a custom viewer context using default level or custom log level (if provided via kwargs).
        This method can be used to extend the capabilities of the
        SmartInspect Python library. You can assemble a so-called viewer
        context and thus can send custom data to the SmartInspect
        Console. Furthermore, you can choose the viewer in which your
        data should be displayed. Every viewer in the Console has
        a corresponding viewer context class in this library.
        Have a look at the ViewerContext class and its derived classes
        to see a list of available viewer context classes.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param logentry_type: The custom Log Entry type.
        :param context: The viewer context which holds the actual data and the
                        appropriate viewer ID.
        """

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
        """
        Logs a text using a custom Log Entry type and viewer ID and
        using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param text: The text to log.
        :param log_entry_type: The custom Log Entry type.
        :param viewer_id: The custom viewer ID which specifies the way the Console handles the text content.
        """
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
        """
        Logs the content of a file using a custom Log Entry type, viewer ID and title and
        using default level or custom log level (if provided via kwargs).
        This method logs the content of the supplied file using a custom Log Entry type and viewer ID.
        The parameters control the way the content of the file is displayed in the Console.
        You can extend the functionality of the SmartInspect Python library with this method.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param filename: The file to log.
        :param log_entry_type: The custom Log Entry type.
        :param viewer_id: The custom viewer ID which specifies the way the Console handles the file content.
        :param title: The title to display in the Console.
        """
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
        """
        Logs the content of a stream with a custom Log Entry type and viewer ID and
        using default level or custom log level (if provided via kwargs).
        This method logs the content of the supplied stream using a custom Log Entry type and viewer ID.
        The parameters control the way the content of the stream is displayed in the Console.
        Thus, you can extend the functionality of the SmartInspect Python library with this method.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: the title to display in the Console
        :param stream: the stream to log
        :param log_entry_type: the custom Log Entry type
        :param viewer_id: the custom viewer ID which specifies the way the Console handles the stream content
        """
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

    def log_text(self, title: str, text: str, **kwargs) -> None:
        """
        Logs a text using default level or custom log level (if provided via kwargs)
        and displays it in a read-only text field.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param text: The text to log.
        """
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
        """
        Logs a text file and displays the content in a read-only text field using a custom title and
        using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param filename: The file to log.
        :param title: The title to display in the Console.
        """
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
        """
        Logs a stream using default level or custom log level (if provided via kwargs)
        and displays the content in a read-only text field.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param stream: The stream to log.
        """
        level = self.__get_level(**kwargs)

        try:
            if not isinstance(title, str):
                raise TypeError("title must be a string")
            self.log_custom_stream(title, stream, LogEntryType.TEXT, ViewerId.DATA, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_html(self, title: str, html: str, **kwargs) -> None:
        """
        Logs HTML code using default level or custom log level (if provided via kwargs) and
        displays it in a web browser.
        This method logs the supplied HTML source code. The source
        code is displayed as a website in the web viewer of the Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param html: The HTML source code to display.
        """
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("title must be a string")
            if not isinstance(html, str):
                raise TypeError("stream must be a BytesIO")

            self.log_custom_text(title, html, LogEntryType.WEB_CONTENT, ViewerId.WEB, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_html_file(self, filename: str, title: str = "", **kwargs) -> None:
        """
        Logs an HTML file and displays the content in a
        web browser using a custom title and using default level or custom log level (if provided via kwargs).
        This method logs the HTML source code of the supplied file. The
        source code is displayed as a website in the web viewer of the
        Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param filename: The HTML file to display.
        """
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(filename, str):
                raise TypeError("filename must be a string")
            if not isinstance(title, str):
                raise TypeError("title must be a string")

            self.log_custom_file(filename, LogEntryType.WEB_CONTENT, ViewerId.WEB, title=title, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_html_stream(self, title: str, stream: io.BytesIO, **kwargs) -> None:
        """
        Logs a stream using default level or custom log level (if provided via kwargs) and displays
        the content in a web browser.
        This method logs the HTML source code of the supplied stream.
        The source code is displayed as a website in the web viewer of
        the console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param stream: The stream to display.
        """
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("title must be a string")
            if not isinstance(stream, io.BytesIO):
                raise TypeError("stream must be a BytesIO")

            self.log_custom_stream(title, stream, LogEntryType.WEB_CONTENT, ViewerId.WEB, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_binary(self, title: str, value: (bytes, bytearray),
                   offset: int = 0, length: int = 0, **kwargs) -> None:
        """
        Logs a byte sequence (bytes or bytearray) array using default level or custom log level (if provided via kwargs)
        and displays it in a hex viewer.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param value: The byte sequence to display data from.
        :param offset: The byte offset of buffer at which to display data from.
        :param length: The amount of bytes to display.
        """
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
        """
        Logs a binary file and displays its content in a hex viewer using a custom title and
        using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param filename: The binary file to display in a hex viewer.
        :param title: The title to display in the Console.
        """
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
        """
        Logs a binary stream using default level or custom log level (if provided via kwargs)
        and displays its content in a hex viewer.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param stream: The binary stream to display in a hex viewer.
        """
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
        """
        Logs a bitmap file and displays it in the Console using a custom title and
        using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param filename: The bitmap file to display in the Console.
        :param title: The title to display in the Console.
        """
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
        """
        Logs a stream using a custom title and
        using default level or custom log level (if provided via kwargs) and
        interprets its content as a bitmap.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param stream: The stream to display as bitmap.
        """
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("Title must be a string")

            self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.BITMAP, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_jpeg_file(self, filename: str, title: str = "", **kwargs) -> None:
        """
        Logs a JPEG file and displays it in the Console using a custom title and
        using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param filename: The JPEG file to display in the Console.
        """
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
        """
        Overloaded. Logs a stream using default level or custom log level (if provided via kwargs) and
        interprets its content as JPEG image.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param stream: The stream to display as JPEG image.
        """
        level = self.__get_level(**kwargs)

        try:
            if not isinstance(title, str):
                raise TypeError("Title must be a string")

            self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.JPEG, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_ico_file(self, filename: str, title: str = "", **kwargs) -> None:
        """
        Logs a Windows icon file and displays it in the Console using a custom title and
        using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param filename: The Windows icon file to display in the Console.
        """
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
        """
        Overloaded.
        Logs a stream using default level or custom log level (if provided via kwargs) and
        interprets its content as Windows icon.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param stream: The stream to display as Windows icon.
        """
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("Title must be a string")

            self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.ICON, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_metafile_file(self, filename: str, title: str = "", **kwargs) -> None:
        """
        Logs a Windows Metafile file and displays it in
        the Console using a custom title and using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param filename: The Windows Metafile file to display in the Console.
        """
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
        """
        Logs a stream using a custom title and using default level or custom log level (if provided via kwargs) and
        interprets its content as Windows Metafile image.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param stream: The stream to display as Windows Metafile image.
        """
        level = self.__get_level(**kwargs)
        try:
            if not isinstance(title, str):
                raise TypeError("Title must be a string")
            self.log_custom_stream(title, stream, LogEntryType.GRAPHIC, ViewerId.METAFILE, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_sql(self, title: str, source: str, **kwargs) -> None:
        """
        Logs a string containing SQL source code using default level or custom log level (if provided via kwargs).
        This method displays the supplied SQL source code with syntax highlighting in the
        Console. It is especially useful to debug or track dynamically generated SQL source code.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param source: The SQL source code to log.
        """
        level = self.__get_level(**kwargs)
        try:
            self.log_source(title, source, SourceId.SQL, level=level)
        except Exception as e:
            return self.__process_internal_error(e)

    def log_source(self, title: str, source: str, source_id: SourceId, **kwargs) -> None:
        """
        Logs source code that is displayed with syntax highlighting in the Console
        using default level or custom log level (if provided via kwargs).
        This method displays the supplied source code with syntax highlighting in the Console.
        The type of the source code can be specified by the source_id argument.
        Please see the SourceId enum for information on the supported source code types.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param source: The source code to log.
        :param source_id: Specifies the type of source code.
        """
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
        """
        Logs the content of a file as source code with
        syntax highlighting using a custom title and using default level or custom log level (if provided via kwargs).
        This method displays the source file with syntax highlighting
        in the Console. The type of the source code can be specified by
        the source_id argument. Please see the SourceId enum for information
        on the supported source code types.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param filename: The name of the file which contains the source code.
        :param source_id: Specifies the type of source code.
        """
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(source_id, SourceId):
                    raise TypeError("source_id must be a SourceId")
            except Exception as e:
                return self.__process_internal_error(e)
            self.log_custom_file(filename, LogEntryType.SOURCE, source_id.viewer_id, title, level=level)

    def log_source_stream(self, title: str, stream, source_id: SourceId, **kwargs) -> None:
        """
        Logs the content of a stream as source code with
        syntax highlighting using default level or custom log level (if provided via kwargs).
        This method displays the content of a stream with syntax
        highlighting in the Console. The type of the source code can be
        specified by the source_id argument. Please see the SourceId enum for
        information on the supported source code types.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param stream: The stream which contains the source code.
        :param source_id: Specifies the type of source code.
        """
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            try:
                if not isinstance(source_id, SourceId):
                    raise TypeError("source_id must be a SourceId")
            except Exception as e:
                return self.__process_internal_error(e)
            self.log_custom_stream(title, stream, LogEntryType.SOURCE, source_id.viewer_id, level=level)

    def log_object(self, title: str, instance: object, include_non_public_fields: bool = False, **kwargs) -> None:
        """
        Logs fields and properties of an object using default level or custom log level (if provided via kwargs).
        Lets you specify if non-public fields should also be logged.
        This method logs all field names and their current values of
        an object. These key/value pairs will be displayed in the Console in an object
        inspector like viewer.
        You can specify if non-public or only public fields should be logged by setting
        the include_non_public_fields argument to True or False, respectively.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param instance: The object whose fields and properties should be logged.
        :param include_non_public_fields: Specifies if non-public fields should also be logged.
        """
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
        """
        Logs the content of an exception with a custom title and a log level of Level.ERROR.
        This method extracts the exception message and stack trace from the supplied exception and
        logs an error with this data.
        It is especially useful if you place calls to this method in exception handlers.
        See log_error() for a more general method with a similar intention.
        :param title: The title to display in the Console.
        :param exception: The exception to log.
        """
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
        """
        Logs information about the current thread with a custom title using default level or
        custom log level (if provided via kwargs).
        This method logs information about the current thread. This includes its name.
        log_current_thread() is especially useful in a multithreaded program like in a network server application.
        See log_thread() for a more general method which can handle any thread.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        """
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
        """
        Logs information about a thread with a custom title using default level or
        custom log level (if provided via kwargs).
        This method logs information about the supplied thread. This includes its name, its current state and more.
        log_thread() is especially useful in a multithreaded program like in a network server application.
        By using this method you can easily track all threads of a process and obtain detailed information about them.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param thread: The thread to log.
        """
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
        """
        Logs the content of an iterable using default level or
        custom log level (if provided via kwargs).
        This method iterates through the supplied iterable and renders every element into
        a string. These elements will be displayed in a listview in the Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param iterable: The iterable to log.
        """
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
        """
        Logs the content of a dictionary using default level or
        custom log level (if provided via kwargs).
        This method iterates through the supplied dictionary and
        renders every key/value pair into a string. These pairs will be displayed in a
        key/value viewer in the Console.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param dictionary: The dictionary to log.
        """
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
        """
        Logs the current stack trace with a custom title using default level or
        custom log level (if provided via kwargs).
        This method logs the current stack trace as returned by Python's traceback.format_stack()
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        """
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
        """
        Logs information about the system using a custom title and using default level or
        custom log level (if provided via kwargs).
        The logged information include the version of the operating system, the Python version and more.
        This method is useful for logging general information at the program startup.
        This guarantees that the support staff or developers have general information about the execution environment.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the console.
        """
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
        """
        Logs information about the metadata of a database cursor payload and using default level or
        custom log level (if provided via kwargs).
        The logged information is the metadata of table columns if such information is present in cursor description.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the console.
        :param cursor: Python DB API 2.0 compliant database cursor.
        """
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
        """
        Logs information about the rows, fetched by database cursor and using default level or
        custom log level (if provided via kwargs).
        The logged information is the table column names and rows as returned by cursor's fetchall().
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the console.
        :param cursor: Python DB API 2.0 compliant database cursor.
        """
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
        """
        This method performs an attempt to check for cursor compliance with
        Python DB API 2.0 by checking existence of mandatory methods and attributes
        according to PEP249 https://peps.python.org/pep-0249/ and returns False if any
        of them is missing.
        """

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
        """
        Logs a string using default level or custom log level (if provided via kwargs)
        and displays it in a read-only text field.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title to display in the Console.
        :param string: The string to log.
        """
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
        """
        Clears all Log Entries in the Console.
        """
        if self.is_on:
            self.__send_control_command(ControlCommandType.CLEAR_LOG, data=None)

    def clear_watches(self) -> None:
        """
        Clears all Watches in the Console.
        """
        if self.is_on:
            self.__send_control_command(ControlCommandType.CLEAR_AUTO_VIEWS, data=None)

    def clear_auto_views(self) -> None:
        """
        Clears all AutoViews in the Console.
        """
        if self.is_on:
            self.__send_control_command(ControlCommandType.CLEAR_AUTO_VIEWS, data=None)

    def clear_all(self) -> None:
        """
        Resets the whole console.
        This method resets the whole console. This means that all Watches, Log Entries, Process Flow entries and
        AutoViews will be deleted.
        """
        if self.is_on:
            self.__send_control_command(ControlCommandType.CLEAR_ALL, data=None)

    def clear_process_flow(self) -> None:
        """
        Clears all Process Flow entries in the Console.
        """
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
        """
        Increments a named counter by one and automatically
        sends its name and value as integer watch using default level or custom log level (if provided via kwargs).
        .. note::
           The Session class tracks a list of so called named counters.
           A counter has a name and a value of type integer. This method
           increments the value for the specified counter by one and then
           sends a normal integer watch with the name and value of the
           counter. The initial value of a counter is 0. To reset the
           value of a counter to 0 again, you can call reset_counter().
           See dec_counter() for a method which decrements the value of a
           named counter instead of incrementing it.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the counter to log.
        """
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
        """
        Decrements a named counter by one and automatically
        sends its name and value as an integer watch using default level or custom log level (if provided via kwargs).
        The Session class tracks a list of so called named counters.
        A counter has a name and a value of type integer. This method
        decrements the value for the specified counter by one and then
        sends a normal integer watch with the name and value of the
        counter. The initial value of a counter is 0. To reset the
        value of a counter to 0 again, you can call reset_counter().
        See inc_counter() for a method which increments the value of a
        named counter instead of decrementing it.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the counter to log.
        """
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
        """
        Resets a named counter to its initial value of 0.
        This method resets the integer value of a named counter to 0
        again. If the supplied counter is unknown, this method has no
        effect. Please refer to the inc_counter() and dec_counter() methods
        for more information about named counters.
        :param name: The name of the counter to reset.
        """
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
                              data: (bytes, bytearray) = b"", **kwargs) -> None:
        """
        Logs a custom log entry using default level or custom log level (if provided via kwargs).
        This method is useful for implementing custom Log Entry
        methods. For example, if you want to display some information
        in a particular way in the Console, you can just create a
        simple method which formats the data in question correctly and
        logs them using this send_custom_log_entry() method.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title of the new log entry.
        :param log_entry_type: The log entry type to use.
        :param viewer_id: The viewer id to use.
        :param data: Optional binary sequence to log (bytes or bytearray).

        :see also: :class:`Gurock.SmartInspect.LogEntry`
        """

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
                                    data: (bytes, bytearray) = b"", **kwargs) -> None:
        """
        Logs a custom Control Command using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param control_command_type: The Control Command type to use.
        :param data: Optional binary sequence to log (bytes or bytearray).
        """
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
        """
        Logs a custom Watch using default level or custom log level (if provided via kwargs).
        This method is useful for implementing custom Watch methods.
        For example, if you want to track the status of an instance of
        a specific class, you can just create a simple method which
        extracts all necessary information about this instance and logs
        them using this send_custom_watch() method.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the new Watch.
        :param value: The value of the new Watch.
        :param watch_type: The Watch type to use.
        """
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
        """
        Logs a custom Process Flow entry using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param title: The title of the new Process Flow entry.
        :param process_flow_type: The Process Flow type to use.
        """
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
        """
        Logs an object Watch using default level or custom log level (if provided via kwargs).
        This method serves as a convenience method and dispatches the value to watch to a specific method depending
        on the value type.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the Watch.
        :param value: The object value to display as Watch value.
        """
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
        """
        Logs a binary (bytes, bytearray) Watch with an optional hexadecimal
        representation using default level or custom log level (if provided via kwargs).
        You can specify if a
        hexadecimal representation should be included as well
        by setting the include_hex parameter to True.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the Watch.
        :param value: The value to display as Watch value.
        :param include_hex: Indicates if a hexadecimal representation should be included.
        """
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
        """
        Logs an integer Watch with an optional hexadecimal representation
        using default level or custom log level (if provided via kwargs).
        This method logs an integer Watch. You can specify if a hexadecimal representation should be
        included as well by setting the include_hex parameter to true.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the Watch.
        :param value: The value to display as Watch value.
        :param include_hex: Indicates if a hexadecimal representation should be included.
        """
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
        """
        Logs a float Watch using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the Watch.
        :param value: The value to display as Watch value.
        """
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
        """
        Logs a boolean Watch using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the Watch.
        :param value: The value to display as Watch value.
        """
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
        """
        Logs a datetime.time Watch using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the Watch.
        :param value: The value to display as Watch value.
        """
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

    def watch_datetime(self, name: str, value: datetime.datetime, **kwargs) -> None:
        """
        Logs a datetime.datetime Watch using default level or custom log level (if provided via kwargs).
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the Watch.
        :param value: The value to display as Watch value.
        """
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            if not isinstance(name, str):
                self.__log_internal_error("watch_datetime: name must be an str")
            if not isinstance(value, datetime.datetime):
                self.__log_internal_error("watch_datetime: value must be datetime.datetime")

            self.__send_watch(level, name, str(value), WatchType.TIMESTAMP)

    def watch_object(self, name: str, value: object, **kwargs) -> None:
        """
        Logs an object Watch using default level or custom log level (if provided via kwargs).
        The value of the resulting Watch is the string representation of the supplied object.
        .. note::
            If a custom Level is provided via kwargs (i.e. level=Level.MESSAGE) it will be used
            to determine whether the Log Entry is to be shown in Console.
            For more information, please refer to the documentation
            of the default_level property of the SmartInspect class.
        :param name: The name of the Watch.
        :param value: The value to display as Watch value.
        """
        level = self.__get_level(**kwargs)

        if self.is_on_level(level):
            if not isinstance(name, str):
                self.__log_internal_error("watch_object: name must be an str")
            try:
                self.__send_watch(level, name, str(value), WatchType.OBJECT)
            except Exception as e:
                exc_message = getattr(e, "message", repr(e))
                self.__log_internal_error(f"watch_object: {exc_message}")
