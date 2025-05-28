from django.contrib.auth.models import User  # type: ignore
from django.db.models import (
    OneToOneField,
    ForeignKey,
    Model,
    RESTRICT,
    CASCADE,
    CharField,
    Choices,
)  # type: ignore
from University.models import Branch, University, Institute
from tools.typesCauseWhyNot import NullStr, NullInt
from typing import Iterator, TypedDict


class Admin(Model):
    pass


class Manager(Model):
    pass


class Student(Model):
    pass


class UserObject(User):
    pass


class RoleType:
    UNKNOWN: str = "Unknown"
    STUDENT: str = "Student"
    MANAGER: str = "Manager"
    ADMIN: str = "Admin"

    @staticmethod
    def getRole() -> Iterator[tuple[str, str]]:
        yield (RoleType.STUDENT, RoleType.STUDENT)
        yield (RoleType.MANAGER, RoleType.MANAGER)
        yield (RoleType.ADMIN, RoleType.ADMIN)

    @staticmethod
    def isStudent(roleID: str) -> bool:
        return RoleType.STUDENT == roleID

    @staticmethod
    def isManager(roleID: str) -> bool:
        return RoleType.MANAGER == roleID

    @staticmethod
    def isAdmin(roleID: str) -> bool:
        return RoleType.ADMIN == roleID


class PostNameDict(TypedDict):
    university: str
    institute: str
    branch: str


class PostIdDict(TypedDict):
    university: int
    institute: int
    branch: int


class Role(Model):
    user: "User" = OneToOneField(to=User, on_delete=RESTRICT, related_name="role")
    role: "str" = CharField(  # type: ignore
        verbose_name="Role ID",
        max_length=10,
        choices=list(RoleType.getRole()),
        default=RoleType.UNKNOWN,
    )
    belongs: "Branch" = ForeignKey(
        to=Branch, null=False, blank=False, on_delete=RESTRICT
    )  # type: ignore


class u_ser(User):
    id: int
    role: Role

    class Meta:
        proxy = True


type _User = u_ser


def is_manager(user: _User) -> bool:
    return RoleType.isManager(user.role.role)


def is_student(user: _User) -> bool:
    return RoleType.isStudent(user.role.role)


def is_admin(user: _User) -> bool:
    return RoleType.isAdmin(user.role.role)


def get_user_by_id(id: int) -> NullStr:
    try:
        user = _User.objects.get(id=id)
        return user.username
    except _User.DoesNotExist:
        return None


def get_user_id(name: str) -> NullInt:
    try:
        user: _User = _User.objects.get(username=name)
        return user.id
    except:
        return None


def get_post(user: _User) -> PostNameDict:
    role: Role = user.role

    branch = role.belongs
    insti = branch.institute
    uni = insti.university

    return PostNameDict(
        **{"university": uni.name, "institute": insti.name, "branch": branch.name}
    )


def get_post_id(user: _User) -> PostIdDict:
    role: Role = user.role

    branch = role.belongs
    insti = branch.institute
    uni = insti.university

    return PostIdDict(
        **{"university": uni.id, "institute": insti.id, "branch": branch.id}
    )


def is_authenticated(user: _User) -> bool:
    return bool((user.is_authenticated) and (is_admin(user) or is_manager(user)))


def getID(user: _User):
    return user.id


def get_admin_by_name(username: str) -> list[int]:
    return list(
        map(
            getID,
            _User.objects.filter(
                username__icontains=username, role__role=RoleType.ADMIN
            )
            .order_by("username")
            .only("id"),
        )
    )


def get_manager_by_name(username: str) -> list[int]:
    return list(
        map(
            getID,
            _User.objects.filter(
                username__icontains=username, role__role=RoleType.ADMIN
            )
            .order_by("username")
            .only("id"),
        )
    )


def get_post_by_ID(university: int, institute: int, branch: int) -> PostNameDict:
    uni: str = ""
    insti: str = ""
    bra: str = ""

    try:
        uni = University.objects.get(id=university).name
        insti = Institute.objects.get(id=institute).name
        bra = Branch.objects.get(id=branch).name
    except:
        pass

    return PostNameDict(**{"university": uni, "institute": insti, "branch": bra})
