from Crypto.Cipher import DES3
from Crypto.Hash import SHA256
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode
from datetime import datetime
from django.utils import timezone #type: ignore
import zlib
import json
from django.conf import settings #type: ignore

IV_LENGTH: int = 12

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

def getAuthKey():
    nowTime = datetime.now(timezone.get_current_timezone()).strftime("%H:%d:%m:%Y").encode()
    
    hashKey = SHA256.new(nowTime)
    hashKey.update(settings.API_KEY.encode())
    hashKey.update(settings.SECURE_KEY.encode())
    
    return hashKey.hexdigest()
