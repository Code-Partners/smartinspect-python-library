from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


class SICipher:
    """
    SI Cipher class encapsulates the details of encryption algorithm used in SmartInspect Python library.
    """

    def __init__(self, key: bytes, iv: bytes) -> None:
        """
        Initializes a SI Cipher object which can be used to encrypt binary data stored in SmartInspect log files.
        :param key: byte sequence to be used as a secret key.
        :param iv: byte sequence to be used as initialization vector.
        """
        self._validate_arg(key, "key")
        self._validate_arg(iv, "iv")

        self._cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        self._padder = padding.PKCS7(128).padder()
        self._encryptor = self._cipher.encryptor()

    def update(self, data: bytes) -> bytes:
        """
        This method is used to update the previously encrypted byte sequence and return an updated sequence.
        The encryption process is not finalized until the finalize() method is called.
        :param data: byte sequence to encrypt.
        """
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")

        return self._encryptor.update(self._padder.update(data))

    def finalize(self) -> bytes:
        """
        Finalizes the encryption process of any previously written byte sequence.
        The encryption is not finished before calling this method, which means also that the encrypted sequence
        still cannot be read with the provided password because the sequence has not been finalized yet.
        """
        return self._encryptor.update(self._padder.finalize()) + self._encryptor.finalize()

    @staticmethod
    def _validate_arg(arg: object, arg_name: str) -> None:
        if not isinstance(arg, bytes):
            raise TypeError("%s must be bytes" % arg_name)

        if len(arg) != 16:
            raise ValueError("%s length must be 16 bytes" % arg_name)
