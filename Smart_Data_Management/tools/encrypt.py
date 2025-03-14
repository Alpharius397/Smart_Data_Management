from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode
import zlib
import json

# Encryption Function
def encrypt_data(key: bytes, jsonObject: dict) -> str:
    data = json.dumps(jsonObject).encode()
    compressed = zlib.compress(data, level=9)
    padded = pad(compressed, DES3.block_size)
    
    cipher = DES3.new(key, DES3.MODE_CBC)
    encrypted = cipher.encrypt(padded)
    iv = b64encode(cipher.iv).decode()
    
    encrypted_b64 = b64encode(encrypted).decode()
    
    return f"{iv}:{encrypted_b64}"

# Decryption Function
def decrypt_data(key: bytes, encrypted_data: str) -> str:
    iv, encrypted_b64 = encrypted_data.split(":")
    iv = b64decode(iv)
    encrypted = b64decode(encrypted_b64)
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    decompressed = zlib.decompress(unpad(decrypted, DES3.block_size))
    return json.loads(decompressed.decode())