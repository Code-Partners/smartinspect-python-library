from smartinspect.common.context.text_context import TextContext
from smartinspect.common.viewer_id import ViewerId


class DataViewerContext(TextContext):
    """
    Represents the data viewer in the Console which can display simple
    and unformatted text.

    .. note::
       The data viewer in the Console interprets the data of a Log Entry as text and displays it in a read-only text
       field.

       You can use the DataViewerContext class for creating custom log
       methods around LogCustomContext for
       sending custom text data.

    .. note::
      This class is not guaranteed to be threadsafe.
    """

    def __init__(self):
        """
        Initializes a DataViewerContext instance.
        """
        super().__init__(ViewerId.DATA)
