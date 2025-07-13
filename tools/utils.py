from typing import Iterator, TypedDict, Literal, NamedTuple, Any
import typing  
from tools.get_image import compress_image, expand_image
from tools.errors import IncorrectDataFormat
from django.http import HttpRequest as __HttpRequest, QueryDict # type: ignore
from constants.constants import WRONG_IMAGE, WRONG_PERSONAL, WRONG_SEM


############ TYPES ############
class HttpRequest(__HttpRequest):
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
def get_2_value(value: Literal['true', 'false']) -> bool:
    assert value in [
        "true",
        "false",
    ], f"Invalid Boolean Type. Value '{value}' not in ['true', 'false']"

    if value == "true":
        return True
    else:
        return False

def get_3_value(value: Literal['true', 'false', 'none']) -> bool | None:
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

def get_string_value(value: bool | None) -> Literal['true', 'false', 'none']:
    match(value):
        case True: return 'true'
        case False: return 'false'
        case None: return 'none'
        case _: raise ValueError(f"'value' should be of type bool or None. Got: {type(value)}")

def textAnnotate(column: str) -> str:
    return f"{column}T"

def get_SQL_boolean(value: bool | None) -> Literal['true', 'false', 'null']:
    match(value):
        case True: return 'true'
        case False: return 'false'
        case None: return 'null'
        case _: raise ValueError(f"'value' should be of type bool or None. Got: {type(value)}")

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


def deconstructSubjects(data: dict[str, str | list[str]], expand_images: bool = False):
    """ Get subjects details from card """
    
    personal_info: dict[str, str] = {}
    image_info: dict[str, str] = {}
    semester_info: dict[int, dict[str, tuple[str, ...]]] = {}

    for column, value in data.items():
        _column: str = column

        if (column[-2:]) == "PP":
            assert isinstance(value, str), WRONG_PERSONAL
            personal_info[_column] = value

        elif (column[-2:]) == "II":
            assert isinstance(value, str), WRONG_IMAGE

            images = value.split(":")

            assert len(images) == 3, WRONG_IMAGE

            width, height, img = images

            assert width.isnumeric() and height.isnumeric(), WRONG_IMAGE

            img = (
                expand_image(img, int(width), int(height))
                if expand_images
                else compress_image(img)
            )

            image_info[_column] = img

        elif (column[-2]) == "S":
            _sem = int(column[-1], 16)  # hex conversion

            assert (
                isinstance(value, list) and len(value) > 1 and len(value) < 4
            ), WRONG_SEM

            semester_info[_sem][_column] = tuple(value)

        else:
            raise IncorrectDataFormat()

    return ReportStructure(personal_info, image_info, semester_info)


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

def setSwalAlert(context: dict[str, typing.Any] = {}, text: str = '', icon: Literal['success', 'error', 'warning','info'] = 'error', title: str = ''):
    
    if context:
        if ("title" in context):
            context.update({"text": text, "icon": icon})
        else:
            context.update({"text": text, "icon": icon, "title": title})
        return {}
    else:
        return {"text": text, "icon": icon, "title": title}