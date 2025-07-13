from Crypto.Cipher import DES3, AES
from Crypto.Hash import SHA256
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode as a64encode, b64decode as a64decode
from datetime import datetime, timedelta
from django.utils import timezone  # type: ignore
import zlib
import json
from Main.settings import settingsInterface as settings  # type: ignore
from tools.token import get_token  # type: ignore

DES_3_IV_LENGTH: int = 8
AES_IV_LENGTH: int = 16
SHA256_LENGTH: int = 32
BASE_64_LENGTH: int = 3


def b64encode(s: bytes):
    return a64encode(pad(s, BASE_64_LENGTH), b"-_")


def b64decode(s: str):
    return unpad(a64decode(s, b"-_"), BASE_64_LENGTH)


# Encryption Function
def encrypt_data(key: bytes, jsonObject: dict) -> str:
    data = json.dumps(jsonObject).encode()
    compressed = zlib.compress(data, level=9)
    padded = pad(compressed, DES3.block_size)

    cipher = DES3.new(key, DES3.MODE_CBC)
    encrypted = cipher.encrypt(padded)
    iv = bytes(cipher.iv)  # type: ignore

    iv += encrypted

    return b64encode(iv).decode()


# Decryption Function
def decrypt_data(key: bytes, encrypted_data: str) -> dict:
    _encrypted = b64decode(encrypted_data)
    iv, encrypted = _encrypted[:DES_3_IV_LENGTH], _encrypted[DES_3_IV_LENGTH:]

    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    decompressed = zlib.decompress(unpad(decrypted, DES3.block_size))
    return json.loads(decompressed.decode())


def certificateToken() -> str:
    nowTime = datetime.now(timezone.get_current_timezone())
    nowTime += timedelta(days=settings.CERTIFICATE_EXPIRE_DAYS)

    nowTimeByte: bytes= nowTime.strftime("%H:%M:%d:%m:%Y").encode()

    iv = bytes(AES.new(get_token(AES.block_size).encode(), mode=AES.MODE_CBC).iv)
    cipherA = AES.new(settings.AES_KEY_1, mode=AES.MODE_CBC, iv=iv)
    cipherB = AES.new(settings.AES_KEY_2, mode=AES.MODE_CBC, iv=iv)

    padded = pad(nowTimeByte, AES.block_size)

    encrypt_1 = cipherA.encrypt(padded)
    encryptFinal = cipherB.encrypt(encrypt_1)

    iv += encryptFinal

    return b64encode(iv).decode()


def certificateHash(jsonDict: dict) -> str:
    """certificate (encrypted): {iv = 16 bytes}{certiHash = _ bytes}

    certiHash = {timeToken = _ bytes}{jsonHash = 32 bytes}


    """

    cipher = AES.new(settings.CERTIFICATE_KEY, mode=AES.MODE_CBC)

    token = certificateToken()
    jsonHash = SHA256.new(json.dumps(jsonDict).encode()).hexdigest()

    iv = bytes(cipher.iv)

    certiHash = cipher.encrypt(f"{token}{jsonHash}".encode())

    iv += certiHash

    return b64encode(iv).decode()


def certificateDecrypt(certificate: str) -> tuple[str, str]:
    token, jsonHash = "", ""
    try:
        decoded = b64decode(certificate)
        iv, encrypt = decoded[:AES_IV_LENGTH], decoded[AES_IV_LENGTH:]
        cipher = AES.new(settings.CERTIFICATE_KEY, mode=AES.MODE_CBC, iv=iv)

        decrypt = cipher.decrypt(encrypt)

        token = decrypt[:-SHA256_LENGTH].decode()
        jsonHash = decrypt[-SHA256_LENGTH:].decode()

    except Exception as e:
        print(e)

    return token, jsonHash


def jsonHash(jsons: dict):
    return SHA256.new(json.dumps(jsons).encode()).hexdigest()


def authTokenCheck(token: str):
    """
    Basic Auth Flow =>
            1) Get Date Time as: hour:minute:day:month:year (~16 bytes)
            2) Perform AES twice with aes_key1 and then aes_key2
            3) Encode as base64 string
    """

    try:
        _encrypted = b64decode(token)
        iv, encrypted = _encrypted[:AES_IV_LENGTH], _encrypted[AES_IV_LENGTH:]

        cipherA = AES.new(settings.AES_KEY_2, mode=AES.MODE_CBC, iv=iv)
        cipherB = AES.new(settings.AES_KEY_1, mode=AES.MODE_CBC, iv=iv)

        data = cipherB.decrypt(cipherA.decrypt(encrypted))

        mainData = unpad(data, AES.block_size).decode()

        hour, minute, day, month, year = map(int, mainData.split(":"))

        start_time = datetime(
            year, month, day, hour, minute, tzinfo=timezone.get_current_timezone()
        )

        current_time = datetime.now(timezone.get_current_timezone())

        if current_time > start_time:
            return False
        else:
            return True

    except Exception as e:
        print(f"Auth Token Check failed {e}")
        return False
