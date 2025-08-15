from typing import TypedDict, Literal, NamedTuple

from Report.views import SubjectProto


class FetchJson(TypedDict):
    data: str


class ReadJson(TypedDict):
    message: str
    status: Literal["true", "false", "none"]
    card: str
    data: str


class ConfirmJson(TypedDict):
    message: str
    status: Literal["true", "false", "none"]
    card: str


class SubjectMeta(TypedDict):
    sem: int
    marks: int


class SemMeta(NamedTuple):
    marks: int
    total: int


class CardReport(TypedDict):
    images: dict[str, str]
    personal: dict[str, str]
    sem_data: dict[int, dict[str, SubjectProto]]

    columns: dict[int, set[str]]

    university_icon: str
    institute_icon: str
    university_heading: str
    institute_heading: str
    branch_heading: str
