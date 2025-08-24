from hashlib import sha256
from Crypto.Random.random import choice

TOKEN: str = "qwertyuiopasdfghjklzxcvbnm1234567890_-"
LENGTH: int = 32

def get_token(size: int = LENGTH):
    return "".join([__upperCase__(choice(TOKEN)) for _ in range(size)])


def hash_token(token: str, id: int) -> str:
    return sha256(f"{token}{str(id)}".encode()).hexdigest()


def __upperCase__(token: str) -> str:
    return token.upper() if (choice([True, False])) else token.lower()
