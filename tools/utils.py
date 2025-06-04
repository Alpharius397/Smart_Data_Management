from typing import Iterator, TypedDict, Any, NamedTuple  # type: ignore
from tools.get_image import compress_image, expand_image
from tools.errors import IncorrectDataFormat
from constants.constants import WRONG_IMAGE, WRONG_PERSONAL, WRONG_SEM


############ TYPES ############
class ReportStructure(NamedTuple):
    personal_info: dict[str, str]
    image_info: dict[str, str]
    semester_info: dict[int, dict[str, tuple[str, ...]]]


class branchSubjects(TypedDict):
    name: str
    semester: int


class ColumnType(NamedTuple):
    images: list[str]
    personal: list[str]
    semester: list[str]

    def __iter__(self) -> Iterator[list[str]]:
        yield self.images
        yield self.personal
        yield self.semester


############ UTILS ############
def personalAnnotate(column: str) -> str:
    return f"{column}PP"


def imageAnnotate(column: str):
    return f"{column}II"


def semesterAnnotate(column: str, index: int):  # you have 15 semester max {1, 15}
    return f"{column}S{index.to_bytes().hex().lstrip('0')}"


def processSubjects(
    branchSubs: Iterator[branchSubjects | dict[str, Any]],
    columns: list[str],
    image_idx: list[int],
) -> dict[str, str]:
    mapping: dict[str, str] = {i: i for i in columns}

    for idx in image_idx:  # add I to identify column containing image
        mapping[columns[idx]] = imageAnnotate(columns[idx])

    for sub in branchSubs:  # add S and sem number (hex) to identify Semester Info
        name: str = sub["name"]
        sem: int = sub["semester"]

        if not (name and sem):
            continue

        if name in mapping:
            mapping[name] = semesterAnnotate(name, sem)

    for key, value in mapping.items():
        if key == value:
            mapping[key] = personalAnnotate(value)

    return mapping


def deconstructSubjects(data: dict[str, str | list[str]], expand_images: bool = False):
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
    personal: list[str] = []
    sem: list[str] = []

    for column in columns:
        _column = column

        if (column[-2:]) == "PP":
            personal.append(_column)

        elif (column[-2:]) == "II":
            image.append(_column)

        elif (column[-2]) == "S":
            _ = column[-1].encode().hex()  # hex check
            sem.append(_column)

        else:
            print(column)
            raise IncorrectDataFormat()

    return ColumnType(image, personal, sem)
