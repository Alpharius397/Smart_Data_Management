from hashlib import sha256
from Crypto.Random.random import choice

__TOKEN: str = "qwertyuiopasdfghjklzxcvbnm1234567890_-"
__LENGTH: int = 32


def get_token(size: int = __LENGTH):
    return "".join([__upperCase__(choice(__TOKEN)) for _ in range(size)])


def hash_token(token: str, id: int) -> str:
    return sha256(f"{token}{str(id)}".encode()).hexdigest()


def __upperCase__(token: str) -> str:
    return token.upper() if (choice([True, False])) else token.lower()
