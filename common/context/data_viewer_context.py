from common.context.text_context import TextContext
from common.viewer_id import ViewerId


class DataViewerContext(TextContext):
    def __init__(self):
        super().__init__(ViewerId.DATA)
