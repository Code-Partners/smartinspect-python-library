from abc import ABC, abstractmethod


class SmartInspectListener(ABC):

    @abstractmethod
    def on_error(self):
        ...
