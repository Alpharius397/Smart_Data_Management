from typing import Iterator, TypedDict, Any, NamedTuple  # type: ignore
from tools.get_image import compress_image, expand_image
from tools.errors import IncorrectDataFormat
from constants.constants import WRONG_IMAGE, WRONG_PERSONAL, WRONG_SEM
import re

############ CONSTANTS ############
SEM_RE = r"^(\w+)S(\d+)\Z"
PERSONAL_RE = r"^(\w+)P\Z"
IMAGE_RE = r"^(\w+)I\Z"


############ TYPES ############
class ReportStructure(NamedTuple):
    personal_info: dict[str, str]
    image_info: dict[str, str]
    semester_info: dict[int, dict[str, tuple[str, ...]]]


class branchSubjects(TypedDict):
    name: str
    semester: int


############ UTILS ############
def personalAnnotate(column: str) -> str:
    return f"{column}P"


def imageAnnotate(column: str):
    return f"{column}I"


def semesterAnnotate(column: str, index: int):
    return f"{column}S{index}"


def processSubjects(
    branchSubs: Iterator[branchSubjects | dict[str, Any]],
    columns: list[str],
    image_idx: list[int],
) -> dict[str, str]:
    mapping: dict[str, str] = {i: i for i in columns}

    for idx in image_idx:  # add I to identify column containing image
        mapping[columns[idx]] = imageAnnotate(columns[idx])

    for sub in branchSubs:  # add S and sem number to identify Semester Info
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
        _column: str = ""

        if mo := re.match(PERSONAL_RE, column):
            _column = mo.group(1)

            assert isinstance(value, str), WRONG_PERSONAL
            personal_info[_column] = value

        elif mo := re.match(IMAGE_RE, column):
            _column = mo.group(1)

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

        elif mo := re.match(SEM_RE, column):
            _column = mo.group(1)
            _sem = int(mo.group(2))

            assert (
                isinstance(value, list) and len(value) > 1 and len(value) < 4
            ), WRONG_SEM

            semester_info[_sem][_column] = tuple(value)

        else:
            raise IncorrectDataFormat()

    return ReportStructure(personal_info, image_info, semester_info)
