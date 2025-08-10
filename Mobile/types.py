from typing import TypedDict
from tools.typesCauseWhyNot import NullStr


class TokenResponse(TypedDict):
    access: NullStr
    refresh: NullStr
    status: bool
    error: list[str]


class LoginResponse(TokenResponse):
    pass


class RegisterResponse(TokenResponse):
    pass


class SubscriberResponse(TokenResponse):
    pass


class CardData(TypedDict):
    cardID: str
    timestamp: str
    university: str
    institute: str
    branch: str


class CardResponse(TokenResponse):
    cards: list[CardData]
    nextPage: int


class UserInfoResponse(TokenResponse):
    username: NullStr
    email: NullStr


class CredResponse(TokenResponse):
    pass


class DeleteResponse(TokenResponse):
    pass


class OtpResponse(TokenResponse):
    pass
