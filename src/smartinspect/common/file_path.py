import os


class FilePath:
    """
    Provides static methods to perform certain operations on strings which represent a path.

    The FilePath class provides several methods to perform transformations on path strings. This class only transforms
    strings and does no operations on the corresponding filesystem entries. For example, the change_extension()
    method changes the extension of a given path string but does not change the actual filesystem entry.
    Operations are done in a cross-platform manner.

    .. note::
       This class is not guaranteed to be threadsafe.
    """

    @staticmethod
    def change_extension(path: str, extension: str) -> str:
        """
        Changes the file extension of a filename for a given path.

        If the supplied path argument is empty string, the return value of this method is empty string as well.
        If the supplied extension argument is empty string, an existing file extension is removed from the given path.

        :param path: The path information to modify. Allowed to be empty string.
        :param extension: The file extension (with leading period).
        Specify an empty string to remove an existing file extension

        :return: The supplied path but with the changed or removed extension
        """
        if not isinstance(path, str):
            raise TypeError("path must be an str")
        if not isinstance(extension, str):
            raise TypeError("extension must be an str")

        root = os.path.splitext(path)[0]
        path = root + extension

        return path

    @staticmethod
    def get_extension(path: str) -> str:
        """
        Returns the file extension of a filename for a given path.
        This method returns the file extension of the given path string
        including the leading period character. If the supplied path
        parameter is empty or does not contain an extension,
        the return value of this method is an empty string.

        :param path: The path from which to get the extension
        :return: The file extension of the supplied path if available or an empty
        string otherwise
        """
        if not isinstance(path, str):
            raise TypeError("path must be an str")

        extension = os.path.splitext(path)[1]
        return extension

    @staticmethod
    def get_directory_name(path: str) -> str:
        """
        Returns the directory name for a given path.

        This method returns the directory name of the given path string. If the supplied path parameter is empty,
        the return value of this method is empty as well.

        :param path: The path from which to get the directory name. Allowed to be empty string.
        :return: The directory of the supplied path if available or empty string if the supplied path argument is empty.
        """
        if not isinstance(path, str):
            raise TypeError("path must be an str")

        directory_name = os.path.split(path)[0]
        return directory_name

    @staticmethod
    def get_filename(path: str) -> str:
        """
        Returns the file name for a given path.

        This method returns the file name of the given path string
        excluding any directory or volume separator characters. If the
        supplied path parameter is empty, the return value
        of this method is empty as well. If the last character of the
        supplied path argument is a directory or volume character, then
        the return value of this method is an empty string.

        :param path: The path from which to get the file name. Allowed to be empty string.
        :return: The file name of the supplied path if available or empty string if the
        supplied path argument is empty.
        """
        if not isinstance(path, str):
            raise TypeError("path must be an str")

        filename = os.path.split(path)[1]
        return filename
