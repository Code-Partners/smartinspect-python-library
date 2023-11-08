from enum import Enum


class ViewerId(Enum):
    METAFILE = 403
    ICON = 402
    JPEG = 401
    BITMAP = 400
    NO_VIEWER = -1
    TITLE = 0
    DATA = 1
    ...
