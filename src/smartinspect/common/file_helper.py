import datetime
import os
import typing
from pathlib import Path

from smartinspect.common.exceptions import SmartInspectError
from smartinspect.common.file_path import FilePath


class FileHelper:
    _ALREADY_EXISTS_SUFFIX: str = "a"
    _DATETIME_FORMAT: str = "%Y-%m-%d-%H-%M-%S"
    _FORMATTED_DATETIME_LENGTH: int = 19
    _DATETIME_SEPARATOR: str = "-"
    _DATETIME_TOKENS: int = 6

    @classmethod
    def get_file_date(cls, basename: str, path: str) -> typing.Optional[datetime.datetime]:
        if not isinstance(basename, str):
            raise TypeError("basename must be an str")
        if not isinstance(path, str):
            raise TypeError("path must be an str")

        date = cls._try_get_file_date(basename, path)
        if date is None:
            raise SmartInspectError("Invalid filename")

        return date

    @classmethod
    def _try_get_file_date(cls, basename: str, path: str) -> typing.Optional[datetime.datetime]:
        filename = FilePath.get_filename(path)
        basename = FilePath.change_extension(FilePath.get_filename(basename), "")

        idx = filename.find(basename)

        if idx != 0:
            return None

        value = FilePath.change_extension(filename[len(basename) + 1:], "")

        if len(value) > cls._FORMATTED_DATETIME_LENGTH:
            value = value[: cls._FORMATTED_DATETIME_LENGTH]

        return cls._try_parse_file_date(value)

    @classmethod
    def _try_parse_file_date(cls, filedate: str) -> typing.Optional[datetime.datetime]:
        if len(filedate) != cls._FORMATTED_DATETIME_LENGTH:
            return None

        for symbol in filedate:
            if not symbol.isdigit() and symbol != cls._DATETIME_SEPARATOR[0]:
                return None

        values = filedate.split(cls._DATETIME_SEPARATOR)

        if len(values) != cls._DATETIME_TOKENS:
            return None

        # year, month, day, hour, minutes and seconds are cast into ints and then
        # unpacked as arguments to create a datetime object
        return datetime.datetime(*[int(val) for val in values], tzinfo=datetime.timezone.utc)

    @classmethod
    def _is_valid_file(cls, basename: str, path: str) -> bool:
        return cls._try_get_file_date(basename, path) is not None

    @classmethod
    def get_filename(cls, basename: str, append: bool) -> str:
        if not isinstance(basename, str):
            raise TypeError("basename must be an str")
        if not isinstance(append, bool):
            raise TypeError("append must be a bool")

        if append:
            filename = cls._find_filename(basename)

            if filename is not None:
                return filename

        return cls._expand_filename(basename)

    @classmethod
    def _find_filename(cls, basename: str) -> typing.Optional[str]:
        files = cls._get_files(basename)
        if files is None or len(files) == 0:
            return None

        return files[-1]

    @classmethod
    def _expand_filename(cls, basename: str) -> str:
        now = datetime.datetime.now(datetime.timezone.utc)
        date = now.strftime(cls._DATETIME_FORMAT)

        result = "".join([
            FilePath.change_extension(basename, ""),
            "-",
            date,
            FilePath.get_extension(basename)
        ])

        while os.path.isfile(result):
            result = "".join([
                FilePath.change_extension(result, ""),
                cls._ALREADY_EXISTS_SUFFIX,
                FilePath.get_extension(result)
            ])

        return result

    @classmethod
    def _get_files(cls, basename: str) -> typing.List[str]:
        directory_name = FilePath.get_directory_name(basename)

        if len(directory_name) == 0:
            directory = Path("")
        else:
            directory = Path(directory_name)

        filename = FilePath.get_filename(basename)
        file_extension = FilePath.get_extension(filename)
        file_prefix = FilePath.change_extension(filename, "")

        available_files = [file.name for file in Path(directory).glob("*{}".format(file_extension))]

        filtered_files = filter(
            lambda x: (x.startswith(file_prefix) and cls._is_valid_file(basename, x)), available_files)

        files = list(filtered_files)

        if len(files) == 0:
            return files

        if len(directory_name) != 0:
            if not directory_name.endswith(os.sep):
                directory_name += os.sep

            files = [directory_name + filename for filename in files]

        files.sort()
        return files

    @classmethod
    def delete_files(cls, basename: str, max_parts: int) -> None:
        files = cls._get_files(basename)

        length = len(files)

        if length == 0:
            return

        for i in range(length):
            if i + max_parts >= length:
                break
            Path(files[i]).unlink()
