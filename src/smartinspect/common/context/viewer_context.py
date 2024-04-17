from abc import abstractmethod

from smartinspect.common.viewer_id import ViewerId


class ViewerContext:
    """
    The ViewerContext class.
    This is the abstract base class for a viewer context. A viewer context
    is the library-side representation of a viewer in the Console.
    A viewer context contains a ViewerId and data which can be
    displayed in a viewer in the Console. Every viewer in the Console
    has a corresponding viewer context class in this library. A viewer
    context is capable of processing data and to format them in a way
    so that the corresponding viewer in the Console can display it.
    Viewer contexts provide a simple way to extend the functionality
    of the SmartInspect Python library. See the Session.log_custom_context
    method for a detailed example.
    :note: This class is not guaranteed to be threadsafe.
    """

    def __init__(self, viewer: ViewerId):
        """
        Initializes a ViewerContext instance.
        :param viewer: The ViewerId to use.
        """
        self.__viewer_id = viewer

    @property
    def viewer_id(self):
        """
        Returns the ViewerId which specifies the viewer to use in the Console.
        """
        return self.__viewer_id

    @property
    @abstractmethod
    def viewer_data(self):
        """
        Returns the actual data which will be displayed in the viewer specified by the ViewerId property.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Overloaded. Releases any managed and unmanaged resources
        of this viewer context.
        """
        pass
