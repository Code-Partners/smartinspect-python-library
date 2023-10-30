from enum import Enum


class ViewerId(Enum):
    Metafile = 403
    Icon = 402
    Jpeg = 401
    Bitmap = 400
    NoViewer = -1
    Title = 0
    Data = 1
    ...
