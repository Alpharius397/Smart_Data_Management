from Crypto.Cipher import DES3, AES
from Crypto.Hash import SHA256
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode
from datetime import datetime, timedelta
from django.utils import timezone #type: ignore
import zlib
import json
from Main.settings import settingsInterface as settings #type: ignore

IV_LENGTH: int = 12
MAX_DURATION: int = 300

# Encryption Function
def encrypt_data(key: bytes, jsonObject: dict) -> str:
    data = json.dumps(jsonObject).encode()
    compressed = zlib.compress(data, level=9)
    padded = pad(compressed, DES3.block_size)
    
    cipher = DES3.new(key, DES3.MODE_CBC)
    encrypted = cipher.encrypt(padded)
    iv = b64encode(cipher.iv).decode() #type: ignore
    
    encrypted_b64 = b64encode(encrypted).decode()
    
    return f"{iv}{encrypted_b64}"

# Decryption Function
def decrypt_data(key: bytes, encrypted_data: str) -> dict:
    _iv, encrypted_b64 = encrypted_data[:IV_LENGTH], encrypted_data[IV_LENGTH:]
    iv = b64decode(_iv)
    encrypted = b64decode(encrypted_b64)
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    decompressed = zlib.decompress(unpad(decrypted, DES3.block_size))
    return json.loads(decompressed.decode())

def monthYearHash():
    nowTime = datetime.now(timezone.get_current_timezone())
    return SHA256.new(f"{nowTime.month}/{nowTime.year}".encode()).hexdigest()

def jsonHash(jsons: dict):
    return SHA256.new(json.dumps(jsons).encode()).hexdigest()

"""
Basic Auth Flow =>
    1) Get Date Time as: hour:minute:day:month:year (16 bytes)
    2) Perform AES twice with aes_key1 and thne aes_key2
    3) Encode as hex string
"""
def authTokenCheck(token: str):
    
    _iv, _encrypted = token[:24], token[24:]
    iv = b64decode(_iv)
    encrypted = b64decode(_encrypted)
    
    cipherA = AES.new(settings.AES_KEY_2.encode(), mode=AES.MODE_CBC, iv=iv)
    cipherB = AES.new(settings.AES_KEY_1.encode(), mode=AES.MODE_CBC, iv=iv)
    
    data = cipherB.decrypt(cipherA.decrypt(encrypted))
    padLength = data[-1]
    
    mainData = data[:-padLength].decode()
    
    hour, minute, day, month, year = map(int,mainData.split(":"))

    start_time = datetime(year, month, day, hour, minute, tzinfo=timezone.get_current_timezone())
    
    current_time = datetime.now(timezone.get_current_timezone())

    difference: timedelta = current_time - start_time
    
    if(difference.seconds>MAX_DURATION):
        return False
    else:
        return True
