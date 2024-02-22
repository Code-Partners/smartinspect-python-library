import os


class FilePath:

    @staticmethod
    def change_extension(path: str, extension: str) -> str:
        if not isinstance(path, str):
            raise TypeError("path must be an str")
        if not isinstance(extension, str):
            raise TypeError("extension must be an str")

        root = os.path.splitext(path)[0]
        path = root + extension

        return path

    @staticmethod
    def get_extension(path: str) -> str:
        if not isinstance(path, str):
            raise TypeError("path must be an str")

        extension = os.path.splitext(path)[1]
        return extension

    @staticmethod
    def get_directory_name(path: str) -> str:
        if not isinstance(path, str):
            raise TypeError("path must be an str")

        directory_name = os.path.split(path)[0]
        return directory_name

    @staticmethod
    def get_filename(path: str) -> str:
        if not isinstance(path, str):
            raise TypeError("path must be an str")

        filename = os.path.split(path)[1]
        return filename
