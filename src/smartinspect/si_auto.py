import platform

from smartinspect.common.exceptions import InvalidConnectionsError
from smartinspect.session import Session
from smartinspect import SmartInspect


class SiAuto:
    """
    This class provides automatically created objects
    for using the SmartInspect and Session classes.

    This class provides a static property called si of type SmartInspect.
    Furthermore, a Session instance named main with si as parent is ready
    to use. The SiAuto class is especially useful if you do not want to
    create SmartInspect and Session instances by yourself.

    The connections string of si is
    set to "pipe(reconnect=True, reconnect.interval=1s)" for Windows
    or "tcp(host=localhost, port=4228,reconnect=True, reconnect.interval=1s)" for Linux and Darwin.
    Application name is set  to "Auto" and the
    session name of main to "Main".

    The public static members of this class are threadsafe.

    Usage example
    --------
        |  SiAuto.si.set_enabled(True)
        |  SiAuto.main.log_message("Welcome aboard!")
        |  SiAuto.main.enter_process("SiAutoExample")
        |  try:
        |       ...
        |  finally:
        |      SiAuto.main.leave_process("SiAutoExample")
        |      SiAuto.si.dispose()
    """

    _APP_NAME: str = "Auto"
    _WINDOWS_CONNECTION_STRING: str = "pipe(reconnect=True, reconnect.interval=1s)"
    _NON_WINDOWS_CONNECTION_STRING: str = "tcp(host=localhost, port=4228,reconnect=True, reconnect.interval=1s)"
    _SESSION_NAME: str = "Main"
    si: SmartInspect = SmartInspect(_APP_NAME)
    main: Session = si.add_session(_SESSION_NAME, True)

    try:
        if platform.system() == "Windows":
            si.set_connections(_WINDOWS_CONNECTION_STRING)
        else:
            si.set_connections(_NON_WINDOWS_CONNECTION_STRING)
    except InvalidConnectionsError:
        ...
