from django.db.models import (
    CASCADE,
    CharField,
    RESTRICT,
    OneToOneField,
    ForeignKey,
    Model,
    IntegerField,
    AutoField,
)  # type: ignore
from django.core.validators import MinValueValidator, RegexValidator  # type: ignore

ColorRegex = RegexValidator(r"^#[a-fA-F0-9]{6}$", message="Invalid Hex color")


class University(Model):
    id: int = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    name: str = CharField(
        max_length=200, null=False, blank=False, verbose_name="University Name"
    )  # type: ignore
    institute: "Institute"

    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name


class Institute(Model):
    id: int = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    name: str = CharField(
        max_length=200, null=False, blank=False, verbose_name="Institute Name"
    )  # type: ignore
    university: "University" = ForeignKey(
        to=University,
        null=False,
        blank=False,
        related_name="institute",
        on_delete=RESTRICT,
    )  # type: ignore
    location: str = CharField(
        max_length=200, null=False, blank=False, verbose_name="Location"
    )  # type: ignore
    color: "Color"

    class Meta:
        verbose_name = "Institute"
        verbose_name_plural = "Institutes"

    def __str__(self):
        return f"{self.university}:{self.name}"


class Branch(Model):
    id: int = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    name: str = CharField(
        max_length=200, null=False, blank=False, verbose_name="Branch Name"
    )  # type: ignore
    institute: "Institute" = ForeignKey(
        to=Institute, null=False, on_delete=RESTRICT, related_name="branch"
    )  # type: ignore

    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"

    def __str__(self):
        return f"{self.institute}:{self.name}"


class Subject(Model):
    id: int = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    name: str = CharField(
        max_length=200, null=False, blank=False, verbose_name="Subject Name"
    )  # type: ignore
    semester: int = IntegerField(
        verbose_name="Semester",
        validators=[MinValueValidator(1, "Semester cannot be negative or zero")],
    )  # type: ignore
    branch: "Branch" = ForeignKey(
        to=Branch, null=True, blank=False, on_delete=RESTRICT, related_name="subject"
    )  # type: ignore

    marks: int = IntegerField(
        verbose_name="Max Marks",
        validators=[MinValueValidator(1, "Semester cannot be negative or zero")],
    )  # type: ignore

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self):
        return f"{self.name} - {self.semester} - {self.branch}"


class Color(Model):
    id: int = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    institute: "Institute" = OneToOneField(
        to=Institute, null=True, blank=False, related_name="color", on_delete=CASCADE
    )  # type: ignore
    main_color: str = CharField(
        max_length=7,
        null=False,
        blank=False,
        verbose_name="Main Color",
        validators=[ColorRegex],
    )  # type: ignore
    sec_color: str = CharField(
        max_length=7,
        null=False,
        blank=False,
        verbose_name="Secondary Color",
        validators=[ColorRegex],
    )  # type: ignore

    class Meta:
        verbose_name = "Color Theme"
        verbose_name_plural = "Color Themes"

    def __str__(self):
        return f"Color Theme: {self.institute.name}"
