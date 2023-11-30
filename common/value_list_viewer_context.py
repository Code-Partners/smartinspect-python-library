from common.list_viewer_context import ListViewerContext
from common.viewer_id import ViewerId


class ValueListViewerContext(ListViewerContext):
    def __init__(self, viewer_id: ViewerId = ViewerId.VALUE_LIST):
        super().__init__(viewer_id)

    def append_key_value(self, key: str, value) -> None:
        if (
                not isinstance(key, str)
        ):
            raise TypeError("arguments must be str")

        if key != "":
            self.append_text(self.escape_item(key))
            self.append_text("=")
            self.append_text(self.escape_item(value))
        self.append_text("\r\n")

    def escape_item(self, item) -> str:
        try:
            item = str(item)
        except TypeError as e:
            item = e.args[0]
        return self.escape_line(item, "\\=")
