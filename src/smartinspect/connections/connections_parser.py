from smartinspect.common.events.connections_parser_event import ConnectionsParserEvent
from smartinspect.common.exceptions import SmartInspectError
from smartinspect.connections.connections_parser_listener import ConnectionsParserListener


class ConnectionsParser:
    def __do_protocol(self, callback: ConnectionsParserListener, protocol: str, options: str) -> None:
        options = options.strip()
        protocol = protocol.lower().strip()

        event = ConnectionsParserEvent(self, protocol, options)

        callback.on_protocol(event)

    def __internal_parse(self, connections: str, callback: ConnectionsParserListener) -> None:
        length = len(connections)
        name = ""
        options = ""
        symbol = ""
        pointer = 0

        while pointer < length - 1:
            # Store protocol name.
            while pointer < length:
                symbol = connections[pointer]
                if symbol == '(':
                    break
                else:
                    name += symbol
                    pointer += 1

            if symbol != "(":
                # The connections string is invalid because the '('
                # character is missing.
                raise SmartInspectError(
                    f"Missing \"(\" at position {pointer + 1}"
                )
            else:
                pointer += 1

            # Store protocol options.
            quoted = False
            while pointer < length:
                symbol = connections[pointer]
                pointer += 1
                if symbol == '"':
                    if pointer < length:
                        if connections[pointer] != '"':
                            quoted = not quoted
                        else:
                            pointer += 1
                            options += '"'
                elif symbol == ')' and not quoted:
                    break
                options += symbol

            if quoted:
                raise SmartInspectError(
                    f"Quoted values not closed at protocol \"{name}\""
                )

            if symbol != ')':
                # The connections string is invalid because the ')'
                # character is missing.
                raise SmartInspectError(
                    f"Missing \")\" at position {pointer + 1}"
                )
            elif pointer < length and connections[pointer] == ',':
                # Skip the ',' character.
                pointer += 1

            self.__do_protocol(callback, name, options)
            name = ""
            options = ""

    def parse(self, connections: str, callback: ConnectionsParserListener) -> None:
        if not isinstance(connections, str):
            raise TypeError("connections must be a string")
        elif not isinstance(callback, ConnectionsParserListener):
            raise TypeError("callback must be a ConnectionsParserListener")
        else:
            connections = connections.strip()
            if len(connections) > 0:
                self.__internal_parse(connections, callback)
