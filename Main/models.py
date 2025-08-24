from typing import ParamSpec, TypedDict
from Main.settings import settingsInterface as settings
from Logs.loggers import REDIS_LOG
import redis
import redis.asyncio as aRedis
import json
from enum import Enum


P = ParamSpec("P")


class BaseDict(TypedDict):
    pass


type TypedDictType = type[BaseDict]


class RedisDataBase(Enum):
    """
    Base Idea:

        USER_TOKEN = Stores all user related token
        GOLANG_TOKEN = Store golang-exe assigned token
        OTP_TOKEN = Store otp-token
        EMAIL_TOKEN = Store forgot-password token
        CARD_READ_TOKEN = Store card read token
        CARD_WRITE_TOKEN = Store card write token

        Adv:
            1) Token Sharing
            2) Auto-Refresh Token
            3) Cross-platform
            4) Separation of Concern
            5) Immediate Resource removal on changes
        Disadvantages:
            1) Redis Overuse
    """

    USER_TOKEN = 2  # store user-assigned token
    OTP_TOKEN = 3  # store otp-token
    EMAIL_TOKEN = 4  # store forgot-password token
    CARD_READ_TOKEN = 5  #  store card read token
    CARD_WRITE_TOKEN = 6  #  store card write token
    PDF_TOKEN = 7  #  store pdf generate token


class WriteToken(TypedDict):
    ID: int
    key: str


class PdfToken(TypedDict):
    ID: int


class ReadToken(TypedDict):
    ID: int
    data: str


class RedisConnection:
    MAX_DURATION: int = 3
    """ Default expiry duration in `minutes` """

    log = REDIS_LOG

    @staticmethod
    def get_secs_from_minutes(minutes: int) -> int:
        return minutes * 60

    def __init__(self, dataBase: RedisDataBase) -> None:
        self.r: redis.Redis | None = None
        self.db = dataBase

    def connect(self) -> "RedisConnection":
        try:
            self.r = redis.Redis(
                **settings.REDIS, decode_responses=True, db=self.db.value
            )
            self.log.write_info(f"Connecting to Redis Database {self.db.name}")
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return self

    def getText(self, key: str) -> str:
        if self.r is None:
            return ""

        try:
            value = self.r.get(key)

            assert isinstance(
                value, str
            ), f"For key {key}: Value must be string. Got {type(value)}"

            self.log.write_info(f"Fetching Key: {key} in Database: {self.db.name}")
            return value

        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return ""

    def getDict(self, key: str) -> dict:
        if self.r is None:
            return {}

        try:
            value = self.r.get(key)

            assert isinstance(
                value, str
            ), f"For key {key}: Value must be string. Got {type(value)}"

            self.log.write_info(f"Fetching Key: {key} in Database: {self.db.name}")
            return json.loads(value)

        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return {}

    def setDict(
        self,
        key: str,
        value: dict | TypedDictType,
        duration: int = 0,
        set_once: bool = False,
    ) -> bool:
        duration = RedisConnection.MAX_DURATION if (duration >= 0) else duration

        if self.r is None:
            return False

        try:
            jsonText = json.dumps(value)
            self.r.set(
                key,
                jsonText,
                ex=RedisConnection.get_secs_from_minutes(duration),
                nx=set_once,
            )
            self.log.write_info(
                f"Setting Key: {key}, with Value: {jsonText} for duration {RedisConnection.get_secs_from_minutes(duration)} seconds in Database: {self.db.name}"
            )
            return True
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        return False

    def setText(
        self, key: str, value: str, duration: int = 0, set_once: bool = False
    ) -> bool:
        duration = RedisConnection.MAX_DURATION if (duration >= 0) else duration

        if self.r is None:
            return False

        try:
            jsonText = value
            self.r.set(
                key,
                jsonText,
                ex=RedisConnection.get_secs_from_minutes(duration),
                nx=set_once,
            )
            self.log.write_info(
                f"Setting Key: {key}, with Value: {jsonText} for duration {RedisConnection.get_secs_from_minutes(duration)} seconds in Database: {self.db.name}"
            )
            return True

        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        return False

    def unset(self, key: str) -> bool:
        if self.r is None:
            return False

        try:
            self.r.unlink(key)
            self.log.write_info(f"Unsetting Key: {key} in Database: {self.db.name}")
            return True
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return False

    def close(self) -> bool:
        if self.r is None:
            return False

        try:
            self.r.close()
            self.log.write_info(
                f"Closing Redis connection for Database: {self.db.name}"
            )
            return True
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return False

    def exists(self, key: str) -> bool:
        if self.r is None:
            return False

        try:
            a = bool(self.r.exists(key))
            self.log.write_error(
                f"Checking Database: {self.db.name} for key: '{key}'. Found it: {a}"
            )
            return a
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return False

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class AsyncRedisConnection:
    MAX_DURATION: int = 3
    """ Default expiry duration in `minutes` """

    log = REDIS_LOG

    @staticmethod
    def get_secs_from_minutes(minutes: int) -> int:
        return minutes * 60

    def __init__(self, dataBase: RedisDataBase) -> None:
        self.r: aRedis.Redis | None = None
        self.db = dataBase

    async def connect(self) -> "AsyncRedisConnection":
        try:
            self.r = await aRedis.Redis(
                **settings.REDIS, decode_responses=True, db=self.db.value
            )

            self.log.write_info(f"Connecting to Redis Database {self.db.name}")
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return self

    async def getText(self, key: str) -> str:
        if self.r is None:
            return ""

        try:
            value = await self.r.get(key)

            assert isinstance(value, str), f"Value must be string. Got {type(value)}"

            self.log.write_info(f"Fetching Key: {key} in Database: {self.db.name}")
            return value

        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return ""

    async def getDict(self, key: str) -> dict:
        if self.r is None:
            return {}

        try:
            value = await self.r.get(key)

            assert isinstance(value, str), f"Value must be string. Got {type(value)}"

            self.log.write_info(f"Fetching Key: {key} in Database: {self.db.name}")
            return json.loads(value)

        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return {}

    async def setDict(
        self, key: str, value: dict | TypedDictType, duration: int = 0
    ) -> bool:
        duration = RedisConnection.MAX_DURATION if (duration >= 0) else duration

        if self.r is None:
            return False

        try:
            jsonText = json.dumps(value)
            await self.r.set(
                key, jsonText, ex=RedisConnection.get_secs_from_minutes(duration)
            )
            self.log.write_info(
                f"Setting Key: {key}, with Value: {jsonText} for duration {RedisConnection.get_secs_from_minutes(duration)} seconds in Database: {self.db.name}"
            )
            return True
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        return False

    async def setText(self, key: str, value: str, duration: int = 0) -> bool:
        duration = RedisConnection.MAX_DURATION if (duration >= 0) else duration

        if self.r is None:
            return False

        try:
            jsonText = value
            await self.r.set(
                key, jsonText, ex=RedisConnection.get_secs_from_minutes(duration)
            )
            self.log.write_info(
                f"Setting Key: {key}, with Value: {jsonText} for duration {RedisConnection.get_secs_from_minutes(duration)} seconds in Database: {self.db.name}"
            )
            return True

        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))
        return False

    async def unset(self, key: str) -> bool:
        if self.r is None:
            return False

        try:
            await self.r.unlink(key)
            self.log.write_info(f"Unsetting Key: {key} in Database: {self.db.name}")
            return True
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return False

    async def close(self) -> bool:
        if self.r is None:
            return False

        try:
            await self.r.close()
            self.log.write_info(
                f"Closing Redis connection for Database: {self.db.name}"
            )
            return True
        except Exception as e:
            self.log.write_error(self.log.get_error_info(e))

        return False

    async def __aenter__(self):
        return await self.connect()

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()
