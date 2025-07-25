from typing import Any, NamedTuple, TypedDict
from django.core.files.uploadedfile import UploadedFile  # type: ignore
from django.shortcuts import render  # type: ignore
from django.urls import reverse  # type: ignore
from django.http import HttpRequest, QueryDict  # type: ignore
from Main.forms import getErrors
from Task.forms import (
    SemesterDeleteForm,
    TaskCreateForm,
    TaskDeleteForm,
    TaskUpdateForm,
    SemesterCreateForm,
    SemesterEditForm,
)
from Task.models import TaskTable
from django.db import transaction  # type: ignore
from django.db.models import QuerySet  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, Task
from constants import DEFAULT_ERROR, MAX_RECORD
from tools.get_image import image_load
from tools.url_auth import (
    htmx_response,
    is_auth_get,
    is_hx_delete,
    is_hx_get,
    is_hx_post,
    auth_needed,
    is_hx_put,
    login_needed,
    semester_permission_check,
    task_permission_check,
)
from User.models import RoleType, User, get_user, is_admin, is_manager
from .models import AssignTable, DataTable
from django.contrib import messages  # type: ignore
import pandas as pd  # type: ignore
from tools.utils import processSubjects, setSwalAlert
from .errors import (
    FileNameExists,
    FileProcessFailed,
    ManagerAlreadyAssigned,
    ManagerNeverAssigned,
    ColumnNotFound,
)
from django.forms import forms  # type: ignore


############ TYPES ############
class ManagerList(NamedTuple):
    id: int
    username: str


class SemData(TypedDict):
    id: int
    count: int

############ CONSTANTS ############
ASSIGN_FORM = "Assign Form"
TASK_CREATE = "Task Creation"
TASK_DELETE = "Task Deletion"
TASK_EDIT = "Task Updation"
SEMESTER_CREATE = "Semester Creation"
SEMESTER_DELETE = "Semester Deletion"
SEMESTER_EDIT = "Semester Updation"

############ UTILS ############
def getAssignForm(user: User, task: TaskTable) -> dict[str, list[ManagerList]]:
    context: dict[str, list[ManagerList]] = {
        "assigned_manager": [],
        "available_managers": [],
    }

    try:
        managers: list[ManagerList] = task.assigned.distinct().values_list(
            "manager__id", "manager__username"
        )

        all_managers: list[ManagerList] = (
            User.objects.filter(
                role__role=RoleType.MANAGER, role__belongs=user.role.belongs
            )
            .exclude(id__in=[i[0] for i in managers])
            .distinct()
            .values_list("id", "username")
        )

        context["managers"] = all_managers
        context["all_managers"] = managers

    except Exception:
        pass

    return context


############ HTTP Request ############
@login_needed(admin_only=True)
def task_create(req: HttpRequest):
    if is_auth_get(req):
        user = get_user(req)
        f = TaskCreateForm(initial={"username": user.username})

        return render(req, "Task/HTML/task.create.html", {"form": f})


@login_needed(admin_only=True)
@task_permission_check
def task_edit(req: HttpRequest, id: int):
    user = get_user(req)

    if is_auth_get(req):
        context = {"id": id}
        try:
            task: TaskTable = req.__getattribute__("task")
            context["form"] = TaskUpdateForm(
                initial={
                    "taskID": task.id,
                    "fileName": task.name,
                    "semesterLimit": task.semesterLimit,
                }
            )

        except Exception as f:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=user, exception=f)
            )
            setSwalAlert(context, DEFAULT_ERROR, title=TASK_EDIT)

        return render(req, "Task/HTML/task.edit.html", context=context)


@login_needed(admin_only=True)
@task_permission_check
def task_delete(req: HttpRequest, id: int):
    if is_auth_get(req):
        context = {"id": id}
        
        try:
            task: TaskTable = req.__getattribute__("task")
            context["form"] = TaskDeleteForm(
                initial={
                    "taskID": task.id,
                    "fileName": task.name,
                    "semesterLimit": task.semesterLimit,
                }
            )

        except Exception as f:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=f)
            )
            setSwalAlert(context, DEFAULT_ERROR, title=TASK_DELETE)

        return render(req, "Task/HTML/task.delete.html", context=context)


@login_needed(admin_only=True)
@task_permission_check
def sem_create(req: HttpRequest, id: int):
    if is_auth_get(req):
        form = SemesterCreateForm(initial={"taskID": id})
        context={"id": id, "form": form}
        try:
            sems = [("", "------")] + list(
                map(lambda x: (x, x), DataTable.availableSems(id))
            )

            form.setChoice(sems)

        except Exception:
            setSwalAlert(context, DEFAULT_ERROR, title=SEMESTER_CREATE)
            
        return render(
            req, "Task/HTML/semester.create.html", context=context
        )


@login_needed(admin_only=True)
@semester_permission_check
def sem_edit(req: HttpRequest, id: int, idx: int):
    if is_auth_get(req):
        form = SemesterEditForm(initial={"taskID": id, "semester": idx})

        return render(
            req,
            "Task/HTML/semester.edit.html",
            context={"id": id, "idx": idx, "form": form},
        )


@login_needed(admin_only=True)
@semester_permission_check
def sem_delete(req: HttpRequest, id: int, idx: int):
    if is_auth_get(req):
        form = SemesterDeleteForm(initial={"taskID": id, "semester": idx})

        return render(
            req,
            "Task/HTML/semester.delete.html",
            context={"id": id, "idx": idx, "form": form},
        )


@login_needed()
@task_permission_check
def get_task(req: HttpRequest, id: int):
    if is_auth_get(req):
        user = get_user(req)

        if is_admin(user):
            return render(req, "Task/HTML/admin.html", context={"id": id})
        elif is_manager(user):
            return render(req, "Task/HTML/manager.html", context={"id": id})


############ HTMX Request ############
@htmx_response
@auth_needed(admin_only=True)
def htmx_task_create(req: HttpRequest):
    user = get_user(req)

    if is_hx_post(req):
        context = setSwalAlert(title=TASK_CREATE)

        f = TaskCreateForm(req.POST)

        if f.is_valid():
            try:
                name = f.cleaned_data.get("fileName")
                semesterLimit = f.cleaned_data.get("semesterLimit")
                task = TaskTable(
                    name=name,
                    semesterLimit=semesterLimit,
                    creator=user,
                    branch=user.role.belongs,
                )
                task.save()
                setSwalAlert(
                    context,
                    "Task was successfully created!",
                    "success",
                )
            except forms.ValidationError as g:  # type: ignore
                setSwalAlert(context, getErrors(g))
            except Exception:
                setSwalAlert(context, DEFAULT_ERROR)

        else:
            setSwalAlert(context, f.getErrors())
        return render(req, "Task/HTMX/message.html", context=context)


@htmx_response
@auth_needed(admin_only=True)
@task_permission_check
def htmx_task_edit(req: HttpRequest, id: int):
    if is_hx_post(req):
        f = TaskUpdateForm(req.POST)
        context = {"id": id, **setSwalAlert(title=TASK_EDIT)}
        try:
            task: TaskTable = req.__getattribute__("task")
            if f.is_valid():
                name = f.cleaned_data.get("fileName")
                semesterLimit = f.cleaned_data.get("semesterLimit")

                task.semesterLimit = semesterLimit
                task.name = name

                task.save()
                setSwalAlert(
                    context, "Task Edited Successfully", "success"
                )
            else:
                setSwalAlert(context, f.getErrors())

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Task/HTMX/message.html", context=context)


@htmx_response
@auth_needed(admin_only=True)
@task_permission_check
def htmx_task_delete(req: HttpRequest, id: int):
    if is_hx_post(req):
        context: dict[str, str] = setSwalAlert(title=TASK_DELETE)

        try:
            task: TaskTable = req.__getattribute__("task")
            task.delete()
            setSwalAlert(
                context,
                "Task was deleted successfully! Redirecting to Task Dashboard",
                "success",
            )

            context["redirect"] = req.build_absolute_uri(reverse("Dash:index"))

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(
            req,
            "Task/HTMX/message.html",
            context=context
        )


@htmx_response
@auth_needed(admin_only=True)
@task_permission_check
def htmx_sem_create(req: HttpRequest, id: int):
    if is_hx_post(req):
        pd_data: pd.DataFrame = pd.DataFrame()
        image_id: list[int] = []
        form = SemesterCreateForm(req.POST, req.FILES)
        
        context = {"option": [], **setSwalAlert(title=SEMESTER_CREATE)}

        try:
            semesterChoice = [("", "------")] + list(
                map(lambda x: (x, x), DataTable.availableSems(id))
            )
            form.setChoice(semesterChoice)
            
            with transaction.atomic():
                if form.is_valid():
                    excel_file = req.FILES["file"]
                    assert isinstance(excel_file, UploadedFile), (
                        "Incompatible File Type!"
                    )

                    with excel_file.open() as file:
                        image_id, pd_data = image_load(file.read())

                        if pd_data.empty:
                            raise FileProcessFailed()

                    pd_data.rename(
                        columns=processSubjects(list(pd_data.columns), image_id),
                        inplace=True,
                    )

                    fields = pd_data.columns
                    rows: list[DataTable] = []
                    task: TaskTable = req.__getattribute__("task")
                    sem = form.cleaned_data.get("semester")

                    for row in pd_data.itertuples(index=False):
                        rowJson = {
                            fields[idx]: str(row[idx]) for idx in range(len(row))
                        }
                        rows.append(DataTable(taskID=task, data=rowJson, semester=sem))

                    DataTable.objects.bulk_create(rows)
                    semesterChoice = [("", "------")] + list(
                        map(lambda x: (x, x), DataTable.availableSems(id))
                    )
                    setSwalAlert(
                        context,
                        "Semester Data Uploaded Successfully",
                        "success",
                    )
                else:
                    setSwalAlert(
                        context, form.getErrors()
                    )
                context["option"] = semesterChoice

        except AssertionError as e:
            setSwalAlert(context, str(e))

        except (ValueError, FileProcessFailed):
            setSwalAlert(
                context, FileProcessFailed().get_error()
            )

        except FileNameExists as f:
            setSwalAlert(context, f.get_error())

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(
            req, "Task/HTMX/semester.create.html", context=context
        )


@htmx_response
@auth_needed(admin_only=True)
@semester_permission_check
def htmx_sem_edit(req: HttpRequest, id: int, idx: int):
    if is_hx_post(req):
        pd_data: pd.DataFrame = pd.DataFrame()
        image_id: list[int] = []
        form = SemesterEditForm(req.POST, req.FILES)
        context = setSwalAlert(title=SEMESTER_EDIT)

        try:
            with transaction.atomic():
                if form.is_valid():
                    excel_file = req.FILES["file"]
                    assert isinstance(excel_file, UploadedFile), (
                        "Incompatible File Type!"
                    )

                    with excel_file.open() as file:
                        image_id, pd_data = image_load(file.read())
                        print(pd_data)
                        if pd_data.empty:
                            raise FileProcessFailed()

                    pd_data.rename(
                        columns=processSubjects(list(pd_data.columns), image_id),
                        inplace=True,
                    )

                    fields = pd_data.columns
                    create: list[DataTable] = []
                    task: TaskTable = req.__getattribute__("task")

                    data: QuerySet[DataTable] = task.data.filter(semester=idx)
                    data.delete()

                    for row in pd_data.itertuples(index=False):
                        rowJson = {
                            fields[idx]: str(row[idx]) for idx in range(len(row))
                        }
                        create.append(
                            DataTable(taskID=task, data=rowJson, semester=idx)
                        )

                    DataTable.objects.bulk_create(create)

                    setSwalAlert(
                        context,
                        "Semester Data Updated Successfully",
                        "success",
                    )

                else:
                    setSwalAlert(
                        context, form.getErrors()
                    )

        except AssertionError as e:
            setSwalAlert(context, str(e))

        except (ValueError, FileProcessFailed):
            setSwalAlert(
                context, FileProcessFailed().get_error()
            )

        except FileNameExists as f:
            setSwalAlert(context, f.get_error())

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Task/HTMX/message.html", context=context)


@htmx_response
@auth_needed(admin_only=True)
@semester_permission_check
def htmx_sem_delete(req: HttpRequest, id: int, idx: int):
    if is_hx_post(req):
        form = SemesterDeleteForm(req.POST)
        context: dict[str, str] = setSwalAlert(title=SEMESTER_DELETE)

        try:
            with transaction.atomic():
                if form.is_valid():
                    task: TaskTable = req.__getattribute__("task")

                    task.data.filter(semester=idx).delete()

                    setSwalAlert(
                        context,
                        "Semester Data Deleted Successfully! Redirecting to the Semester Dashboard",
                        "success",
                    )

                    context["redirect"] = req.build_absolute_uri(
                        reverse("Task:index", args=(id,))
                    )

                else:
                    setSwalAlert(
                        context, form.getErrors()
                    )

        except AssertionError as e:
            setSwalAlert(context, str(e))

        except (ValueError, FileProcessFailed):
            setSwalAlert(
                context, FileProcessFailed().get_error()
            )

        except FileNameExists as f:
            setSwalAlert(context, f.get_error())

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Task/HTMX/message.html", context=context)


@htmx_response
@auth_needed()
@task_permission_check
def htmx_get_task(req: HttpRequest, id: int):
    if is_hx_get(req):
        context = {"id": id, "semesters": []}

        try:
            task: TaskTable = req.__getattribute__("task")
            semList: list[SemData] = []

            semester = req.GET.get("semester", "")
            start = int(req.GET.get("page", "0"))

            for sems in (
                task.data.filter(semester__icontains=semester)
                .only("semester")
                .distinct("semester")
                .order_by("semester")[start : start + MAX_RECORD]
            ):
                count = task.data.filter(semester=sems.semester).count()
                semList.append(SemData(id=sems.semester, count=count))

            context["semesters"] = semList
            context["next"] = start + MAX_RECORD

            if (semester) and (not semList):
                messages.error(req, "No matching Semesters Found!")
            elif (not semList) and (start == 0):
                messages.error(req, "No Semesters Found!")
        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=e)
            )
            
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Task/HTMX/index.html", context=context)


@htmx_response
@auth_needed(admin_only=True)
@task_permission_check
def assign_form(req: HttpRequest, id: int):
    context: dict[str, Any] = {"id": id, "error": True}
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")

    if is_hx_get(req):
        try:
            context.update(getAssignForm(user, task))
            context["error"] = False
        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )

            setSwalAlert(context, DEFAULT_ERROR, title=ASSIGN_FORM)

        return render(req, "Task/HTMX/assign.html", context=context)

    elif is_hx_put(req):
        value = QueryDict(req.body)  # type: ignore

        managerID = value.get("user", "")
        setSwalAlert(context, title=ASSIGN_FORM)

        try:
            manager = User.objects.get(id=managerID)

            assignFlag = task.assigned.filter(manager__id=managerID).exists()  # type: ignore

            if assignFlag:
                raise ManagerAlreadyAssigned(managerID, id)

            assignee = AssignTable(taskID=task, manager=manager)
            assignee.save()

            context.update(getAssignForm(user, task))

            setSwalAlert(
                context,
                f"Manager ID: {managerID} is added to the Task ID: {id}",
                "success",
            )
        except User.DoesNotExist:
            setSwalAlert(
                context, f"Manager ID: {managerID} does not exists!"
            )
        except ManagerAlreadyAssigned as f:
            setSwalAlert(context, f.get_error())

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Task/HTMX/assign.update.html", context=context)

    elif is_hx_delete(req):
        value = req.GET  # type: ignore

        managerID = value.get("user", "")
        setSwalAlert(context, title=ASSIGN_FORM)
        try:
            manager = User.objects.get(id=managerID)

            notAssignFlag = task.assigned.filter(manager__id=managerID).exists()  # type: ignore

            if not notAssignFlag:
                raise ManagerNeverAssigned(managerID, id)

            assignee = AssignTable.objects.get(taskID=task, manager=manager)
            assignee.delete()

            context.update(getAssignForm(user, task))
            setSwalAlert(
                context, f"Manager ID: {managerID} is removed from Task ID: {id}", "success"
            )

        except User.DoesNotExist:
            setSwalAlert(context, "Manager ID: {managerID} does not exists!")

        except ManagerNeverAssigned as f:
            setSwalAlert(context, f.get_error())

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )

            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Task/HTMX/assign.update.html", context=context)


@htmx_response
@auth_needed(admin_only=True)
@task_permission_check
def groupBy_form(req: HttpRequest, id: int):
    context: dict[str, Any] = {"id": id}
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")

    if is_hx_get(req):
        try:
            context["column"] = task.groupByColumn

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )

            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Task/HTMX/groupBy.html", context=context)

    elif is_hx_put(req):
        try:
            context["column"] = DataTable.getCommonColumn(id)

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )

            setSwalAlert(context, DEFAULT_ERROR)


        return render(req, "Task/HTMX/groupBy.change.html", context=context)

    elif is_hx_delete(req):
        try:
            context["column"] = task.groupByColumn

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )

            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Task/HTMX/groupBy.view.html", context=context)

    elif is_hx_post(req):
        column: str = req.POST.get("column", "")
        context["column"] = column
        setSwalAlert(context, title="Group By Form")
        try:
            _column = bytes.fromhex(column).decode()
            columns = set(DataTable.getCommonColumn(id))

            if _column not in columns:
                raise ColumnNotFound(column)

            task.groupByColumn = _column
            task.save()
            context["column"] = _column
            setSwalAlert(context, "Group By Column changed successfully", "success")

        except ColumnNotFound as f:
            setSwalAlert(context, f.get_error())
            
        except ValueError:
            setSwalAlert(context, "Invalid Column Name detected! Request Aborted")
        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )

            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Task/HTMX/groupBy.view.html", context=context)

