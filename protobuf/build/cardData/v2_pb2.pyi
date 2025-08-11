from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Header(_message.Message):
    __slots__ = ("university", "institute", "branch")
    UNIVERSITY_FIELD_NUMBER: _ClassVar[int]
    INSTITUTE_FIELD_NUMBER: _ClassVar[int]
    BRANCH_FIELD_NUMBER: _ClassVar[int]
    university: str
    institute: str
    branch: str
    def __init__(self, university: _Optional[str] = ..., institute: _Optional[str] = ..., branch: _Optional[str] = ...) -> None: ...

class Subject(_message.Message):
    __slots__ = ("row",)
    ROW_FIELD_NUMBER: _ClassVar[int]
    row: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, row: _Optional[_Iterable[str]] = ...) -> None: ...

class Semester(_message.Message):
    __slots__ = ("semester",)
    class SemesterEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Subject
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Subject, _Mapping]] = ...) -> None: ...
    SEMESTER_FIELD_NUMBER: _ClassVar[int]
    semester: _containers.MessageMap[str, Subject]
    def __init__(self, semester: _Optional[_Mapping[str, Subject]] = ...) -> None: ...

class Personal(_message.Message):
    __slots__ = ("personal",)
    class PersonalEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PERSONAL_FIELD_NUMBER: _ClassVar[int]
    personal: _containers.ScalarMap[str, str]
    def __init__(self, personal: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Image(_message.Message):
    __slots__ = ("image",)
    class ImageEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bytes
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    image: _containers.ScalarMap[str, bytes]
    def __init__(self, image: _Optional[_Mapping[str, bytes]] = ...) -> None: ...

class CardData(_message.Message):
    __slots__ = ("header", "semester", "personal", "image")
    HEADER_FIELD_NUMBER: _ClassVar[int]
    SEMESTER_FIELD_NUMBER: _ClassVar[int]
    PERSONAL_FIELD_NUMBER: _ClassVar[int]
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    header: Header
    semester: Semester
    personal: Personal
    image: Image
    def __init__(self, header: _Optional[_Union[Header, _Mapping]] = ..., semester: _Optional[_Union[Semester, _Mapping]] = ..., personal: _Optional[_Union[Personal, _Mapping]] = ..., image: _Optional[_Union[Image, _Mapping]] = ...) -> None: ...
