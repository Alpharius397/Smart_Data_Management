from django.db.models import ( # type: ignore
    CharField,
    Model,
    ForeignKey,
    AutoField,
    JSONField,
    BooleanField,
    DateTimeField,
    IntegerField,
    CASCADE,
    RESTRICT,
    SET_NULL,
    UniqueConstraint
)
from django.core.validators import MinValueValidator # type: ignore
from University.models import Branch
from User.models import User, is_admin, is_manager, RoleType
from django import forms # type: ignore
import typing
from django.db.models.manager import BaseManager # type: ignore

############ MODEL ############
class TaskTable(Model):
    id = AutoField(
        verbose_name="Task ID", primary_key=True, null=False, blank=False
    )
    
    name = CharField(
        verbose_name="Task Name", max_length=255, null=False, blank=False
    )
    
    creator = ForeignKey(
        to=User,
        on_delete=SET_NULL,
        null=True,
        blank=True,
    )
    
    branch = ForeignKey(
        to=Branch,
        on_delete=RESTRICT,
        null=False,
        blank=False
    )
    
    semesterLimit = IntegerField(
        verbose_name="Semester",
        null=False,
        blank=False,
        validators=[
            MinValueValidator(1, "Semester count cannot be less than 1!")
        ]
    )
    
    groupByColumn = CharField(
        verbose_name="Group By Column", max_length=255, null=True, blank=True
    )
    
    data: "Data"
    assigned: "Assign"
    
    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        
        constraints = [
            UniqueConstraint(fields=["name", "branch"], name="unique_task_for_each_branch"),
            
        ]
    
    def clean_creators(self):
        if((self.creator is not None) and (not is_admin(self.creator))):
            raise forms.ValidationError("Only Admins can create a Task!")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class UploadTable(Model):
    id = AutoField(
        verbose_name="FileID", primary_key=True, null=False, blank=False
    )
    
    fileName = CharField(
        max_length=255, verbose_name="File Name", null=False, blank=False
    )
    
    task = ForeignKey(
        to=TaskTable,
        on_delete=RESTRICT,
        null=False,
        blank=False,
        related_name="upload",
        verbose_name="File Uploader",
    )
    
    semester = IntegerField(
        verbose_name="Semester",
        null=False,
        blank=False,
        validators=[
            MinValueValidator(1, "Semester cannot be less than 1!")
        ]
    )
    
    data: "Data"
    
    class Meta:
        verbose_name = "Upload"
        verbose_name_plural = "Uploads"
        
        constraints = [
            UniqueConstraint(fields=["fileName", "task"], name="unique_filename_for_each_task"),
            UniqueConstraint(fields=["task", "semester"], name="one_semester_per_task")
            
        ]
        
        
    def clean_semesters(self):
        try:
            if self.semester > self.task.semesterLimit:
                raise forms.ValidationError("Detected more semester than Semester Limit!")
            
        except:
            raise forms.ValidationError("Validation Failed!")
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    

class AssignTable(Model):
    id = AutoField(
        verbose_name="AssignID", primary_key=True, null=False, blank=False
    )
    
    fileID = ForeignKey(
        to=TaskTable,
        verbose_name="taskID",
        related_name="assigned",
        on_delete=CASCADE,
        null=False,
        blank=False,
    )
    
    manager = ForeignKey(
        to=User,
        on_delete=RESTRICT,
        null=False,
        blank=False,
        related_name="manager",
        verbose_name="Assigned User",
        limit_choices_to={"role__role": RoleType.MANAGER},
    )

    def clean_managers(self):
        if not is_manager(self.manager):
            raise forms.ValidationError(
                "Only managers can be assigned to a file",
                code="invalid",
                params={"value": self.manager},
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class DataTable(Model):
    id = AutoField(
        verbose_name="DataID", primary_key=True, null=False, blank=False
    )
    
    taskID = ForeignKey(
        to=TaskTable,
        verbose_name="taskID",
        related_name="data",
        on_delete=CASCADE,
        null=False,
        blank=False,
    )
    
    semester = IntegerField(
        verbose_name="Semester",
        null=False,
        blank=False,
        validators=[
            MinValueValidator(1, "Semester cannot be less than 1!")
        ]
    )
    
    locked = BooleanField(
        verbose_name="Lock Status", default=False, null=False, blank=False
    )

    issued = BooleanField(
        verbose_name="Issue Status", default=False, null=True, blank=False
    )
    
    time_of_lock = DateTimeField(
        verbose_name="Time of Lock", null=True, blank=False, default=None
    )
    
    time_of_issue = DateTimeField(
        verbose_name="Time of Issue", null=True, blank=False, default=None
    )
    
    status = BooleanField(
        verbose_name="Feedback Status", default=None, null=True, blank=False
    )
    
    feed = CharField(
        max_length=255, verbose_name="Feedback", null=True, blank=False, default=None
    )
    
    data = JSONField(verbose_name="rowData", null=False, blank=False)

    def update_data(self, jsonText: dict[str, typing.Any]) -> "DataTable":
        self.data = jsonText
        self.locked = False
        self.issued = False
        self.time_of_issue = None
        self.time_of_lock = None
        self.status = None
        self.feed = None

        return self

############ TYPES ############
type Upload = BaseManager[UploadTable]
type Assign = BaseManager[AssignTable]
type Data = BaseManager[DataTable]
