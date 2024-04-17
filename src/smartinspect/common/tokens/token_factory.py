from .tokens import *
from .token_abc import Token


class TokenFactory:
    """
    Creates instances of Token subclasses.

    This class has only one public method called get_token(), which
    is capable of creating Token objects depending on the given
    argument.

    .. note::
       This class is not guaranteed to be threadsafe.
    """
    tokens = {
        "$appname$": AppNameToken,
        "$session$": SessionToken,
        "$hostname$": HostNameToken,
        "$title$": TitleToken,
        "$timestamp$": TimestampToken,
        "$level$": LevelToken,
        "$color$": ColorToken,
        "$logentrytype$": LogEntryTypeToken,
        "$viewerid$": ViewerIdToken,
        "$thread$": ThreadIdToken,
        "$process$": ProcessIdToken,
    }

    @staticmethod
    def _create_literal(value: str) -> Token:
        if not isinstance(value, str):
            raise TypeError("value must be an str")
        token = LiteralToken()
        token.options = ""
        token.value = value
        token.width = 0
        return token

    @classmethod
    def get_token(cls, value: str) -> Token:
        """Creates instance of Token subclasses.

        :param value: The original string representation of the token.
        :return: An appropriate Token object for the given string representation of a token.

        This method analyses and parses the supplied representation of a token and creates
        an appropriate Token object. For example, if the value argument is set to "$session$",
        a Token object is created and returned which is responsible for expanding the $session$
        variable. For a list of available tokens and a detailed description, please have a look
        at the PatternParser class, especially the PatternParser pattern property.
        """
        if not isinstance(value, str):
            raise TypeError("value must be an str")

        length = len(value)

        if length <= 2:
            return cls._create_literal(value)

        if value[0] != "$" or value[-1] != "$":
            return cls._create_literal(value)

        original = value
        options = ""

        # extract the token options: $token{options}$
        if value[-2] == "}":
            idx = value.find("{")

            if idx > -1:
                idx += 1
                options = value[idx: -2]
                value = value[:idx - 1] + value[-1]

        width = ""
        idx = value.find(",")

        # extract the token width: $token, width$
        if idx > -1:
            idx += 1
            width = value[idx: -1]
            value = value[: idx - 1] + value[-1]

        value = value.lower()
        impl = cls.tokens.get(value)
        if impl is None:
            return cls._create_literal(original)

        # noinspection PyBroadException
        try:
            token: Token = impl()
            token.options = options
            token.value = original
            token.width = cls._parse_width(width)
        except Exception:
            return cls._create_literal(original)

        return token

    @staticmethod
    def _parse_width(value: str) -> int:
        if not isinstance(value, str):
            raise TypeError("value must be an str")

        value = value.strip()
        if len(value) == 0:
            return 0

        try:
            width = int(value)
        except ValueError:
            width = 0

        return width
