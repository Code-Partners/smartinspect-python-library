from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


class SICipher:
    def __init__(self, key: bytes, iv: bytes) -> None:
        self._validate_arg(key, "key")
        self._validate_arg(iv, "iv")

        self._cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        self._padder = padding.PKCS7(128).padder()
        self._encryptor = self._cipher.encryptor()

    def update(self, data: bytes):
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")

        return self._encryptor.update(self._padder.update(data))

    def finalize(self):
        return self._encryptor.update(self._padder.finalize()) + self._encryptor.finalize()

    @staticmethod
    def _validate_arg(arg: object, arg_name: str) -> None:
        if not isinstance(arg, bytes):
            raise TypeError("%s must be bytes" % arg_name)

        if len(arg) != 16:
            raise ValueError("%s length must be 16 bytes" % arg_name)
