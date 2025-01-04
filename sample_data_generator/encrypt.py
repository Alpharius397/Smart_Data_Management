from Crypto.Cipher import DES3
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode
import zlib
import json
from PIL import Image
from io import BytesIO

# Encryption Function
def encrypt_data(key: bytes, jsonObject: dict):
    data = json.dumps(jsonObject).encode()
    compressed = zlib.compress(data, level=9)
    padded = pad(compressed, DES3.block_size)
    
    cipher = DES3.new(key, DES3.MODE_CBC)
    encrypted = cipher.encrypt(padded)
    iv = b64encode(cipher.iv).decode()
    
    encrypted_b64 = b64encode(encrypted).decode()
    return f"{iv}:{encrypted_b64}"

# Decryption Function
def decrypt_data(key: bytes, encrypted_data: str):
    iv, encrypted_b64 = encrypted_data.split(":")
    iv = b64decode(iv)
    encrypted = b64decode(encrypted_b64)
    cipher = DES3.new(key, DES3.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted)
    decompressed = zlib.decompress(unpad(decrypted, DES3.block_size))
    return json.loads(decompressed.decode())

# Example Usage
key = b"123456789123456789123456"  # Must be 24 bytes for 3DES
json_obj = {"a": 1, "b": 2, "c": 3}

# Encrypt
encrypted = encrypt_data(key, json_obj)
print("Encrypted Data:", encrypted)

# Decrypt
decrypted = decrypt_data(key, encrypted)
print("Decrypted Data:", decrypted)

im = Image.open("sample_data_generator/img/504708-200.png")
out = BytesIO()
asd = im.save(out,'png',quality=95)

with open("sample_data_generator/img/asd.txt",'w') as g:
    g.write(b64encode(out.getvalue()).decode())
    
# a = Image.open(out)
# print(a.width,a.height)
# a=a.resize((780,438),resample=3)
# a.save("C://Users//RAJ//Desktop//Intern//Smart_Data_Management//sample_data_generator//img//generated-1.jpg",quality=95)