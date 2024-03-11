from .tokens import *
from .token_abc import Token


class TokenFactory:
    tokens = {
        "/%appname/%": AppNameToken,
        "/%session/%": SessionToken,
        "/%hostname/%": HostNameToken,
        "/%title/%": TitleToken,
        "/%timestamp/%": TimestampToken,
        "/%level/%": LevelToken,
        "/%color/%": ColorToken,
        "/%logentrytype/%": LogEntryTypeToken,
        "/%viewerid/%": ViewerIdToken,
        "/%thread/%": ThreadIdToken,
        "/%process/%": ProcessIdToken,
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
        if not isinstance(value, str):
            raise TypeError("value must be an str")

        length = len(value)

        if length <= 2:
            return cls._create_literal(value)

        if value[:2] != "/%" or value[-2:] != "/%":
            return cls._create_literal(value)

        original = value
        options = ""

        # extract the token options: /%token{options}/%
        if value[-3] == "}":
            idx = value.find("{")

            if idx > -1:
                idx += 1
                options = value[idx: -3]
                value = value[:idx - 1] + value[-2:]
                length = len(value)

        width = ""
        idx = value.find(",")

        # extract the token width: /%token, width/%
        if idx > -1:
            idx += 1
            width = value[idx: -2]
            value = value[: idx - 1] + value[length - 2:]

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
