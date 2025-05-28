from University.models import Subject
from Main.errors import MainException
from typing import Iterator, TypedDict, Any  # type: ignore

SEM_RE = r"(\w+)S(\d+)$"
PERSONAL_RE = r"(\w+)P$"
IMAGE_RE = r"(\w+)I$"

Subject.semester


def personalAnnotate(column: str) -> str:
    return f"{column}P"


def imageAnnotate(column: str):
    return f"{column}I"


def semesterAnnotate(column: str, index: int):
    return f"{column}S{index}"


class SubjectsNotDefined(MainException):
    """Exception if Subjects of the Branch are not defined"""

    def __init__(self, branchID: int) -> None:
        super().__init__(
            f"Subjects of the Branch with ID {
                branchID
            } are not defined. Please add the Subjects"
        )


class branchSubjects(TypedDict):
    name: str
    semester: int


def processSubjects(
    branchSubs: Iterator[branchSubjects | dict[str, Any]],
    columns: list[str],
    image_idx: list[int],
) -> dict[str, str]:
    mapping: dict[str, str] = {i: i for i in columns}

    for idx in image_idx:  # add I to identify column containing image
        mapping[columns[idx]] = imageAnnotate(columns[idx])

    for sub in branchSubs:
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
