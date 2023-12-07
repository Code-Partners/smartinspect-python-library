from abc import ABC, abstractmethod

from connections.options_parser_event import OptionsParserEvent


class OptionsParserListener(ABC):
    
    @abstractmethod
    def on_option(self, event: OptionsParserEvent) -> None:
        pass

