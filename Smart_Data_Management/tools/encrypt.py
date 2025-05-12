from Crypto.Cipher import DES3, AES
from Crypto.Hash import SHA256
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode as a64encode, b64decode as a64decode
from datetime import datetime, timedelta
from django.utils import timezone #type: ignore
import zlib
import json
from Main.settings import settingsInterface as settings #type: ignore
from tools.token import get_token #type: ignore

def b64encode(s: bytes):
    return a64encode(s, b'-_')

def b64decode(s: str):
    return a64decode(s, b'-_')

DES_3_IV_LENGTH: int = 12
AES_IV_LENGTH_BASE_64: int = 24

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
    _iv, encrypted_b64 = encrypted_data[:DES_3_IV_LENGTH], encrypted_data[DES_3_IV_LENGTH:]
    iv = b64decode(_iv)
    encrypted = b64decode(encrypted_b64)
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    decompressed = zlib.decompress(unpad(decrypted, DES3.block_size))
    return json.loads(decompressed.decode())

def monthYearHash():
    nowTime = datetime.now(timezone.get_current_timezone())
    nowTime += timedelta(days=settings.CERTIFICATE_EXPIRE_DAYS)
    
    nowTime = nowTime.strftime("%H:%M:%d:%m:%Y").encode()
    
    iv = AES.new(get_token(AES.block_size).encode(), mode=AES.MODE_CBC).iv
    cipherA = AES.new(settings.AES_KEY_1.encode(), mode=AES.MODE_CBC, iv=iv)
    cipherB = AES.new(settings.AES_KEY_2.encode(), mode=AES.MODE_CBC, iv=iv)
    
    padded = pad(nowTime, AES.block_size)
    
    encrypt_1 = cipherA.encrypt(padded)
    encryptFinal = cipherB.encrypt(encrypt_1)
    
    return f"{b64encode(iv).decode()}{b64encode(encryptFinal).decode()}"

def jsonHash(jsons: dict):
    return SHA256.new(json.dumps(jsons).encode()).hexdigest()

"""
Basic Auth Flow =>
    1) Get Date Time as: hour:minute:day:month:year (16 bytes)
    2) Perform AES twice with aes_key1 and then aes_key2
    3) Encode as base64 string
"""
def authTokenCheck(token: str, fromGolang: bool = True):
    
    _iv, _encrypted = token[:AES_IV_LENGTH_BASE_64], token[AES_IV_LENGTH_BASE_64:]
    iv = b64decode(_iv)
    encrypted = b64decode(_encrypted)
    
    cipherA = AES.new(settings.AES_KEY_2.encode(), mode=AES.MODE_CBC, iv=iv)
    cipherB = AES.new(settings.AES_KEY_1.encode(), mode=AES.MODE_CBC, iv=iv)
    
    data = cipherB.decrypt(cipherA.decrypt(encrypted))
    
    if(fromGolang):
        padLength = data[-1]
        
        mainData = data[:-padLength].decode()
        
    else:
        mainData = unpad(data, AES.block_size).decode()
    
    hour, minute, day, month, year = map(int,mainData.split(":"))

    start_time = datetime(year, month, day, hour, minute, tzinfo=timezone.get_current_timezone())
    
    current_time = datetime.now(timezone.get_current_timezone())

    if(current_time>start_time):
        return False
    else:
        return True
