from enum import Enum

from common.viewer_id import ViewerId


class SourceId(Enum):
    HTML = ViewerId.HTML_SOURCE
    JAVASCRIPT = ViewerId.JAVASCRIPT_SOURCE
    VBSCRIPT = ViewerId.VBSCRIPT_SOURCE
    PERL = ViewerId.PERL_SOURCE
    SQL = ViewerId.SQL_SOURCE
    INI = ViewerId.INI_SOURCE
    PYTHON = ViewerId.PYTHON_SOURCE
    XML = ViewerId.XML_SOURCE

    def __init__(self, viewer_id: ViewerId):
        self.__viewer_id = viewer_id
        self.__str = ""

    @property
    def viewer_id(self):
        return self.__viewer_id

    # do we need the __str__(to_string method here?)
    def __str__(self):
        if self.__str == "":
            self.__str = str(self.viewer_id)
            index = self.__str.rfind("SOURCE")

            if index != -1:
                self.__str = self.__str[:index - 1]
        return self.__str

