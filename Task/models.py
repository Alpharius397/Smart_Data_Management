import json
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
from django.db import connection
from psycopg2.sql import SQL, Identifier, Literal

from tools.utils import ColumnType, segregateColumns # type: ignore

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
    
    taskID = ForeignKey(
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
    
    class Meta:
        verbose_name = "Assign"
        verbose_name_plural = "Assigns"
        
        constraints = [
            UniqueConstraint(fields=["taskID", "manager"], name="unique_manager_for_each_task"),
        ]

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
    
    @staticmethod
    def getCommonColumn(id: int):
        data_column = Identifier(DataTable.data.field.column)
        taskID = Identifier(DataTable.taskID.field.column)
        semester_column = Identifier(DataTable.semester.field.column)
        data_table = Identifier(DataTable._meta.db_table)
        id = Literal(id)
        
        common_columns: list[str] = []
        
        with connection.cursor() as cursor:
            sql_query = SQL('''
                            select "B"."data" 
                            from (select distinct "A"."data" as "data", count("A"."semester") as "count" from 
                            (select {semester_column} as "semester", jsonb_object_keys(MAX({data_column}::varchar)::jsonb) as "data" 
                            from {data_table} where {taskID}={id} group by {semester_column}) as "A" group by "A"."data")
                            as "B" where "B"."count"=(select count(distinct {semester_column}) from {data_table} where {taskID}={id});
                            ''').format(
                                data_column=data_column,
                                semester_column=semester_column,
                                data_table=data_table,
                                taskID=taskID,
                                id=id
                            ).as_string(cursor.connection)
                            
            print(sql_query)
            cursor.execute(sql_query)
            
            common_columns = [col[0] for col in cursor.fetchall()]

        return common_columns
    
    @staticmethod
    def availableSems(id: int):
        task_table = TaskTable._meta.db_table
        semesterLimit = TaskTable.semesterLimit.field.column
        task_id = DataTable.taskID.field.column
        semester_column = DataTable.semester.field.column
        data_table = DataTable._meta.db_table
        options = []
        
        with connection.cursor() as cursor:
            sql_query = SQL('''select "a" 
                            from generate_series(1, (select {semesterLimit} from {task_table} where "id" = {id} limit 1)) 
                            as "a" where "a" not in (select distinct({semester_column}) from {data_table} where {task_id}={id});
                            ''').format(
                                semesterLimit = Identifier(semesterLimit),
                                task_table = Identifier(task_table),
                                id = Literal(id),
                                semester_column = Identifier(semester_column),
                                data_table = Identifier(data_table),
                                task_id = Identifier(task_id)
                            )
                            
            cursor.execute(sql_query)
            options = [col[0] for col in cursor.fetchall()]

        return options     
    
    @staticmethod
    def getColumnValue(id: int, idx: int, rowID: int, column: str) -> "RowStatus":
        value = RowStatus(True, False, "")
        
        try:
            table_name = Identifier(DataTable._meta.db_table)
            column=Literal(column)
            data_column = Identifier(DataTable.data.field.column)
            task_column = Identifier(DataTable.taskID.field.column)
            semester_column = Identifier(DataTable.semester.field.column)
            rowID=Literal(rowID)
            semester = Literal(idx)
            taskID = Literal(id)

            with connection.cursor() as cursor:
                sql_query = SQL('''
                                select "locked", {data_column}::jsonb?{column} ,{data_column}::json ->> {column} 
                                from {table_name} 
                                where {task_column}={taskID} and "id"={rowID} and {semester_column}={semester} limit 1;
                            ''').format(
                                data_column=data_column,
                                column=column,
                                table_name=table_name,
                                task_column=task_column,
                                rowID=rowID,
                                taskID=taskID,
                                semester_column=semester_column,
                                semester=semester,
                            )

                cursor.execute(sql_query)

                value = cursor.fetchone() or value

            return value

        except Exception as e:
            print(e)
            pass

        return value

    @staticmethod
    def setColumnValue(id: int, idx: int, rowID: int ,column: str, value: str) -> bool:
        result = False

        dicts: dict = json.loads(value)

        if (column not in dicts) or (len(dicts.keys()) > 1):
            raise ValueError("Invalid values detected")

        table_name = Identifier(DataTable._meta.db_table)
        rowColumn = Identifier(DataTable.data.field.column)
        task_column = Identifier(DataTable.taskID.field.column)
        semester_column = Identifier(DataTable.semester.field.column)
        locked = Identifier(DataTable.locked.field.column)
        _column = Literal(column)
        rowID=Literal(rowID)
        semester = Literal(idx)
        taskID = Literal(id)
        _value = Literal(value)

        with connection.cursor() as cursor:
            sql_query = SQL("""
                            update {table_name} set {rowColumn} = {rowColumn}::jsonb || {_value}::jsonb 
                                where {task_column} = {taskID} 
                                and "id" = {rowID}
                                and {semester_column}={semester}
                                and {rowColumn}::jsonb?{_column}
                                and {locked} is false;
                            """
                        ).format(
                            table_name=table_name,
                            rowColumn=rowColumn,
                            _value=_value,
                            task_column=task_column,
                            taskID=taskID,
                            rowID=rowID,
                            semester_column=semester_column,
                            semester=semester,
                            locked=locked,
                            _column=_column,
                        )

            cursor.execute(sql_query)
            result = (cursor.rowcount == 1) or result

        return result
    
    @staticmethod
    def suggestValues(id: int, idx: int, column: str, value: str) -> list[str]:
        column_name = Literal(column)
        table_name = Identifier(DataTable._meta.db_table)
        _value = Literal(f"%{value}%")
        task_column = Identifier(DataTable.taskID.field.column)
        taskID = Literal(id)
        sem_column = Identifier(DataTable.semester.field.column)
        semID = Literal(idx)
        data_column = Identifier(DataTable.data.field.column)
        suggests: list[str] = []

        with connection.cursor() as cursor:
            sql_query = SQL('''
                            select "A"."option" 
                            from (
                                select distinct {data_column}::jsonb ->> {column_name} as "option" 
                                from {table_name} where {task_column}={taskID} and {sem_column}={semID} 
                                and {data_column}::jsonb ->> {column_name} is not null 
                                and {data_column}::jsonb ->> {column_name} like {value}
                                ) 
                            as "A" order by length("A"."option"), "A"."option" limit 5;
            ''').format(
                data_column=data_column,
                column_name=column_name,
                table_name=table_name,
                task_column=task_column,
                taskID=taskID,
                sem_column=sem_column,
                semID=semID,
                value=_value,
            )

            cursor.execute(sql_query)

            suggests = [col[0] for col in cursor.fetchall()]        
            
        return suggests
    
    @staticmethod
    def suggestAllValues(id: int, column: str, value: str) -> list[str]:
        column_name = Literal(column)
        table_name = Identifier(DataTable._meta.db_table)
        _value = Literal(f"%{value}%")
        task_column = Identifier(DataTable.taskID.field.column)
        taskID = Literal(id)
        sem_column = Identifier(DataTable.semester.field.column)
        data_column = Identifier(DataTable.data.field.column)
        suggests: list[str] = []

        with connection.cursor() as cursor:
            sql_query = SQL('''
                            select "A"."option" 
                            from (
                                select distinct {data_column}::jsonb ->> {column_name} as "option" 
                                from {table_name} where {task_column}={taskID}
                                and {data_column}::jsonb ->> {column_name} is not null 
                                and {data_column}::jsonb ->> {column_name} like {value}
                                ) 
                            as "A" order by length("A"."option"), "A"."option" limit 5;
            ''').format(
                data_column=data_column,
                column_name=column_name,
                table_name=table_name,
                task_column=task_column,
                taskID=taskID,
                sem_column=sem_column,
                value=_value,
            )

            cursor.execute(sql_query)

            suggests = [col[0] for col in cursor.fetchall()]        
            
        return suggests
    
    @staticmethod
    def get_columns(id: int, idx: int) -> tuple[int, ColumnType]:
        table_name = Identifier(DataTable._meta.db_table)
        data_column = Identifier(DataTable.data.field.column)  # type: ignore
        semester_column = Identifier(DataTable.semester.field.column)  # type: ignore
        taskID_column = Identifier(DataTable.taskID.field.column)  # type: ignore
        taskID = Literal(id)
        semID = Literal(idx)

        columns: list[str] = []
        count: int = 0

        with connection.cursor() as cursor:
            sql_query = (
                SQL(
                    """
                        select *
                        from (select distinct(jsonb_object_keys(max({data_column}::varchar)::jsonb)) as "option" 
                        from {table_name} where {taskID_column}={taskID} and {semester_column}={semID}) as "A" 
                        order by length("A"."option"), "A"."option";
                    """
                )
                .format(
                    data_column=data_column,
                    table_name=table_name,
                    taskID_column=taskID_column,
                    semester_column=semester_column,
                    semID=semID,
                    taskID=taskID,
                )
            )

            cursor.execute(sql_query)
            columns = [col[0] for col in cursor.fetchall()]
            count = cursor.rowcount

        return count, segregateColumns(columns)

    @staticmethod
    def get_all_columns(id: int) -> tuple[int, ColumnType]:
        table_name = Identifier(DataTable._meta.db_table)
        data_column = Identifier(DataTable.data.field.column)  # type: ignore
        semester_column = Identifier(DataTable.semester.field.column)  # type: ignore
        taskID_column = Identifier(DataTable.taskID.field.column)  # type: ignore
        taskID = Literal(id)

        columns: list[str] = []
        count: int = 0

        with connection.cursor() as cursor:
            sql_query = SQL(
                    """
                    select distinct jsonb_object_keys("A"."data"::jsonb) as "data" 
                    from (select "semester", MAX({data_column}::varchar) as "data" from {table_name} 
                    where {taskID_column}={taskID} group by {semester_column}) as "A" order by "data";
                    """
                ).format(
                    data_column=data_column,
                    table_name=table_name,
                    taskID_column=taskID_column,
                    semester_column=semester_column,
                    taskID=taskID,
                )
            
            cursor.execute(sql_query)

            cursor.execute(sql_query)
            columns = [col[0] for col in cursor.fetchall()]
            count = cursor.rowcount

        return count, segregateColumns(columns)

############ TYPES ############
type Upload = BaseManager[UploadTable]
type Assign = BaseManager[AssignTable]
type Data = BaseManager[DataTable]

class RowStatus(typing.NamedTuple):
    locked: bool
    exists: bool
    value: str

    def __iter__(self):
        yield self.locked
        yield self.exists
        yield self.value