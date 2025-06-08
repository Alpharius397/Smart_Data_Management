from django.db.models import ( # type: ignore
    CASCADE,
    CharField,
    RESTRICT,
    OneToOneField,
    ForeignKey,
    Model,
    IntegerField,
    AutoField,
    ImageField,
    DateTimeField,
    BooleanField,
    UniqueConstraint
)
from django.core.validators import MinValueValidator, RegexValidator, MaxValueValidator # type: ignore
from django.forms import forms # type: ignore
from django.utils import timezone # type: ignore
from django.db.models.manager import BaseManager # type: ignore

ColorRegex = RegexValidator(r"^#[a-fA-F0-9]{6}$", message="Invalid Hex color")


class University(Model):
    id = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    
    name = CharField(
        max_length=200, null=False, blank=False, verbose_name="University Name", unique=True
    )  # type: ignore
    
    institute: "institute"

    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name


class Institute(Model):
    id = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    
    name = CharField(
        max_length=200, null=False, blank=False, verbose_name="Institute Name"
    )  # type: ignore
    
    university = ForeignKey(
        to=University,
        null=False,
        blank=False,
        related_name="institute",
        on_delete=RESTRICT,
    )  # type: ignore
    
    location = CharField(
        max_length=200, null=False, blank=False, verbose_name="Location"
    )  # type: ignore
    
    color: "color"
        
    class Meta:
        verbose_name = "Institute"
        verbose_name_plural = "Institutes"
        
        constraints = [
            UniqueConstraint(fields=["university", "name"], name="unique_institute_for_each_university"),
        ]

    def __str__(self):
        return f"{self.university}:{self.name}"


class Branch(Model):
    id = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    
    name = CharField(
        max_length=200, null=False, blank=False, verbose_name="Branch Name"
    )  # type: ignore
    
    institute = ForeignKey(
        to=Institute, null=False, on_delete=RESTRICT, related_name="branch"
    )  # type: ignore

    schema: "schema"
    
            
    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        
        constraints = [
            UniqueConstraint(fields=["institute", "name"], name="unique_branch_for_each_institute"),
        ]

    def __str__(self):
        return f"{self.institute}:{self.name}"

class Schema(Model):
    id = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)    
    
    name = CharField(max_length=200, null=False, unique=True, blank=False, verbose_name="Scheme Name")
    
    date = DateTimeField(default=timezone.now, verbose_name="Date of Creation")
    
    default = BooleanField(default=False, null=False, blank=True, verbose_name="Default Schema")
    
    branch = ForeignKey(
        to=Branch, null=True, blank=False, on_delete=RESTRICT, related_name="schema"
    )  # type: ignore
    
    subject: "subject"
    
    class Meta:
        verbose_name = "Schema"
        verbose_name_plural = "Schemas"
        
        constraints = [
            UniqueConstraint(fields=["branch", "name"], name="unique_schema_for_each_branch"),
        ]
        
    
class Subject(Model):
    id = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    
    name = CharField(
        max_length=200, null=False, blank=False, verbose_name="Subject Name"
    )  # type: ignore
    
    semester = IntegerField(
        verbose_name="Semester",
        validators=[MinValueValidator(1, "Semester cannot be negative or zero"), MaxValueValidator(15, "Semester cannot be more than 15")],
    )  # type: ignore
    
    schema = ForeignKey(
        to=Schema, null=True, blank=False, on_delete=RESTRICT, related_name="subject"
    )  # type: ignore

    marks = IntegerField(
        verbose_name="Max Marks",
        validators=[MinValueValidator(1, "Semester cannot be negative or zero")],
        null=False,
    )  # type: ignore

    grade: "grade"


    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        
        constraints = [
            UniqueConstraint(fields=["semester", "schema", "name"], name="unique_name_for_each_semester_and_schema"),
        ]

    def __str__(self):
        return f"{self.name} - {self.semester} - {self.schema}"

class Grade(Model):
    id = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    
    subject = ForeignKey(verbose_name="Subject", null=False, blank=False, to=Subject, on_delete=CASCADE, related_name="grade")
    
    grade = CharField(verbose_name="Grade", null=False, blank=False, max_length=2)
    
    minMarks = IntegerField(verbose_name="Min Marks Needed", null=False, blank=False, validators=[MinValueValidator(0, "Minimum marks cannot be negative")])
    
    
    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        
        constraints = [
            UniqueConstraint(fields=["subject", "minMarks", "grade"], name="unique_grades_and_minMarks_for_subject"),
        ]


class Color(Model):
    id = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    
    institute = OneToOneField(
        to=Institute, null=True, blank=False, related_name="color", on_delete=CASCADE
    )  # type: ignore
    
    main_color = CharField(
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
    
    icon = ImageField(verbose_name="Institute Icon", upload_to="icon", null=True)
    
    class Meta:
        verbose_name = "Color Theme"
        verbose_name_plural = "Color Themes"

    def __str__(self):
        return f"Color Theme: {self.institute.name}"

############ TYPES ############
type institute = BaseManager[Institute]
type branch = BaseManager[Branch]
type color = BaseManager[Color]
type schema = BaseManager[Schema]
type subject = BaseManager[Subject]
type grade = BaseManager[Grade]