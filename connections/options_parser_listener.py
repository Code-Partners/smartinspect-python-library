from abc import ABC, abstractmethod

from connections.options_parser_event import OptionsParserEvent


class OptionsParserListener:

    @staticmethod
    def on_option(event: OptionsParserEvent) -> None:
        pass

