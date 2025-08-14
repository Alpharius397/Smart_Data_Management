from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Header(_message.Message):
    __slots__ = ("university", "institute", "branch", "schema")
    UNIVERSITY_FIELD_NUMBER: _ClassVar[int]
    INSTITUTE_FIELD_NUMBER: _ClassVar[int]
    BRANCH_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_FIELD_NUMBER: _ClassVar[int]
    university: int
    institute: int
    branch: int
    schema: int
    def __init__(self, university: _Optional[int] = ..., institute: _Optional[int] = ..., branch: _Optional[int] = ..., schema: _Optional[int] = ...) -> None: ...

class Meta(_message.Message):
    __slots__ = ("id", "total", "other")
    class OtherEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FIELD_NUMBER: _ClassVar[int]
    OTHER_FIELD_NUMBER: _ClassVar[int]
    id: str
    total: int
    other: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., total: _Optional[int] = ..., other: _Optional[_Mapping[str, str]] = ...) -> None: ...

class Subject(_message.Message):
    __slots__ = ("subject",)
    class SubjectEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: Meta
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[Meta, _Mapping]] = ...) -> None: ...
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    subject: _containers.MessageMap[str, Meta]
    def __init__(self, subject: _Optional[_Mapping[str, Meta]] = ...) -> None: ...

class CardData(_message.Message):
    __slots__ = ("header", "semester", "personal", "image")
    class SemesterEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: int
        value: Subject
        def __init__(self, key: _Optional[int] = ..., value: _Optional[_Union[Subject, _Mapping]] = ...) -> None: ...
    class PersonalEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class ImageEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bytes
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...
    HEADER_FIELD_NUMBER: _ClassVar[int]
    SEMESTER_FIELD_NUMBER: _ClassVar[int]
    PERSONAL_FIELD_NUMBER: _ClassVar[int]
    IMAGE_FIELD_NUMBER: _ClassVar[int]
    header: Header
    semester: _containers.MessageMap[int, Subject]
    personal: _containers.ScalarMap[str, str]
    image: _containers.ScalarMap[str, bytes]
    def __init__(self, header: _Optional[_Union[Header, _Mapping]] = ..., semester: _Optional[_Mapping[int, Subject]] = ..., personal: _Optional[_Mapping[str, str]] = ..., image: _Optional[_Mapping[str, bytes]] = ...) -> None: ...
