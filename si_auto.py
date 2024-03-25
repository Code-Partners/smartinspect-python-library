import platform

from common.exceptions import InvalidConnectionsError
from session.session import Session
from smartinspect import SmartInspect


class SiAuto:
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
