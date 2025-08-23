from typing import TypedDict
from tools.types import NullStr
from User.models import User
import datetime
from django.utils import timezone  # type: ignore
import jwt
import json
from Main.settings import settingsInterface as settings
import typing


class PayLoad:
    __type: str = "Base"
    expire_minutes: int

    def __init__(
        self,
        user: User,
        expire: datetime.datetime | None = None,
        type: str | None = None,
    ):
        self.username: str = user.username
        self.userID: int = user.id
        self.type = type if (type is not None) else self.__type
        self.expire = expire if (expire is not None) else timezone.now()

    def to_json(self, newToken: bool = False) -> dict[str, str | int]:
        return {
            "userID": self.userID,
            "username": self.username,
            "type": self.type,
            "expire": (
                (self.expire if (not newToken) else timezone.now())
                + datetime.timedelta(minutes=self.expire_minutes)
            ).isoformat(),
        }

    def getToken(self, newToken: bool = False):
        return str(
            jwt.encode(
                self.to_json(newToken), settings.JWT_SECRET, settings.JWT_ALGORITHM
            )
        )

    def isCorrectType(self) -> bool:
        return self.type == self.__type

    def __str__(self):
        return json.dumps(
            {
                "userID": self.userID,
                "username": self.username,
                "type": self.type,
                "expire": (
                    self.expire + datetime.timedelta(minutes=self.expire_minutes)
                ).isoformat(),
            }
        )

    @staticmethod
    def from_json(
        classConstruct: type["PayLoad"],
        userID: int,
        username: str,
        type: str,
        expire: str,
    ) -> "PayLoad":
        user: User = User.objects.get(id=userID, username=username)
        return classConstruct(
            user=user, type=type, expire=datetime.datetime.fromisoformat(expire)
        )

    @staticmethod
    async def afrom_json(
        classConstruct: type["PayLoad"],
        userID: int,
        username: str,
        type: str,
        expire: str,
    ) -> "PayLoad":
        user: User = await User.objects.aget(id=userID, username=username)
        return classConstruct(
            user=user, type=type, expire=datetime.datetime.fromisoformat(expire)
        )

    @staticmethod
    def decodeToken(classConstruct: type["PayLoad"], token: str) -> "PayLoad":
        data: dict[str, str] = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return classConstruct.from_json(classConstruct, **data)  # type: ignore

    @staticmethod
    async def adecodeToken(classConstruct: type["PayLoad"], token: str) -> "PayLoad":
        data: dict[str, str] = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        return await classConstruct.afrom_json(classConstruct, **data)  # type: ignore


class AccessPayLoad(PayLoad):
    __type: str = "access"
    expire_minutes = settings.JWT_EXP_DELTA_MINUTES

    def __init__(
        self,
        user: User,
        expire: datetime.datetime | None = None,
        type: str | None = None,
    ):
        self.username: str = user.username
        self.userID: int = user.id
        self.type = type if (type is not None) else self.__type
        self.expire = expire if (expire is not None) else timezone.now()


class RefreshPayLoad(PayLoad):
    __type: str = "refresh"
    expire_minutes = settings.REFRESH_EXP_DELTA_MINUTES

    def __init__(
        self,
        user: User,
        expire: datetime.datetime | None = None,
        type: str | None = None,
    ):
        self.username: str = user.username
        self.userID: int = user.id
        self.type = type if (type is not None) else self.__type
        self.expire = expire if (expire is not None) else timezone.now()


class JwtToken(typing.TypedDict):
    access: str
    refresh: str


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
    key: NullStr


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
    university: NullStr
    institute: NullStr
    branch: NullStr

class CredResponse(TokenResponse):
    pass


class DeleteResponse(TokenResponse):
    pass


class OtpResponse(TokenResponse):
    pass

class HeadingResponse(TokenResponse):
    university: NullStr
    institute: NullStr
    branch: NullStr