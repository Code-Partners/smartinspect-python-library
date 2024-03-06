import typing
from io import BytesIO

from protocols.file_protocol.si_cipher import SICipher


class CipheredIO(BytesIO):
    def __init__(self, stream: typing.BinaryIO, cipher: SICipher) -> None:
        super().__init__()
        self._stream: typing.BinaryIO = stream
        self._cipher: SICipher = cipher

    def write(self, data: bytes) -> int:
        encrypted_data = self._cipher.update(data)
        return self._stream.write(encrypted_data)

    def close(self) -> None:
        finalization = self._cipher.finalize()
        self._stream.write(finalization)
        self._stream.close()
        super().close()

