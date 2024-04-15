import typing
from io import BytesIO

from smartinspect.protocols.file_protocol.si_cipher import SICipher


class CipheredIO(BytesIO):
    """
    CipheredIO class wraps a binary IO  stream together with a cipher for encryption purposes
    and provides necessary methods to implement encryption in SmartInspect Python library.

    For more information on encryption details please see SICipher class.
    """

    def __init__(self, stream: typing.BinaryIO, cipher: SICipher) -> None:
        """
        Initializes a CipheredIO instance.
        :param stream: underlying IO stream which is actually used for IO operations
        :param cipher: SICipher object used for encryption of the data written to the underlying stream.
        """
        super().__init__()
        self._stream: typing.BinaryIO = stream
        self._cipher: SICipher = cipher

    def write(self, data: bytes) -> int:
        """
        Writes the encrypted data to the underlying stream. Data is encrypted using SI Cipher.
        :param data: bytes sequence to be encrypted and written to the underlying stream.
        """
        encrypted_data = self._cipher.update(data)
        return self._stream.write(encrypted_data)

    def close(self) -> None:
        """
        Finalizes the encryption process using SICipher object and closes the underlying stream.
        """
        finalization = self._cipher.finalize()
        self._stream.write(finalization)
        self._stream.close()
        super().close()
