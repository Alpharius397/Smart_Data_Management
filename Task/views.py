from typing import TypedDict
from asgiref.sync import async_to_sync
from django.core.files.uploadedfile import UploadedFile # type: ignore
from django.shortcuts import render  # type: ignore
from django.http import HttpRequest  # type: ignore
from Task.forms import TaskCreateForm, TaskDeleteForm, TaskUpdateForm, SemesterCreateForm, SemesterEditForm
from Task.models import TaskTable, UploadTable
from django.db import transaction # type: ignore
from django.db.models import Q, QuerySet # type: ignore
from Logs.loggers import APP_LOG, LogStructure, Task
from constants.constants import DEFAULT_ERROR, MAX_RECORD
from tools.get_image import image_load
from tools.url_auth import (
    htmx_response,
    is_auth_get,
    is_hx_delete,
    is_hx_get,
    is_hx_post,
    auth_needed,
    login_needed,
    semester_permission_check,
    task_permission_check,
)
from User.models import get_post_id, get_user
from .models import UploadTable, DataTable
from University.models import Schema, Subject
from django.contrib import messages  # type: ignore
import pandas as pd  # type: ignore
from tools.utils import processSubjects
from University.errors import SchemaNotDefined
from .errors import (
    FileLocked,
    FileNameExists,
    FileProcessFailed,
    InvalidForm,
)
from django.forms import forms # type: ignore
from django.db import connection
from psycopg2.sql import SQL, Identifier, Literal # type: ignore

def availableSems(id: int):
    task_table = TaskTable._meta.db_table
    semesterLimit = TaskTable.semesterLimit.field.column
    task_id = DataTable.taskID.field.column
    semester_column = DataTable.semester.field.column
    data_table = DataTable._meta.db_table
    options = []
    
    with connection.cursor() as cursor:
        sql_query = SQL('select "a" from generate_series(1, (select {semesterLimit} from {task_table} where "id" = {id} limit 1)) as "a" where "a" not in (select distinct({semester_column}) from {data_table} where {task_id}={id});').format(
                            semesterLimit = Identifier(semesterLimit),
                            task_table = Identifier(task_table),
                            id = Literal(id),
                            semester_column = Identifier(semester_column),
                            data_table = Identifier(data_table),
                            task_id = Identifier(task_id)
                        ).as_string(
                            cursor.connection
                        )
                        
        cursor.execute(sql_query)
        options = [col[0] for col in cursor.fetchall()]

    return options        


@login_needed(admin_only=True)
def task_create(req: HttpRequest):
    if is_auth_get(req):
        f = TaskCreateForm(initial={"username": req.user.username})

        return render(req, "Task/HTML/task.create.html", {"form": f})

@htmx_response
@auth_needed(admin_only=True)
def htmx_task_create(req: HttpRequest):
    user = get_user(req)
    
    if is_hx_post(req):
        f = TaskCreateForm(req.POST)
        
        if f.is_valid():
            try:
                post = get_post_id(user)
                name = f.cleaned_data.get("fileName")
                semesterLimit = f.cleaned_data.get("semesterLimit")
                task = TaskTable(name=name, semesterLimit=semesterLimit, creator=user, branch=user.role.belongs)
                task.save()
                messages.success(req, "Task was successfully created!")
            except forms.ValidationError as g:
                print(g)
                for field, error in g.error_dict.items(): 
                    messages.error(req, "{}: {}".format(field, ",".join([','.join(i) for i in error])))
            except Exception as e:
                messages.error(req, DEFAULT_ERROR)
        else:
            for field, error in f.errors.items():
                messages.error(req, "{}: {}".format(TaskCreateForm.declared_fields.get(field).label, ",".join([','.join(i) for i in error.data])))
        
                
        return render(req, "Task/HTMX/message.html")

@login_needed(admin_only=True)
@task_permission_check
def task_edit(req: HttpRequest, id: int):
    if is_auth_get(req):
    
        context = {"id": id}
        try:
            task: TaskTable = req.__getattribute__("task")
            context["form"] = TaskUpdateForm(initial={"taskID": task.id, "fileName": task.name, "semesterLimit": task.semesterLimit})
            
        except TaskTable.DoesNotExist:
            messages.error(req, "Task ID: {} does not exists!".format(id))

        except Exception as f:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=f)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Task/HTML/task.edit.html", context=context)

@htmx_response
@auth_needed(admin_only=True)
@task_permission_check
def htmx_task_edit(req: HttpRequest, id: int):
    if is_hx_post(req):
        f = TaskUpdateForm(req.POST)
        
        try:
            task: TaskTable = req.__getattribute__("task")
            if f.is_valid():

                name = f.cleaned_data.get("fileName")
                semesterLimit = f.cleaned_data.get("semesterLimit")
                
                task.semesterLimit = semesterLimit
                task.name = name
                
                task.save()
                messages.success(req, "Task Edited Successfully")
            else:
                for field, error in f.errors.items():
                    messages.error(req, "{}: {}".format(TaskUpdateForm.declared_fields.get(field).label, ",".join([','.join(i) for i in error.data])))
            
        except TaskTable.DoesNotExist:
            messages.error(req, "Task ID: {} does not exists!".format(id))

        except Exception as f:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=f)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Task/HTMX/message.html")

@login_needed(admin_only=True)
@task_permission_check
def task_delete(req: HttpRequest, id: int):
    if is_auth_get(req):
    
        context = {"id": id}
        try:
            task: TaskTable = req.__getattribute__("task")
            context["form"] = TaskDeleteForm(initial={"taskID": task.id, "fileName": task.name, "semesterLimit": task.semesterLimit})
            
        except TaskTable.DoesNotExist: # Wouldn't reach this
            messages.error(req, "Task ID: {} does not exists!".format(id))

        except Exception as f:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=f)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Task/HTML/task.delete.html", context=context)

@htmx_response
@auth_needed(admin_only=True)
@task_permission_check
def htmx_task_delete(req: HttpRequest, id: int):
    if is_hx_post(req):
    
        try:
            task: TaskTable = req.__getattribute__("task")
            task.delete()
            messages.success(req, "Task was deleted successfully")
            
        except TaskTable.DoesNotExist: # Wouldn't reach this
            messages.error(req, "Task ID: {} does not exists!".format(id))

        except Exception as f:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=f)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Task/HTMX/message.html")

@login_needed(admin_only=True)
@task_permission_check
def sem_create(req: HttpRequest, id: int):
    
    if is_auth_get(req):
        sems = [("", "------")] + list(map(lambda x: (x,x)  ,availableSems(id)))
        form = SemesterCreateForm(initial={"taskID": id})
        form.setChoice(sems)
        
        return render(req, "Task/HTML/semester.create.html", context={"id": id, "form": form})
        
@htmx_response
@auth_needed(admin_only=True)
@task_permission_check
def htmx_sem_create(req: HttpRequest, id: int):
    if is_hx_post(req):
        pd_data: pd.DataFrame = pd.DataFrame()
        image_id: list[int] = []
        form = SemesterCreateForm(req.POST, req.FILES)
        semesterChoice = [("", "------")] + list(map(lambda x: (x,x), availableSems(id)))
        form.setChoice(semesterChoice)
        
        try:
            with transaction.atomic():
                if form.is_valid():
                    
                    excel_file = req.FILES["file"]
                    assert isinstance(excel_file, UploadedFile), "Incompatible File Type!"
                    
                    with excel_file.open() as file:
                        image_id, pd_data = image_load(file.read())

                        if pd_data.empty:
                            raise FileProcessFailed()
                    
                    fields = pd_data.columns
                    
                    pd_data.rename(
                        columns=processSubjects(
                            list(fields), image_id
                        ),
                        inplace=True,
                    )
                    
                    rows: list[DataTable] = []
                    task: TaskTable = req.__getattribute__("task")
                    sem = form.cleaned_data.get("semester")
                    
                    for row in pd_data.itertuples(index=False):
                        rowJson = {fields[idx]: str(row[idx]) for idx in range(len(row))}
                        rows.append(DataTable(taskID=task, data=rowJson, semester=sem))

                    DataTable.objects.bulk_create(rows)
                    semesterChoice = [("", "------")] + list(map(lambda x: (x,x), availableSems(id)))
                    messages.success(req, f"Semester Data Uploaded Successfully")
                    
                else:
                    for field, error in form.errors.items(): 
                        messages.error(req, "{}: {}".format(SemesterCreateForm.declared_fields.get(field).label, ",".join([','.join(i) for i in error.data])))
                        
        except AssertionError as e:
            messages.error(req, str(e))

        except (ValueError, FileProcessFailed):
            messages.error(req, FileProcessFailed().get_error())

        except FileNameExists as f:
            messages.error(req, f.get_error())

        except Exception as e:
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Task/HTMX/semester.create.html", context={'option': semesterChoice})

@login_needed(admin_only=True)
@semester_permission_check
def sem_edit(req: HttpRequest, id: int, idx: int):
    
    if is_auth_get(req):
        form = SemesterEditForm(initial={"taskID": id, "semester": idx})
        
        return render(req, "Task/HTML/semester.edit.html", context={"id": id, "idx": idx, "form": form})
    
@htmx_response
@auth_needed(admin_only=True)
@task_permission_check
def htmx_sem_edit(req: HttpRequest, id: int, idx: int):
    
    if is_hx_post(req):
        pd_data: pd.DataFrame = pd.DataFrame()
        image_id: list[int] = []
        form = SemesterEditForm(req.POST, req.FILES)
        
        try:
            with transaction.atomic():
                if form.is_valid():
                    
                    excel_file = req.FILES["file"]
                    assert isinstance(excel_file, UploadedFile), "Incompatible File Type!"
                    
                    with excel_file.open() as file:
                        image_id, pd_data = image_load(file.read())

                        if pd_data.empty:
                            raise FileProcessFailed()
                    
                    fields = pd_data.columns
                    
                    pd_data.rename(
                        columns=processSubjects(
                            list(fields), image_id
                        ),
                        inplace=True,
                    )
                    
                    update: list[DataTable] = []
                    create: list[DataTable] = []
                    task: TaskTable = req.__getattribute__("task")
                    sem = form.cleaned_data.get("semester")
                    
                    data: QuerySet[DataTable] = task.data.filter(semester=idx)
                    count: int = data.count()
                    
                    for serial, row in enumerate(pd_data.itertuples(index=False)):
                        rowJson = {fields[idx]: str(row[idx]) for idx in range(len(row))}
                        
                        if serial < count:
                            update.append(data[serial].update_data(rowJson))
                            print(data[serial].semester)
                        else:
                            create.append(DataTable(taskID=task, data=rowJson, semester=sem))

                    DataTable.objects.bulk_create(create)
                    DataTable.objects.bulk_update(
                        update,
                        fields=[
                            "data",
                            "issued",
                            "locked",
                            "time_of_issue",
                            "time_of_lock",
                            "status",
                            "feed",
                        ])
                    
                    messages.success(req, f"Semester Data Updated Successfully")
                    
                else:
                    for field, error in form.errors.items(): 
                        messages.error(req, "{}: {}".format(SemesterCreateForm.declared_fields.get(field).label, ",".join([','.join(i) for i in error.data])))
                        
        except AssertionError as e:
            messages.error(req, str(e))

        except (ValueError, FileProcessFailed):
            messages.error(req, FileProcessFailed().get_error())

        except FileNameExists as f:
            messages.error(req, f.get_error())

        except Exception as e:
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Task/HTMX/message.html")
    
@login_needed(admin_only=True)
def delete_screen(req: HttpRequest, id: int):
    if is_auth_get(req):
        context = {"id": id}

        try:
            exists = UploadTable.objects.filter(id=id).only("id").exists()

            if not exists:
                raise FileDoesNotExists(id)

        except FileDoesNotExists as e:
            messages.error(req, e.get_error())

        except Exception as f:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=f)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Upload/delete.html", context)

@login_needed(admin_only=True)
@task_permission_check
def get_task(req: HttpRequest, id: int):
    if is_auth_get(req):
        return render(req, "Task/HTML/index.html", context={"id": id})

class SemData(TypedDict):
    id: int
    count: int

@htmx_response
@auth_needed(admin_only=True)
@task_permission_check
def htmx_get_task(req: HttpRequest, id: int):
    if is_hx_get(req):
        context = {"id": id, "semesters":[], "error":None}
        
        try:
            task: TaskTable = req.__getattribute__("task")
            semList: list[SemData] = []
            
            semester = req.GET.get("semester", "")
            start = int(req.GET.get("page", "0"))
            
            for sems in task.data.filter(semester__icontains=semester).only("semester").distinct("semester").order_by("semester")[start: start + MAX_RECORD]:
                count = task.data.filter(semester=sems.semester).count()
                semList.append(SemData(id=sems.semester, count=count))
            
            context["semesters"] = semList
            context["next"] = start + MAX_RECORD
            
            if (semester) and (not semList):
                context['error'] = "No matching Semesters Found!"
            elif (not semList) and (start == 0):
                context['error'] = "No Semesters Found!"
            
        except Exception as e:
            print(e)
            context["error"] = DEFAULT_ERROR
    
        return render(req, "Task/HTMX/index.html", context=context)
    
@login_needed(admin_only=True)
@task_permission_check
def get_sem(req: HttpRequest, id: int):
    if is_auth_get(req):
        return render(req, "Task/HTML/index.html", context={"id": id})