class SmartInspectError(Exception):
    """
    Used internally to report any kind of error.

    This is the base class for several exceptions which are mainly
    used for internal error reporting. However, it can be useful
    to have a look at its derived classes, LoadConnectionsError
    and ProtocolError, which provide additional information
    about occurred errors besides the normal exception message.

    This can be useful if you need to obtain more information about
    a particular error in the SmartInspect ErrorEvent.

    This class is not guaranteed to be threadsafe.
    """

    def __init__(self, message):
        """
        Initializes a SmartInspectError exception
        instance with a custom error message.

        :param message: The error message which describes this exception.
        """
        super().__init__(message)

    @property
    def message(self):
        """
        The error message which describes this exception.
        :return: The error message which describes this exception.
        """
        return self.args[0]


class InvalidConnectionsError(Exception):
    """
    Used to report errors concerning the connections string in the
    SmartInspect class.

    .. note::
       An invalid syntax, unknown protocols or nonexistent options in the
       connections string will result in
       an InvalidConnectionsError exception. This exception type is
       used by the __create_connections() and __try_connections() methods
       of the SmartInspect class.

    .. note::
       This class is not guaranteed to be threadsafe.
    """

    def __init__(self, message):
        """
        Initializes a InvalidConnectionsError exception
        instance with a custom error message.
        :param message: The error message which describes this exception.
        """
        super().__init__(message)


class ProtocolError(Exception):
    """
    This class is used to report any errors concerning the protocol classes.

    This exception can be thrown by several Protocol methods
    like the Protocol.connect(), Protocol.disconnect() or
    Protocol.write_packet() methods when an error has occurred.

    See below for an example on how to obtain detailed information
    in the SmartInspect ErrorEvent about the protocol which caused
    the error.

    .. note::
        This class is not guaranteed to be threadsafe.

    .. note:: Please note: Keep in mind that adding SmartInspect log
           statements or other code to the event handlers which can lead
           to the error event can cause a presumably undesired recursive
           behavior.

    Example:
    --------
    A ProtocolException provides additional information
    about the occurred error besides the normal exception
    message, like, for example, the name of the protocol
    which caused this error

    class Listener(SmartInspectListener):
       def on_error(event: ErrorEvent):
           print(event.exception)
           if isinstance(event.exception, ProtocolError):
               pe = event.exception
               print(pe.get_protocol_name())
    """

    def __init__(self, message):
        """
        Initializes a ProtocolError instance.
        """
        super().__init__(message)
        self.__protocol_name: str = ""
        self.__protocol_options: str = ""

    def set_protocol_name(self, name: str) -> None:
        """
        Sets the name of the protocol which threw
        this exception. A possible value would be "tcp".
        """
        if not isinstance(name, str):
            raise TypeError("Protocol name must be a string")
        self.__protocol_name = name

    def get_protocol_name(self) -> str:
        """
        Represents the name of the protocol which threw this exception. A possible value would be "tcp".
        """
        return self.__protocol_name

    def set_protocol_options(self, options: str) -> None:
        """
        Sets the options of the protocol which threw
        this exception. Can be empty if not set.
        """
        if not isinstance(options, str):
            raise TypeError("Protocol options must be a string")
        self.__protocol_options = options

    def get_protocol_options(self) -> str:
        """
        Represents the options of the protocol which threw
        this exception. Can be empty if not set.
        """
        return self.__protocol_options


class LoadConnectionsError(SmartInspectError):
    """
    Used to report errors concerning the SmartInspect.load_connections() method.

    This exception is used to report errors concerning the
    SmartInspect.load_connections() method. This method is able to load
    connections string from a file. Therefore, errors can occur when trying to load a connections string
    from a nonexistent file or when the file can not be opened for reading, for example.

    If such an error occurs, an instance of this class will be passed to the SmartInspect ErrorEvent.
    Please note, that, if a connections string can be read correctly, but is found to be invalid
    then this exception type will not be used. The SmartInspect.load_connections() method will use
    the InvalidConnectionsError exception instead.

    .. note::
        This class is not guaranteed to be threadsafe.

    Example:
    --------
    A LoadConnectionsError provides additional information
    about the occurred error besides the normal exception
    message. It contains the name of the file which caused the
    exception while trying to read the connections string from
    it.

    class Listener(SmartInspectListener):
       def on_error(event: ErrorEvent):
           print(event.exception)
           if isinstance(event.exception, LoadConnectionsError):
               le = event.exception
               print(le.get_filename())


    SiAuto.si.add_lListener(Listener())  #Register our event handler for the error event.

    SiAuto.si.load_connections("nonexistent.sic")
    # Force an error event by passing a name of file
    which does not exist to the load_connections() method.
    """

    def __init__(self, filename: str, exception: str):
        """
        Initializes a LoadConnectionsError instance with a custom error message.
        Lets you specify the name of the file which caused this exception.

        :param filename: The name of the file which caused this exception.
        :param exception: The error message which describes the exception.
        """
        super().__init__(exception)
        self.__filename = filename

    def get_filename(self):
        """
        Returns the name of the file which caused this exception
        while trying to load the connections string from it.
        """
        return self.__filename

    def set_filename(self, filename: str):
        """
        Specifies the name of the file which caused this exception
        while trying to load the connections string from it.
        """
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        self.__filename = filename


class LoadConfigurationError(SmartInspectError):
    """
    Used to report errors concerning the SmartInspect.load_configuration() method.

    This exception is used to report errors concerning the
    SmartInspect.load_configuration() method. This method is able to load
    the SmartInspect properties from a file. Therefore, errors can occur
    when trying to load properties from a nonexistent file or when the
    file can not be opened for reading, for example.

    If such an error occurs, an instance of this class will be passed
    to the SmartInspect ErrorEvent. Please note that if a connections
    string can be read while loading the configuration file, but is
    found to be invalid then this exception type will not be used. In
    this case, the SmartInspect.load_configuration() method will use the
    InvalidConnectionsError exception instead.

    .. note::
        This class is not guaranteed to be thread-safe.

    Example:
    --------
    A LoadConnectionsError provides additional information
    about the occurred error besides the normal exception
    message. It contains the name of the file which caused the
    exception while trying to read the connections string from
    it.

    class Listener(SmartInspectListener):
       def on_error(event: ErrorEvent):
           print(event.exception)
           if isinstance(event.exception, LoadConfigurationError):
               le = event.exception
               print(le.get_filename())


    SiAuto.si.add_listener(Listener())  #Register our event handler for the error event.

    SiAuto.si.load_connections("nonexistent.sic")
    # Force an error event by passing a name of file
    which does not exist to the load_configuration() method.
    """

    def __init__(self, filename: str, exception: str):
        """
        Initializes a LoadConfigurationError
        instance with a custom error message. Allows you to specify the name
        of the file which caused this exception.

        :param filename: The name of the file which caused this exception.
        :param exception: The error message which describes the exception.
        """
        super().__init__(exception)
        self.__filename = filename

    def get_filename(self):
        """
        Returns the name of the file which caused this exception
        while trying to load the SmartInspect properties from it.
        """
        return self.__filename

    def set_filename(self, filename: str):
        """
        Specifies the name of the file which caused this exception
        while trying to load the SmartInspect properties from it.
        """
        if not isinstance(filename, str):
            raise TypeError("filename must be a string")
        self.__filename = filename
