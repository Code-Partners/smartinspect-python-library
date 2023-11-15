from connections.connections_parser_listener import ConnectionsParserListener
from common.events.connections_parser_event import ConnectionsParserEvent
from common.exceptions import SmartInspectException


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
                raise SmartInspectException(
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
                raise SmartInspectException(
                    f"Quoted values not closed at protocol \"{name}\""
                )

            if symbol != ')':
                # The connections string is invalid because the ')'
                # character is missing.
                raise SmartInspectException(
                    f"Missing \")\" at position {pointer + 1}"
                )
            elif pointer < length and connections[pointer] == ',':
                # Skip the ',' character.
                pointer += 1

            print(f'name>>> {name}')
            print(f'options>>> {options}')

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


if __name__ == "__main__":
    protocols = "text(filename=\"C:\\log.txt\", pattern=\"%pattern%\", maxsize=\"1MB\", buffer=\"5MB\", " \
                "level=\"debug\", caption=\"Caption\", reconnect=\"true\"), mem(maxsize=\"123\", " \
                "reconnect.interval=\"123\", backlog.enabled=\"true\", backlog.queue=\"1MB\"), " \
                "pipe(pipename=\"pipe\", backlog.flushon=\"control\", backlog.keepopen=\"false\", " \
                "async.enabled=\"true\"), " \
                "tcp(reconnect=\"true\", async.enabled=\"true\", async.queue=\"100KB\", host=\"example.com\", " \
                "port=\"1234\")"
    ConnectionsParser().parse(protocols, ConnectionsParserListener())
