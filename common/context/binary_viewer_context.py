from common.context.binary_context import BinaryContext
from common.viewer_id import ViewerId


class BinaryViewerContext(BinaryContext):
    """Represents the binary viewer in the Console which can display binary
       data in a read-only hex editor.

       .. note::

           The binary viewer in the Console interprets the data of a Log Entry as binary data
           and displays it in a read-only hex editor.

           You can use the BinaryViewerContext class for creating custom log
           methods around for sending custom binary data.

       .. note::

           This class is not guaranteed to be threadsafe.
    """
    def __init__(self):
        """
        Creates and initializes a BinaryViewerContext instance.
        """
        super().__init__(ViewerId.BINARY)
