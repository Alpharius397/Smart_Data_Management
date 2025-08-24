from functools import wraps
from typing import (
    Callable,
    Iterator,
    ParamSpec,
    TypeVar,
    TypedDict,
    Literal,
    NamedTuple,
    Any,
)
import typing
from django.http import HttpRequest, QueryDict  # type: ignore
from tools.errors import IncorrectDataFormat


############ TYPES ############
class SpecialHttpRequest(HttpRequest):
    PUT: QueryDict | dict[str, Any]
    DELETE: QueryDict | dict[str, Any]


class ReportStructure(NamedTuple):
    personal_info: dict[str, str]
    image_info: dict[str, str]
    semester_info: dict[int, dict[str, tuple[str, ...]]]


class branchSubjects(TypedDict):
    name: str
    semester: int


class ColumnType(NamedTuple):
    images: list[str]
    text: list[str]

    def __iter__(self) -> Iterator[list[str]]:
        yield self.images
        yield self.text


############ UTILS ############
def get_2_value(value: Literal["true", "false"]) -> bool:
    assert value in [
        "true",
        "false",
    ], f"Invalid Boolean Type. Value '{value}' not in ['true', 'false']"

    if value == "true":
        return True
    else:
        return False


def get_3_value(value: Literal["true", "false", "none"]) -> bool | None:
    assert value in [
        "true",
        "false",
        "none",
    ], f"Invalid Nullable Boolean Type. Value '{value}' not in ['true', 'false', 'none']"

    if value == "true":
        return True
    elif value == "none":
        return None
    else:
        return False


def get_string_value(value: bool | None) -> Literal["true", "false", "none"]:
    assert (value is None) or (
        isinstance(value, bool)
    ), f"'value' should be of type bool or none. got: {type(value)}"

    match value:
        case True:
            return "true"
        case False:
            return "false"
        case None:
            return "none"


def textAnnotate(column: str) -> str:
    return f"{column}T"


def get_SQL_boolean(value: bool | None) -> Literal["true", "false", "null"]:
    assert (value is None) or (
        isinstance(value, bool)
    ), f"'value' should be of type bool or none. got: {type(value)}"

    match value:
        case True:
            return "true"
        case False:
            return "false"
        case None:
            return "null"


def imageAnnotate(column: str):
    return f"{column}I"


def processSubjects(
    columns: list[str],
    image_idx: list[int],
) -> dict[str, str]:
    mapping: dict[str, str] = {i: i for i in columns}

    for idx in image_idx:  # add I to identify column containing image
        mapping[columns[idx]] = imageAnnotate(columns[idx])

    for key, value in mapping.items():
        if key == value:
            mapping[key] = textAnnotate(value)

    return mapping


def segregateColumns(columns: list[str]) -> ColumnType:
    image: list[str] = []
    text: list[str] = []

    for column in columns:
        if (column[-1:]) == "T":
            text.append(column)

        elif (column[-1:]) == "I":
            image.append(column)

        else:
            raise IncorrectDataFormat()

    return ColumnType(image, text)


def setSwalAlert(
    context: dict[str, typing.Any] = {},
    text: str = "",
    icon: Literal["success", "error", "warning", "info"] = "error",
    title: str = "",
):
    if context:
        if "title" in context:
            context.update({"text": text, "icon": icon})
        else:
            context.update({"text": text, "icon": icon, "title": title})
        return {}
    else:
        return {"text": text, "icon": icon, "title": title}


P = ParamSpec("P")
T = TypeVar("T")


def tryCatchThis[T, **P](func: Callable[P, T], default: T) -> Callable[P, T]:
    @wraps(func)
    def inner(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return func(*args, **kwargs)
        except Exception:
            return default

    return inner
