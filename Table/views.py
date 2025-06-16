from io import BytesIO
import typing
from django.contrib import messages  # type: ignore
from django.db.models import Q  # type: ignore
from PIL import Image, UnidentifiedImageError  # type: ignore
from django.shortcuts import render  # type: ignore
from django.http import HttpRequest, HttpResponse  # type: ignore
from Task.models import DataTable, TaskTable
from User.models import (
    get_user,
    is_admin,
    is_manager,
)
from tools.url_auth import (
    task_permission_check,
    semester_permission_check,
    get_color,
    htmx_response,
    is_auth_get,
    is_hx_get,
    is_hx_post,
    is_hx_put,
    auth_needed,
    login_needed,
)
from Table.errors import (
    ColumnDoesNotExist,
    OnlyImageAllowed,
    OnlyTextAllowed,
    RowLocked,
)
from tools.utils import boolSQL, get_2_value, get_3_value
from Logs.loggers import APP_LOG, LogStructure, Task
from django.http import QueryDict
from constants.constants import DEFAULT_ERROR, MAX_RECORD
from Main.models import *
from psycopg2.sql import SQL, Identifier, Literal, Composable  # type: ignore
from tools.get_image import b64encode
from django.db import connection  # type: ignore


############ TYPES ############
class ManagerList(typing.NamedTuple):
    id: int
    username: str

class UpdateStatus(typing.NamedTuple):
    updated: bool
    exists: bool
    locked: bool

class Context(typing.NamedTuple):
    ID: str
    data: dict
    locked: bool 
    issued: bool
    status: bool | None
    
############ UTILS ############
def get_sem_context(
    req: HttpRequest, 
    id: int,
    idx: int,
    column: str = "",
    value: str = "",
    issue: typing.Literal['true', 'false'] = "false",
    status: typing.Literal['true', 'false', 'none'] = "none",
    lock: typing.Literal['true', 'false'] = "false",
    page: int = 0,
) -> dict[str, int | dict | str | bool]:
    
    context: dict[str, int | dict | str | bool] = {"id": id, "idx": idx}
    user = get_user(req)

    try:
        task: TaskTable = req.__getattribute__("task")
        column = bytes.fromhex(column).decode()
        searching = status or issue or lock or (column and value)
        query = Q(semester=idx)

        if status:
            query &= Q(status=get_3_value(status))

        if issue:
            query &= Q(issued=get_2_value(issue))

        if lock:
            query &= Q(locked=get_2_value(lock))

        if column and value:
            query &= Q(
                **{
                    f"data__{column}__isnull": False,
                    f"data__{column}__icontains": value,
                }
            )

        records = task.data.filter(query).order_by("id")[page : page + MAX_RECORD]

        pd_data = {
            (row.id): {
                "status": row.status,
                "locked": row.locked,
                "issued": row.issued,
                "data": row.data,
            }
            for row in records
        }

        empty = not bool(pd_data)

        if searching and (page == 0) and empty:
            context["error"] = "No Matching Records Found"

        context.update(
            {
                "result": pd_data,
                "start": page,
                "max_record": page + MAX_RECORD,
                "isAdmin": is_admin(user)
            }
        )
        
    except Exception as e:
        APP_LOG.write_error(
            LogStructure()
            .set_request(req)
            .set_description(
                type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
            )
        )
        context["error"] = DEFAULT_ERROR

    return context

def get_context(
    req: HttpRequest, 
    id: int,
    column: str = "",
    value: str = "",
    issued: typing.Literal['true', 'false'] = "false",
    status: typing.Literal['true', 'false', 'none'] = "none",
    locked: typing.Literal['true', 'false'] = "false",
    page: int = 0,
) -> dict[str, int | dict | str | bool]:
    context: dict[str, Any] = {"id": id}
    
    table_name = Identifier(DataTable._meta.db_table)
    data_column = Identifier(DataTable.data.field.column)  # type: ignore
    locked_column = Identifier(DataTable.locked.field.column)  # type: ignore
    issued_column = Identifier(DataTable.issued.field.column)  # type: ignore
    status_column = Identifier(DataTable.status.field.column)  # type: ignore
    taskID_column = Identifier(DataTable.taskID.field.column)  # type: ignore
    taskID = Literal(id)
    user = get_user(req)
    
    try:
        task: TaskTable = req.__getattribute__("task")
        groupBy = Literal(task.groupByColumn)
        pageOffset = Literal(page)
        column = bytes.fromhex(column).decode()
        searching = status or issued or locked or (column and value)
        
        query: list[Composable] = [SQL('true')]

        if(column and value):
            sub_query = SQL('("A"."data"::jsonb->>{0}) like {1}').format(Literal(column), Literal(f"%{value}%"))
            query.append(sub_query)
        
        if(locked):
            sub_query = SQL('"A"."locked" is {0}'.format(boolSQL(get_2_value(locked))))
            query.append(sub_query)
            
        if(issued):
            sub_query = SQL('"A"."issued" is {0}'.format(boolSQL(get_2_value(issued))))
            query.append(sub_query)

            
        if(status):
            sub_query = SQL('"A"."status" is {0}'.format(boolSQL(get_3_value(status))))
            query.append(sub_query)
        
        searchQuery = SQL('{0}').format(
            SQL(' and ').join(query)
        )
        
        records: list[Context] = []
        
        with connection.cursor() as cursor:
            sql_query = SQL('select * from (select {data_column}::jsonb ->>{groupBy} as "ID", jsonsum({data_column}::jsonb)::jsonb as "data", bool_and({locked_column}) as "locked", bool_and({issued_column}) as "issued", bool_and({status_column}) as "status" from {table_name} where {taskID_column}={taskID} group by "ID" order by {data_column}::jsonb ->>{groupBy}) as "A" where {searchQuery} limit 5 offset {pageOffset};').format(
                data_column=data_column,
                groupBy=groupBy,
                locked_column=locked_column,
                issued_column=issued_column,
                status_column=status_column,
                table_name=table_name,
                taskID_column=taskID_column,
                searchQuery=searchQuery,
                taskID=taskID,
                pageOffset=pageOffset,
            )

            cursor.execute(sql_query)
            print(sql_query.as_string(cursor.connection))            
            for col in cursor.fetchall():
                ID, Data, Locked, Issued, Status = col
                records.append(Context(ID, json.loads(Data), Locked, Issued, Status))

        pd_data = {
            (row.ID): {
                "status": row.status,
                "locked": row.locked,
                "issued": row.issued,
                "data": row.data,
            }
            for row in records
        }

        empty = not bool(pd_data)

        if searching and (page == 0) and empty:
            context["error"] = "No Matching Records Found"
        context.update(
            {
                "result": pd_data,
                "start": page,
                "max_record": page + MAX_RECORD,
                "isAdmin": is_admin(user)
            }
        )
        
    except Exception as e:
        print(e)
        APP_LOG.write_error(
            LogStructure()
            .set_request(req)
            .set_description(
                type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
            )
        )
        
        context["error"] = DEFAULT_ERROR

    return context

def get_row_context(
    req: HttpRequest, 
    id: int,
    idx: str
) -> dict[str, int | dict | str | bool]:
    context: dict[str, Any] = {"id": id}
    
    table_name = Identifier(DataTable._meta.db_table)
    data_column = Identifier(DataTable.data.field.column)  # type: ignore
    locked_column = Identifier(DataTable.locked.field.column)  # type: ignore
    issued_column = Identifier(DataTable.issued.field.column)  # type: ignore
    status_column = Identifier(DataTable.status.field.column)  # type: ignore
    taskID_column = Identifier(DataTable.taskID.field.column)  # type: ignore
    taskID = Literal(id)
    rowID = Literal(idx)
    user = get_user(req)
    
    try:
        task: TaskTable = req.__getattribute__("task")
        groupBy = Literal(task.groupByColumn)
        
        with connection.cursor() as cursor:
            sql_query = SQL('select {data_column}::jsonb ->>{groupBy} as "ID", jsonsum({data_column}::jsonb)::jsonb as "data", bool_and({locked_column}) as "locked", bool_and({issued_column}) as "issued", bool_and({status_column}) as "status" from {table_name} where {taskID_column}={taskID} and {data_column}::jsonb ->>{groupBy}={rowID} group by "ID" limit 1;').format(
                data_column=data_column,
                groupBy=groupBy,
                locked_column=locked_column,
                issued_column=issued_column,
                status_column=status_column,
                table_name=table_name,
                taskID_column=taskID_column,
                taskID=taskID,
                rowID=rowID
            )

            cursor.execute(sql_query)            
            ID, Data, Locked, Issued, Status = cursor.fetchone()
            record = Context(ID, json.loads(Data), Locked, Issued, Status)
            
            pd_data = {
                (record.ID): {
                    "status": record.status,
                    "locked": record.locked,
                    "issued": record.issued,
                    "data": record.data,
                }
            }

        context.update(
            {
                "result": pd_data,
                "isAdmin": is_admin(user)
            }
        )
        
    except Exception as e:
        APP_LOG.write_error(
            LogStructure()
            .set_request(req)
            .set_description(
                type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
            )
        )
        print(e)
        context["error"] = DEFAULT_ERROR

    return context

########### HTTP Request #############
@login_needed()
@semester_permission_check
def sem_view(req: HttpRequest, id: int, idx: int) -> HttpResponse | None:
    user = get_user(req)
    context: dict[str, int] = {"id": id, "idx": idx}
    if is_auth_get(req):
        get_color(req)

        if is_admin(user):
            return render(req, "Table/HTML/table/admin.html", context=context)

        elif is_manager(user):
            return render(req, "Table/HTML/table/manager.html", context=context)

    return None

@login_needed()
@task_permission_check
def complete_view(req: HttpRequest, id: int) -> HttpResponse | None:
    user = get_user(req)
    context: dict[str, int] = {"id": id}
    if is_auth_get(req):
        get_color(req)

        if is_admin(user):
            return render(req, "Table/HTML/complete.html", context=context)

        elif is_manager(user):
            return render(req, "Table/HTML/complete.html", context=context)

    return None

############ HTMX Request ############
@htmx_response
@auth_needed()
@semester_permission_check
def sem_column_view(req: HttpRequest, id: int, idx: int) -> HttpResponse | None:
    if is_hx_get(req):
        context = {"search": [], "column": [], "count": 0}

        try:
            count, (images, text) = DataTable.get_columns(id, idx)

            context["search"] = text

            text.extend(images)

            context["column"] = text
            context["count"] = count

        except Exception as e:
            print(e)

            messages.error(req, DEFAULT_ERROR)
        return render(req, "Table/HTMX/column.html", context=context)

    return None

@htmx_response
@auth_needed()
@semester_permission_check
def sem_row_view(req: HttpRequest, id: int, idx: int) -> HttpResponse:
    user = get_user(req)
    
    if is_hx_get(req):
        column = req.GET.get("column", "")
        value = req.GET.get("search", "")
        issue = req.GET.get("issue", "")
        status = req.GET.get("status", "")
        lock = req.GET.get("lock", "")

        try:
            page = int(req.GET.get("page", "0"))
        except Exception as e:
            page = 0
            
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )
            
        context = get_sem_context(req, id, idx, column, value, issue, status, lock, page)

        return render(req, "Table/HTMX/sem.row.html", context=context)

    return HttpResponse(status=403)

@htmx_response
@auth_needed()
@task_permission_check
def sem_suggest_view(req: HttpRequest, id: int, idx: int):
    if is_hx_get(req):
        column = req.GET.get("column", "")
        value = req.GET.get("search", "")
        context: dict[str, list[str] | int] = {"id": id, "idx": idx, "option": []}

        try:
            column = bytes.fromhex(column).decode()
            suggestions = DataTable.suggestValues(id, idx, column, value)
            context["option"] = suggestions

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=id, user=req.user, exception=e
                )
            )

        return render(req, "Table/HTMX/suggests.html", context=context)

@htmx_response
@auth_needed()
@semester_permission_check
def sem_refresh_row(req: HttpRequest, id: int, idx: int, rowID: int) -> HttpResponse:
    if is_hx_get(req):
        context: dict[str, Any] = {"id": id, "idx": idx}

        try:
            records = DataTable.objects.get(taskID__id=id,semester=idx,id=rowID)

            pd_data = {
                (records.id): {
                    "status": records.status,
                    "locked": records.locked,
                    "issued": records.issued,
                    "data": records.data,
                }
            }

            context.update(
                {
                    "result": pd_data,
                    "isAdmin": is_admin(req.user),
                }
            )

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=id, user=req.user, exception=e
                )
            )

            context["error"] = DEFAULT_ERROR

        return render(req, "Table/HTMX/sem.refresh.html", context=context)

@htmx_response
@auth_needed(admin_only=True)
@semester_permission_check
def edit_form(req: HttpRequest, id: int, idx: int, rowID: int) -> HttpResponse:
    if is_hx_put(req):
        body = QueryDict(req.body)
        column: str = body.get("column", "")
        value: str = body.get("value", "")

        context = {"id": id, "idx": idx, "rowID": rowID,"column": column, "locked": False, "value": ""}

        try:
            column = bytes.fromhex(column).decode()

            if column[-1:] == "I":
                raise OnlyTextAllowed(column[:-1])

            locked, exists, value = DataTable.getColumnValue(id, idx, rowID ,column)

            if not exists:
                raise ColumnDoesNotExist(idx, column[:-1])

            context["locked"] = locked
            context["value"] = value

            if locked:
                raise RowLocked(idx)

        except ColumnDoesNotExist as f:
            messages.error(req, f.get_error())

        except RowLocked as a:
            messages.error(req, a.get_error())

        except OnlyTextAllowed as g:
            messages.error(req, g.get_error())

        except ValueError:
            messages.error(req, "Invalid Column Name detected! Request Aborted")

        return render(req, "Table/HTMX/edit/edit_form.html", context=context)

    elif is_hx_get(req):
        column = req.GET.get("column", "")

        context = {
            "id": id,
            "idx": idx,
            "rowID": rowID,
            "column": column,
            "locked": False,
            "value": "Data Not Found",
        }

        try:
            column = bytes.fromhex(column).decode()
            if column[-1] == "I":
                raise OnlyTextAllowed(column[:-1])

            locked, exists, value = DataTable.getColumnValue(id, idx, rowID, column)

            if not exists:
                raise ColumnDoesNotExist(idx, column[:-1])

            context["locked"] = locked
            context["value"] = value

        except ColumnDoesNotExist as f:
            messages.error(req, f.get_error())
        except OnlyTextAllowed as g:
            messages.error(req, g.get_error())
        except ValueError:
            messages.error(req, "Invalid Column Name detected! Request Aborted")
        except Exception as e:
            print(e)
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Table/HTMX/normal/normal.html", context=context)

    elif is_hx_post(req):
        column = req.POST.get("column", "")
        value = req.POST.get("value", "")

        context = {"id": id, "idx": idx, "rowID": rowID,"updated": False, "column": column}
        try:
            column = bytes.fromhex(column).decode()

            if column[-1:] == "I":
                raise OnlyTextAllowed(column[:-1])

            updated = DataTable.setColumnValue(id, idx, rowID, column, json.dumps({column: value}))

            context["updated"] = updated

            if updated:
                messages.success(
                    req,
                    f"Column '{column[:-1]}' of Row ID: '{rowID}' was successfully updated",
                )
            else:
                messages.error(
                    req, f"Updating Column '{column[:-1]}' of Row ID: '{rowID}' failed!"
                )

        except OnlyTextAllowed as g:
            messages.error(req, g.get_error())

        except RowLocked as f:
            messages.error(req, f.get_error())

        except ValueError:
            messages.error(req, "Invalid Column Name detected! Request Aborted")

        return render(req, "Table/HTMX/update/text.html", context=context)

@htmx_response
@auth_needed(admin_only=True)
@semester_permission_check
def edit_image_form(req: HttpRequest, id: int, idx: int, rowID: int) -> HttpResponse:
    if is_hx_put(req):
        column: str = QueryDict(req.body).get("column", "")

        context = {
            "id": id,
            "idx": idx,
            "rowID": rowID,
            "column": column,
            "locked": False,
        }

        try:
            column = bytes.fromhex(column).decode()

            if column[-1:] != "I":
                raise OnlyImageAllowed(column[:-1])

            locked, exists, value = DataTable.getColumnValue(id, idx, rowID, column)

            if not exists:
                raise ColumnDoesNotExist(idx, column[:-1])

            context["locked"] = locked

            if locked:
                raise RowLocked(idx)

        except ColumnDoesNotExist as f:
            messages.error(req, f.get_error())

        except RowLocked as a:
            messages.error(req, a.get_error())

        except OnlyImageAllowed as g:
            messages.error(req, g.get_error())

        except ValueError:
            messages.error(req, "Invalid Column Name detected! Request Aborted")

        return render(req, "Table/HTMX/edit/edit_image_form.html", context=context)

    elif is_hx_get(req):
        column = req.GET.get("column", "")

        context = {
            "id": id,
            "idx": idx,
            "rowID": rowID,
            "column": column,
            "locked": False,
            "value": "Data Not Found",
        }

        try:
            column = bytes.fromhex(column).decode()

            if column[-1:] != "I":
                raise OnlyImageAllowed(column[:-1])

            locked, exists, value = DataTable.getColumnValue(id, idx, rowID, column)

            if not exists:
                raise ColumnDoesNotExist(idx, column[:-1])

            context["locked"] = locked
            context["value"] = value

        except ColumnDoesNotExist as f:
            messages.error(req, f.get_error())
        except OnlyImageAllowed as g:
            messages.error(req, g.get_error())
        except ValueError:
            messages.error(req, "Invalid Column Name detected! Request Aborted")
        except Exception as e:
            print(e)
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Table/HTMX/normal/normal_image.html", context=context)

    elif is_hx_post(req):
        column = req.POST.get("column", "")

        context = {"id": id, "idx": idx, "rowID": rowID, "updated": False, "column": column}
        try:
            image = req.FILES["file"]
            column = bytes.fromhex(column).decode()

            if column[-1:] != "I":
                raise OnlyImageAllowed(column[:-1])

            with image.open() as img, BytesIO() as b:
                IMAGE = Image.open(img)

                IMAGE.save(b, IMAGE.format, quality=95)

                value = (
                    f"{IMAGE.width}:{IMAGE.height}:{b64encode(b.getvalue()).decode()}"
                )

                updated = DataTable.setColumnValue(id, idx, rowID, column, json.dumps({column: value}))

                context["updated"] = updated

            if updated:
                messages.success(
                    req,
                    f"Column '{column[:-1]}' of Row ID: '{rowID}' was successfully updated",
                )
            else:
                messages.error(
                    req, f"Updating Column '{column[:-1]}' of Row ID: '{rowID}' failed!"
                )

        except OnlyImageAllowed as g:
            messages.error(req, g.get_error())

        except RowLocked as f:
            messages.error(req, f.get_error())

        except ValueError:
            messages.error(req, "Invalid Column Name detected! Request Aborted")

        except UnidentifiedImageError:
            messages.error(req, "Invalid Image Uploaded! Request Aborted")

        return render(req, "Table/HTMX/update/image.html", context=context)

@htmx_response
@auth_needed()
@task_permission_check
def column_view(req: HttpRequest, id: int) -> HttpResponse | None:
    if is_hx_get(req):
        context = {"search": [], "column": [], "count": 0}

        try:
            count, (images, text) = DataTable.get_all_columns(id)

            context["search"] = text
            context["column"] = text + images
            context["count"] = count

        except Exception as e:
            print(e)
            messages.error(req, DEFAULT_ERROR)
        
        return render(req, "Table/HTMX/column.html", context=context)

    return None

@htmx_response
@auth_needed()
@task_permission_check
def complete_row_view(req: HttpRequest, id: int) -> HttpResponse:
    if is_hx_get(req):
        column = req.GET.get("column", "")
        value = req.GET.get("search", "")
        issue = req.GET.get("issue", "")
        status = req.GET.get("status", "")
        lock = req.GET.get("lock", "")
        user = get_user(req)
        try:
            page = int(req.GET.get("page", "0"))
        except Exception as e:
            page = 0
            
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )
        context = get_context(req, id, column, value ,issue ,status ,lock, page)

        return render(req, "Table/HTMX/row.html", context=context)

    return HttpResponse(status=403)

@htmx_response
@auth_needed()
@task_permission_check
def refresh_row(req: HttpRequest, id: int, idx: str) -> HttpResponse:
    if is_hx_get(req):
        context = get_row_context(req, id, idx)

        return render(req, "Table/HTMX/refresh.html", context=context)

    return HttpResponse(status=403)

@htmx_response
@auth_needed()
@task_permission_check
def suggest_view(req: HttpRequest, id: int) -> HttpResponse:
    if is_hx_get(req):
        column = req.GET.get("column", "")
        value = req.GET.get("search", "")
        context: dict[str, list[str] | int] = {"id": id, "option": []}

        try:
            column = bytes.fromhex(column).decode()
            suggestions = DataTable.suggestAllValues(id, column, value)
            context["option"] = suggestions

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=id, user=req.user, exception=e
                )
            )

        return render(req, "Table/HTMX/suggests.html", context=context)

