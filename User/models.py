from enum import Enum
from PIL import Image
from django.contrib.auth.models import User as _User  # type: ignore
from django.db.models import (  # type: ignore
    OneToOneField,
    ForeignKey,
    Model,
    RESTRICT,
    CharField,
    ImageField,
    AutoField,
)
from django.http import HttpRequest  # type: ignore
from University.models import Branch, University, Institute
from constants import EMAIL_KEY
from tools.typesCauseWhyNot import NullStr, NullInt
from typing import Iterator, TypedDict


############ TYPES ############
class PostNameDict(TypedDict):
    university: NullStr
    institute: NullStr
    branch: NullStr


class PostIdDict(TypedDict):
    university: NullInt
    institute: NullInt
    branch: NullInt


############ UTILS ############
class RoleType(Enum):
    UNKNOWN = "Unknown"
    STUDENT = "Student"
    MANAGER = "Manager"
    ADMIN = "Admin"

    @staticmethod
    def getRole() -> Iterator[tuple[str, str]]:
        yield (RoleType.STUDENT.value, RoleType.STUDENT.value)
        yield (RoleType.MANAGER.value, RoleType.MANAGER.value)
        yield (RoleType.ADMIN.value, RoleType.ADMIN.value)

    @staticmethod
    def isStudent(roleID: str) -> bool:
        return RoleType.STUDENT.value == roleID

    @staticmethod
    def isManager(roleID: str) -> bool:
        return RoleType.MANAGER.value == roleID

    @staticmethod
    def isAdmin(roleID: str) -> bool:
        return RoleType.ADMIN.value == roleID


############ MODEL ############
class User(_User):
    """Custom User Proxy"""

    id: int
    role: "Role"
    email: str  # type: ignore
    username: str  # type: ignore

    class Meta:
        proxy = True


class Role(Model):
    id = AutoField(verbose_name="roleID", primary_key=True, null=False, blank=True)

    user = OneToOneField(to=User, on_delete=RESTRICT, related_name="role")  # type: ignore

    role = CharField(  # type: ignore
        verbose_name="Role ID",
        max_length=10,
        choices=list(RoleType.getRole()),
        default=RoleType.UNKNOWN.value,
        blank=False,
    )

    belongs = ForeignKey(  # type: ignore
        to=Branch, null=False, blank=False, on_delete=RESTRICT
    )

    def __str__(self):
        return f"{self.user} - {self.role}"


############ TOOLS ############
def is_manager(user: User) -> bool:
    try:
        return RoleType.isManager(user.role.role)
    except:
        return False


def is_student(user: User) -> bool:
    try:
        return RoleType.isStudent(user.role.role)
    except:
        return False


def is_admin(user: User) -> bool:
    try:
        return RoleType.isAdmin(user.role.role)
    except:
        return False


def get_user_by_id(id: int) -> NullStr:
    try:
        user = User.objects.get(id=id)
        return user.username
    except User.DoesNotExist:
        return None


def get_user_id(name: str) -> NullInt:
    try:
        user: User = User.objects.get(username=name)
        return user.id
    except User.DoesNotExist:
        return None


def get_post(user: User) -> PostNameDict:
    university, institute, branch = None, None, None
    try:
        role: Role = user.role

        bra = role.belongs
        insti = bra.institute
        uni = insti.university

        university = uni.name
        institute = uni.name
        branch = uni.name

    except:
        pass

    return PostNameDict(
        **{"university": university, "institute": institute, "branch": branch}
    )


def get_user(req: HttpRequest) -> User:
    return req.user  # type: ignore


def get_post_id(user: User) -> PostIdDict:
    university, institute, branch = None, None, None
    try:
        role: Role = user.role

        bra = role.belongs
        insti = bra.institute
        uni = insti.university

        university = uni.id
        institute = uni.id
        branch = uni.id

    except:
        pass

    return PostIdDict(
        **{"university": university, "institute": institute, "branch": branch}
    )


def is_authenticated(user: User) -> bool:
    return bool((user.is_authenticated) and (is_admin(user) or is_manager(user)))


def is_authenticated_student(user: User) -> bool:
    return bool((user.is_authenticated) and (is_student(user)))


def getID(user: User) -> int:
    return user.id


def get_admin_by_name(username: str) -> list[int]:
    return list(
        map(
            getID,
            User.objects.filter(username__icontains=username, role__role=RoleType.ADMIN)
            .order_by("username")
            .only("id"),
        )
    )


def get_manager_by_name(username: str) -> list[int]:
    return list(
        map(
            getID,
            User.objects.filter(
                username__icontains=username, role__role=RoleType.MANAGER
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
    except Exception:
        pass

    return PostNameDict(**{"university": uni, "institute": insti, "branch": bra})
