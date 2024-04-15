from enum import Enum

from smartinspect.common.viewer_id import ViewerId


class SourceId(Enum):
    """
    Used in the LogSource methods of the Session class to specify
    the type of source code.

    Instructs the Session.log_source() methods to use syntax highlighting for relevant languages.

    - HTML: Instructs the Session.log_source() methods to use syntax highlighting for HTML
    - JAVASCRIPT: Instructs the Session.log_source() methods to use syntax highlighting for JAVASCRIPT
    - VBSCRIPT: Instructs the Session.log_source() methods to use syntax highlighting for VBSCRIPT
    - PERL: Instructs the Session.log_source() methods to use syntax highlighting for PERL
    - SQL: Instructs the Session.log_source() methods to use syntax highlighting for SQL
    - INI: Instructs the Session.log_source() methods to use syntax highlighting for INI
    - PYTHON: Instructs the Session.log_source() methods to use syntax highlighting for PYTHON
    - XML: Instructs the Session.log_source() methods to use syntax highlighting for XML
    """
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

    # Left as reference to SI Java lib
    def __str__(self):
        if self.__str == "":
            self.__str = str(self.viewer_id)
            index = self.__str.rfind("SOURCE")

            if index != -1:
                self.__str = self.__str[:index - 1]
        return self.__str
