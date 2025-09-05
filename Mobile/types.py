from typing import TypedDict
from tools.types import NullStr
from User.models import User
import datetime
from django.utils import timezone  # type: ignore
import jwt
import json
from Main.settings import settingsInterface as settings

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
        self.expire = expire if (expire is not None) else (timezone.now() + datetime.timedelta(minutes=self.expire_minutes))

    def to_json(self) -> dict[str, str | int]:
        return {
            "userID": self.userID,
            "username": self.username,
            "type": self.type,
            "expire": self.expire.isoformat(),
        }

    def getToken(self):
        return jwt.encode(
                self.to_json(), settings.JWT_SECRET, settings.JWT_ALGORITHM
            )

    def isCorrectType(self) -> bool:
        return self.type == self.__type

    def __str__(self):
        return json.dumps(
            {
                "userID": self.userID,
                "username": self.username,
                "type": self.type,
                "expire": self.expire.isoformat(),
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
        self.expire = expire if (expire is not None) else (timezone.now() + datetime.timedelta(minutes=self.expire_minutes))


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
        self.expire = expire if (expire is not None) else (timezone.now() + datetime.timedelta(minutes=self.expire_minutes))


class MobileResponse(TypedDict):
    status: bool
    error: list[str]


class LoginResponse(MobileResponse):
    access: NullStr
    refresh: NullStr

class TokenResponse(MobileResponse):
    access: NullStr

class RefreshResponse(MobileResponse):
    access: NullStr
    refresh: NullStr
    
class RegisterResponse(MobileResponse):
    pass


class SubscriberResponse(MobileResponse):
    key: NullStr
    decryptionKey: NullStr


class CardData(TypedDict):
    cardID: str
    timestamp: str
    university: str
    institute: str
    branch: str


class CardResponse(MobileResponse):
    cards: list[CardData]
    nextPage: int


class UserInfoResponse(MobileResponse):
    username: NullStr
    email: NullStr
    university: NullStr
    institute: NullStr
    branch: NullStr

class CredResponse(MobileResponse):
    pass


class DeleteResponse(MobileResponse):
    pass


class OtpResponse(MobileResponse):
    pass

class HeadingResponse(MobileResponse):
    university: NullStr
    institute: NullStr
    branch: NullStr