from enum import Enum


class ViewerId(Enum):
    NO_VIEWER = - 1
    TITLE = 0
    DATA = 1
    LIST = 2
    VALUE_LIST = 3
    INSPECTOR = 4
    TABLE = 5
    WEB = 100
    BINARY = 200
    HTML_SOURCE = 300
    JAVASCRIPT_SOURCE = 301
    VBSCRIPT_SOURCE = 302
    PERL_SOURCE = 303
    SQL_SOURCE = 304
    INI_SOURCE = 305
    PYTHON_SOURCE = 306
    XML_SOURCE = 307
    BITMAP = 400
    JPEG = 401
    ICON = 402
    METAFILE = 403
