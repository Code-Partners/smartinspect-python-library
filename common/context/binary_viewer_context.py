from common.context.binary_context import BinaryContext
from common.viewer_id import ViewerId


class BinaryViewerContext(BinaryContext):

    def __init__(self):
        super().__init__(ViewerId.BINARY)
