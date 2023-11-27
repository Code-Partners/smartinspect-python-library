from common.value_list_viewer_context import ValueListViewerContext
from common.viewer_id import ViewerId


class InspectorViewerContext(ValueListViewerContext):
    def __init__(self):
        super().__init__(ViewerId.INSPECTOR)

    def start_group(self, group: str):
        if isinstance(group, str):
            self.append_text("[")
            self.append_text(self.escape_item(group))
            self.append_text("]")

    def escape_item(self, item: str) -> str:
        return self.escape_line(item, "\\=[]")
