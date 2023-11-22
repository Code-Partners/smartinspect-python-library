from abc import abstractmethod

from common.viewer_id import ViewerId


class ViewerContext:
    def __init__(self, viewer: ViewerId):
        self.__viewer_id = viewer

    @property
    def viewer_id(self):
        return self.__viewer_id

    @property
    @abstractmethod
    def viewer_data(self):
        pass

    @abstractmethod
    def close(self):
        pass
