from random import choice
from hashlib import sha256

__TOKEN:str = "qwertyuiopasdfghjklzxcvbnm1234567890"
__LENGTH:int = 32

def get_token():
    return ''.join([__upperCase__(choice(__TOKEN)) for _ in range(__LENGTH)])

def hash_token(token: str, id:int) -> str:
    return sha256(f"{token}{str(id)}".encode()).hexdigest()

def __upperCase__(token: str) -> str:
    return token.upper() if(choice([True,False])) else token.lower()