from enum import Enum


class ViewerId(Enum):
    """
    Specifies the viewer for displaying the title or data of a Log
    Entry in the Console.

    There are many viewers available for displaying the data of a
    Log Entry in different ways. For example, there are viewers that
    can display lists, tables, binary dumps of data or even websites.

    Every viewer in the Console has a corresponding so-called viewer
    context in this library which can be used to send custom logging
    information. To get started, please see the documentation of the
    Session.log_custom_context() method and ViewerContext class.

    - NO_VIEWER: Instructs the Console to use no viewer at all.
    - TITLE: Instructs the Console to display the title of a Log Entry in a read-only text field.
    - LIST: IInstructs the Console to display the data of a Log Entry as a list.
    - VALUE_LIST: Instructs the Console to display the data of a Log Entry as a key/value list.
    - INSPECTOR: Instructs the Console to display the data of a Log Entry using an object inspector.
    - TABLE: Instructs the Console to display the data of a Log Entry as a table.
    - WEB: Instructs the Console to display the data of a Log Entry as a website.
    - BINARY: Instructs the Console to display the data of a Log Entry as a binary dump using a read-only hex editor.
    - HTML_SOURCE: Instructs the Console to display the data of a Log Entry as HTML source with syntax highlighting.
    - JAVASCRIPT_SOURCE: Instructs the Console to display the data of a Log Entry as JS source with syntax highlighting.
    - VBSCRIPT_SOURCE: Instructs the Console to display the data of a LogEntry as VBScript src with syntax highlighting.
    - PERL_SOURCE: Instructs the Console to display the data of a Log Entry as Perl source with syntax highlighting.
    - SQL_SOURCE: Instructs the Console to display the data of a Log Entry  as SQL source with syntax highlighting.
    - INI_SOURCE: Instructs the Console to display the data of a Log Entry as INI source with syntax highlighting.
    - PYTHON_SOURCE: Instructs the Console to display the data of a Log Entry as Python source with syntax highlighting.
    - XML_SOURCE: Instructs the Console to display the data of a Log Entry as XML source with syntax highlighting.
    - BITMAP: Instructs the Console to display the data of a Log Entry as bitmap image.
    - JPEG: Instructs the Console to display the data of a Log Entry as JPEG image.
    - ICON: Instructs the Console to display the data of a Log Entry as a Windows icon.
    - METAFILE: Instructs the Console to display the data of a Log Entry as Windows Metafile image.
    """
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

    def __str__(self):
        return "%s" % self._name_
