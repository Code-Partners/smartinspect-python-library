from smartinspect.common.exceptions import SmartInspectError
from smartinspect.connections.options_parser_event import OptionsParserEvent
from smartinspect.connections.options_parser_listener import OptionsParserListener


class OptionsParser:

    def parse(self, protocol: str, options: str, callback: OptionsParserListener) -> None:
        if not isinstance(protocol, str):
            raise TypeError("Protocol must be a string")
        if not isinstance(options, str):
            raise TypeError("Options must be a string")
        if not isinstance(callback, OptionsParserListener):
            raise TypeError("callback must be a OptionsParserListener")

        options = options.strip()
        if len(options) > 0:
            self.__internal_parse(protocol, options, callback)

    def __internal_parse(self, protocol: str, options: str, callback: OptionsParserListener) -> None:
        i = 0
        length = len(options)
        key = ""
        value = ""

        while i < length:
            # Store key
            c = options[i]
            while i < length - 1:
                key += c
                i += 1
                c = options[i]
                if c == '=':
                    break

            if c != '=':
                # The options string is invalid because the '=' character is missing.
                raise SmartInspectError(f'Missing "=" at "{protocol}" protocol')
            elif i < length:
                i += 1

            # Store value
            quoted = False
            while i < length:
                c = options[i]
                i += 1
                if c == '"':
                    if i < length:
                        if options[i] != '"':
                            quoted = not quoted
                            continue
                        else:
                            i += 1  # Skip one '"'
                    else:
                        quoted = not quoted
                        continue
                elif c == ',' and not quoted:
                    break

                value += c

            self.__do_option(callback, protocol, key, value)
            key = ""
            value = ""

    def __do_option(self, callback: OptionsParserListener, protocol: str, key: str, value: str) -> None:
        value = value.strip()
        key = key.lower().strip()

        event = OptionsParserEvent(self, protocol, key, value)
        callback.on_option(event)
