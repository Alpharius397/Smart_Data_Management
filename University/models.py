from typing import NamedTuple, TypedDict
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
    UniqueConstraint,
)
from django.db.models.fields.files import ImageFieldFile # type: ignore
from django.core.validators import MinValueValidator, RegexValidator, MaxValueValidator # type: ignore
from django.utils import timezone # type: ignore

ColorRegex = RegexValidator(r"^#[a-fA-F0-9]{6}$", message="Invalid Hex color")

class University(Model):
    id = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    
    name = CharField(
        max_length=200, null=False, blank=False, verbose_name="University Name", unique=True
    )  # type: ignore
    
    institute: "Institute"

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
    
    color: "Color"
        
    class Meta:
        verbose_name = "Institute"
        verbose_name_plural = "Institutes"
        
        constraints = [
            UniqueConstraint(fields=["university", "name"], name="unique_institute_for_each_university"),
        ]

    def __str__(self):
        return f"{self.name}"


class Branch(Model):
    id = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    
    name = CharField(
        max_length=200, null=False, blank=False, verbose_name="Branch Name"
    )  # type: ignore
    
    institute = ForeignKey(
        to=Institute, null=False, on_delete=RESTRICT, related_name="branch"
    )  # type: ignore

    schema: "Schema"
    
            
    class Meta:
        verbose_name = "Branch"
        verbose_name_plural = "Branches"
        
        constraints = [
            UniqueConstraint(fields=["institute", "name"], name="unique_branch_for_each_institute"),
        ]

    def __str__(self):
        return f"{self.name}"

class Schema(Model):
    id = AutoField(verbose_name="id", null=False, blank=True, primary_key=True)    
    
    name = CharField(max_length=200, null=False, unique=True, blank=False, verbose_name="Scheme Name")
    
    date = DateTimeField(default=timezone.now, verbose_name="Date of Creation")
    
    branch = ForeignKey(
        to=Branch, null=False, blank=False, on_delete=RESTRICT, related_name="schema"
    )  # type: ignore
    
    subject: "Subject"
    
    universityHeading = CharField(max_length=200, null=False, blank=False, verbose_name="University Heading", default="University Heading")
    instituteHeading = CharField(max_length=200, null=False, blank=False, verbose_name="Institute Heading", default="Institute Heading")
    branchHeading = CharField(max_length=200, null=False, blank=False, verbose_name="Branch Heading", default="Branch Heading")
    
    universityIcon = ImageField(verbose_name="University Icon", upload_to="schema/university", null=True, default='schema/university/default.icon.png')
    instituteIcon = ImageField(verbose_name="Institute Icon", upload_to="schema/institute", null=True, default="schema/institute/default.icon.jpeg")
    
    class Meta:
        verbose_name = "Schema"
        verbose_name_plural = "Schemas"
        
        constraints = [
            UniqueConstraint(fields=["branch", "name"], name="unique_schema_for_each_branch"),
        ]
    
    @staticmethod
    def check_file(obj: "ImageFieldFile"):
        try:
            obj.file
            return True
        except:
            return False
    
    def save(self, *args, **kwargs):
        
        try:
            this = Schema.objects.get(id=self.id)

            if(Schema.check_file(this.universityIcon) and (this.universityIcon != self.universityIcon)):
                this.universityIcon.delete(False)
                    
            if(Schema.check_file(this.instituteIcon) and (this.instituteIcon != self.instituteIcon)):
                this.instituteIcon.delete(False)
    
        except Schema.DoesNotExist:
            pass
        
        except Exception as e:
            raise e
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.branch} - {self.name}"
    
    @staticmethod
    def getSchema(schema_id: int | str) -> 'SchemaMeta':
        icon = SchemaMeta(
            university_icon='/media/schema/university/default.icon.png', 
            institute_icon="/media/schema/institute/default.icon.jpeg", 
            university_heading="University Heading",
            institute_heading="Institute Heading",
            branch_heading="Branch Heading"
        )
        
        try:
            schema = Schema.objects.get(id=schema_id)
            icon["university_icon"] = schema.universityIcon.url
            icon["institute_icon"] = schema.instituteIcon.url
            icon["university_heading"] = schema.universityHeading
            icon["institute_heading"] = schema.instituteHeading
            icon["branch_heading"] = schema.branchHeading
        except Exception as e:
            pass
            
        return icon
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

    class Meta:
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"
        
        constraints = [
            UniqueConstraint(fields=["semester", "schema", "name"], name="unique_name_for_each_semester_and_schema"),
        ]
        
    def __str__(self):
        return f"{self.name} - {self.semester} - {self.schema}"
    
    @staticmethod
    def getSubjects(schema_id: int, branch_id: int):
        
        sem_dict: dict[str, SubjectMeta] = {} # semester wise subjects with max marks
        
        try:
            
            subjects = Subject.objects.filter(schema__id=schema_id, schema__branch__id=branch_id).values("name", "semester", "marks")
                
            for subs in subjects.iterator():
                name = subs["name"]
                semester = subs["semester"]
                marks = subs["marks"]
                    
                sem_dict[name] = SubjectMeta(sem=semester, marks=marks)
                
        except Exception as e:
            pass
                    
        return sem_dict

class Color(Model):
    id = AutoField(verbose_name="id", null=False, blank=False, primary_key=True)  # type: ignore
    
    institute = OneToOneField(
        to=Institute, null=False, blank=False, related_name="color", on_delete=CASCADE
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
    
    instituteIcon = ImageField(verbose_name="Institute Icon", upload_to="icon", null=True)
    
    class Meta:
        verbose_name = "Color Theme"
        verbose_name_plural = "Color Themes"

    @staticmethod
    def check_file(obj: "ImageFieldFile"):
        try:
            obj.file
            return True
        except:
            return False
    
    def save(self, *args, **kwargs):
        
        try:
            this = Color.objects.get(id=self.id)

            if(Color.check_file(this.instituteIcon) and (this.instituteIcon != self.instituteIcon)):
                this.instituteIcon.delete(False)
    
        except Color.DoesNotExist:
            pass
        
        except Exception as e:
            raise e
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Color Theme: {self.institute.name}"

############ TYPES ############
class SemMeta(NamedTuple):
    marks: int
    total: int

class SubjectMeta(NamedTuple):
    sem: int
    marks: int

class SchemaMeta(TypedDict):
    university_icon: str
    institute_icon: str
    university_heading: str
    institute_heading: str
    branch_heading: str