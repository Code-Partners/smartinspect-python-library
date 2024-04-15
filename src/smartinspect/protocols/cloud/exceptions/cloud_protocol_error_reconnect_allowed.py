from smartinspect.protocols.cloud.exceptions.cloud_protocol_error import CloudProtocolError


class CloudProtocolErrorReconnectAllowed(CloudProtocolError):
    def __init__(self, message: str):
        super().__init__(message)
