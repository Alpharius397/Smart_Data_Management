from Crypto.PublicKey import RSA

# Generate a random 2048-bit RSA keypair
key = RSA.generate(2048)

# Export the public key in PEM format (send this to server)
public_key_pem = key.publickey().export_key().decode()

# Export private key in PEM format (keep safe on device)
private_key_pem = key.export_key().decode()

print("Public Key:\n", public_key_pem)
print("\nPrivate Key (keep secret!):\n", private_key_pem)

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
import base64

# Your private key
private_key_pem = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAvAWfU1znI/5HTtL0hGl630wlFVVw0z5ix9GD6bQUy6u0wIVL
8g9Qg17Va31XeJTwAffDIXhjGWawLiEd1vi9jXZv2hjTg1T7ouhSrH3dG2T/IJVR
9+ZFUjDBdnAi81PV4Q+ZKj55L2UDzG1+HlctHbnQtlao6/YW2fiurmJ4d4MD5khe
2CgCsch3mHnvw/Gjz+v4x/zjeHv7RiCNavrvrkOvuskfpOJEtYuc2v1pCSxwI4JE
dJkNuNTUiJVAPq7fFrr0d+g0YkVZb0/JLOBW3c8aIcIKWlh8+qOu20j5sEYhyeKB
KwKmuVqnmjt7tAA4M4YbJ1fNuImKTq8f6SXOGQIDAQABAoIBAAcgMGxcoD7vN10f
phgxljBJxrsDALJk0iIQCO+NvV8FrCVCuADdvzenW6/F8Y92l4z/ipPlZ94R0/n/
k82uoiJvG2iY2cVHrny7UMzMPVm5L2kY96ENR1HI2sAmGlD9+6RarruY4AdhjO4N
tUKpm6JdhTEv4hmFO1L594bQ4Q9oZTDVcwZ6k6MXQ20UudQFjKt2d+DIOMBh/CsJ
N0FfHIBscnwBQGeYFAyHGwB2mQoXLjFNOoPUOVHYe36DJjqh+xsUUhP3LmL/TVQn
RIXWOpuE3bMqm///rEWC855JPqlyv4OCndHUE0ZbnBqorszjV+owNuOAVzC+s/hZ
90NPhT0CgYEAv79d7YxEbY3hiPdbA4bBiAotgGxV5PgpSPdu8U6DmI2LIBd1UeMk
Trx4an5Dv9Av23FJisloReCn4aSXx33F3IhA7E/s1UmFyCwF//Am7YyRfeDR8SAU
9rHVIxULYnACNdjkemiWf0jSL+OCjk0YJzRSE9ID/bLG0rw4Tllh1AUCgYEA+waq
jcBLxjxdnY4dTw694yJdKaoAP8+jAi83xuBQFXFg4kDloZt0C4DuWJ6uA4tD7XeO
oJCz5WR//PdaPEy6jWlNQexUSNdHiN4DFnOb3KCHq1md9d0LgQJCGYxhhByWLOZ9
0y26qC5L+DBDiO1fSYBwjG0JHl9kE6I9jSwEIgUCgYA8M3jp+///5WvJ9N8+XDCm
5Ysjpt/Q45kSr5zFZkEqxEXJ7ZOIAiiED+g+hyX+Mv7Tht3wFQwH5GDRFzwQBgz5
EE5R40YYMN0v26KGmH+gVWHYg51mdwwd5/di7FiGr2QCQ/Z3+B5IGDTllCiJROsw
Y9zhHC7kmByUTUPgVW/BgQKBgHT4NDz9H9HtiwnBkPKnwd+2wYaKircxP5ni+rCX
EXoMbMLAzr+xOi+qEmYE+rz4Bdz/WtyC0PDRFbqAX/G9JyiBqthPES8n8VNbcEDj
+fqiatVzWuGX8KZasQZKnZ373BZsCLGAm3uGpyutAasqQL51NPyaSid296EWdmvz
2LEpAoGBAJj2EO25nZ9QH9vWmfMd/sG9TvYclEG4aN0XWwLdV1T7qR6kphzjal8J
yg928+4Y6OMr2zZWJwXmUqRofNvED597WHAL0f41/7NhoXlV5PJB5CHqsTJvv5Tm
xpSnb0UCceJscdhswvifyYluD8JEdV0wJ61vvy9A6oIUYJ9q8qBn
-----END RSA PRIVATE KEY-----"""

ciphertext_b64url = "tIYJWjexVT86eRf0PemdIPYGXD-n6w3wnnTnrgaCqY0ta6FBDzAkD2LOxaHdeGGobRZUQh4QjqCDt4Du3esoXlbhS6ryrVDYmUGE-sY5mt9gwlTHUwI2oNqX-HYmHz54WrYFCAMptLoMLXlyVEWq3ua9rjCVijUF2lT2sL74uHayBo5UjiVBx4K7TrkQ7lQp6bwEPRYgow4W9Isc1T83oCLUao8mxYYMshGI81G4LEfSOs3YjDMIM5syPaA-VMqRBBwTfVbYwARc2y2rnhPGRyh1rxgqFitpyrhQJmcLTXiHA3OCPrH3LtEr1LjS4uaL13jrx7_ZEoVSiiAuuenS_gIC"

# Fix Base64URL -> Base64
ciphertext_b64 = ciphertext_b64url.replace("-", "+").replace("_", "/")
# Add padding if missing

ciphertext = base64.b64decode(ciphertext_b64)

# Load private key
priv_key = RSA.import_key(private_key_pem)
cipher_rsa = PKCS1_OAEP.new(priv_key)

# Decrypt
plaintext = cipher_rsa.decrypt(ciphertext)
print("Decrypted message:", plaintext.decode(errors="ignore"))
