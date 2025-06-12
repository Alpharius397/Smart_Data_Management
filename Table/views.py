from io import BytesIO
from typing import Any, NamedTuple
import typing
from django.contrib import messages  # type: ignore
from django.db.models import Q  # type: ignore
from PIL import Image, UnidentifiedImageError  # type: ignore
from django.shortcuts import render  # type: ignore
from django.http import HttpRequest, HttpResponse  # type: ignore
from Task.models import DataTable, AssignTable, TaskTable, UploadTable
from User.models import (
    RoleType,
    get_user,
    is_admin,
    is_manager,
    User,
)
from tools.url_auth import (
    file_permission_check,
    task_permission_check,
    semester_permission_check,
    get_color,
    htmx_response,
    is_auth_get,
    is_hx_delete,
    is_hx_get,
    is_hx_post,
    is_hx_put,
    auth_needed,
    login_needed,
)
from Table.errors import (
    ColumnDoesNotExist,
    ManagerAlreadyAssigned,
    ManagerDoesNotExist,
    OnlyImageAllowed,
    OnlyTextAllowed,
    RowLocked,
)
from Logs.loggers import APP_LOG, LogStructure, Task
from tools.utils import ColumnType, segregateColumns
from django.http import QueryDict
from constants.constants import DEFAULT_ERROR, MAX_RECORD
from Main.models import *
from psycopg2.sql import SQL, Identifier, Literal, Composable  # type: ignore
from tools.get_image import b64encode
from django.db import connection  # type: ignore


############ TYPES ############
class ManagerList(NamedTuple):
    id: int
    username: str


############ UTILS ############
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

        for col in cursor.fetchall():
            columns.append(col[0])
            count += 1

    return count, segregateColumns(columns)

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
                select distinct jsonb_object_keys("A"."data"::jsonb) as "data" from (select "semester", MAX({data_column}::varchar) as "data" from {table_name} where {taskID_column}={taskID} group by {semester_column}) as "A" order by "data";
                """
            ).format(
                data_column=data_column,
                table_name=table_name,
                taskID_column=taskID_column,
                semester_column=semester_column,
                taskID=taskID,
            )
        

        cursor.execute(sql_query)

        for col in cursor.fetchall():
            columns.append(col[0])
            count += 1

    return count, segregateColumns(columns)

def get_2_value(value: typing.Literal['true', 'false']) -> bool:
    assert value in [
        "true",
        "false",
    ], f"Invalid Boolean Type. Value '{value}' not in ['true', 'false']"

    if value == "true":
        return True
    else:
        return False

def get_3_value(value: typing.Literal['true', 'false', 'none']) -> bool | None:
    assert value in [
        "true",
        "false",
        "none",
    ], f"Invalid Nullable Boolean Type. Value '{value}' not in ['true', 'false', 'none']"

    if value == "true":
        return True
    elif value == "none":
        return None
    else:
        return False


def get_sem_context(
    req: HttpRequest, 
    id: int,
    idx: int,
    column: str = "",
    value: str = "",
    issue: str = "",
    status: str = "",
    lock: str = "",
    page: str = "0",
) -> dict[str, str | bool | None]:
    
    context: dict[str, Any] = {"id": id, "idx": idx}
    search = False
    user = get_user(req)
    column_list: ColumnType = ColumnType([], [])
    task: TaskTable = req.__getattribute__("task")

    try:
        _page: int = int(page)
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

        records = task.data.filter(query).order_by("id")[_page : _page + MAX_RECORD]

        _, column_list = get_columns(id, idx)

        columns: list = column_list.text
        image_idx: list = column_list.images

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

        if empty:  # no buffer left
            context["empty"] = True

        if searching and (_page == 0) and empty:
            context["error"] = "No Matching Records Found"

        context.update(
            {
                "result": pd_data,
                "images": image_idx,
                "columns": columns,
                "start": _page,
                "max_record": _page + MAX_RECORD,
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
            count, (images, text) = get_columns(id, idx)

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
    if is_hx_get(req):
        column = req.GET.get("column", "")
        value = req.GET.get("search", "")
        issue = req.GET.get("issue", "")
        status = req.GET.get("status", "")
        lock = req.GET.get("lock", "")
        page = req.GET.get("page", "0")

        context = get_sem_context(req, id, idx, column, value, issue, status, lock, page)
        context.update({"admin": is_admin(get_user(req))})

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

            _, column_list = get_columns(id, idx)

            columns: list = column_list.text
            image_idx: list = column_list.images

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
                    "images": image_idx,
                    "columns": columns,
                    "admin": is_admin(req.user),
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


class UpdateStatus(NamedTuple):
    updated: bool
    exists: bool
    locked: bool


@htmx_response
@auth_needed(admin_only=True)
@semester_permission_check
def edit_form(req: HttpRequest, id: int, idx: int, rowID: int) -> HttpResponse:
    if is_hx_put(req):
        body = QueryDict(req.body)
        column = body.get("column", "")
        value = body.get("value", "")

        context = {"id": id, "idx": idx, "rowID": rowID,"column": column, "locked": False, "value": ""}

        try:
            _column = bytes.fromhex(column).decode()

            if _column[-1:] == "I":
                raise OnlyTextAllowed(_column[:-1])

            locked, exists, value = DataTable.getColumnValue(id, idx, rowID ,_column)

            if not exists:
                raise ColumnDoesNotExist(idx, _column[:-1])

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
        column: str = req.GET.get("column", "")

        context = {
            "id": id,
            "idx": idx,
            "rowID": rowID,
            "column": column,
            "locked": False,
            "value": "Data Not Found",
        }

        try:
            _column = bytes.fromhex(column).decode()
            if _column[-1] == "I":
                raise OnlyTextAllowed(_column[:-1])

            locked, exists, value = DataTable.getColumnValue(id, idx, rowID, _column)

            if not exists:
                raise ColumnDoesNotExist(idx, _column[:-1])

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
        column: str = req.POST.get("column", "")
        value: str = req.POST.get("value", "")

        context = {"id": id, "idx": idx, "rowID": rowID,"updated": False, "column": column}
        try:
            _column = bytes.fromhex(column).decode()

            if _column[-1:] == "I":
                raise OnlyTextAllowed(_column[:-1])

            updated = DataTable.setColumnValue(id, idx, rowID, _column, json.dumps({_column: value}))

            context["updated"] = updated

            if updated:
                messages.success(
                    req,
                    f"Column '{_column[:-1]}' of Row ID: '{rowID}' was successfully updated",
                )
            else:
                messages.error(
                    req, f"Updating Column '{_column[:-1]}' of Row ID: '{rowID}' failed!"
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
        column = QueryDict(req.body).get("column", "")

        context = {
            "id": id,
            "idx": idx,
            "rowID": rowID,
            "column": column,
            "locked": False,
        }

        try:
            _column = bytes.fromhex(column).decode()

            if _column[-1:] != "I":
                raise OnlyImageAllowed(_column[:-1])

            locked, exists, value = DataTable.getColumnValue(id, idx, rowID, _column)

            if not exists:
                raise ColumnDoesNotExist(idx, _column[:-1])

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
        column: str = req.GET.get("column", "")

        context = {
            "id": id,
            "idx": idx,
            "rowID": rowID,
            "column": column,
            "locked": False,
            "value": "Data Not Found",
        }

        try:
            _column = bytes.fromhex(column).decode()

            if _column[-1:] != "I":
                raise OnlyImageAllowed(_column[:-1])

            locked, exists, value = DataTable.getColumnValue(id, idx, rowID, _column)

            if not exists:
                raise ColumnDoesNotExist(idx, _column[:-1])

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
        column: str = req.POST.get("column", "")

        context = {"id": id, "idx": idx, "rowID": rowID, "updated": False, "column": column}
        try:
            image = req.FILES["file"]
            _column = bytes.fromhex(column).decode()

            if _column[-1:] != "I":
                raise OnlyImageAllowed(_column[:-1])

            with image.open() as img, BytesIO() as b:
                IMAGE = Image.open(img)

                IMAGE.save(b, IMAGE.format, quality=95)

                value = (
                    f"{IMAGE.width}:{IMAGE.height}:{b64encode(b.getvalue()).decode()}"
                )

                updated = DataTable.setColumnValue(id, idx, rowID, _column, json.dumps({_column: value}))

                context["updated"] = updated

            if updated:
                messages.success(
                    req,
                    f"Column '{_column[:-1]}' of Row ID: '{rowID}' was successfully updated",
                )
            else:
                messages.error(
                    req, f"Updating Column '{_column[:-1]}' of Row ID: '{rowID}' failed!"
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

# select "A"."id",jsonsum("A"."data") from (select distinct data::jsonb->>'IDT' as "id", data::jsonb as "data" from "Task_datatable" where "taskID_id"=1) as "A" group by "A"."id" order by length("A"."id"), "A"."id" limit 1;

def boolSQL(value: bool | None):
    match(value):
        case True: return 'true'
        case False: return 'false'
        case None: return 'null'
        case _: raise ValueError(f"'value' should be of type bool or None. Got: {type(value)}")

class Context(NamedTuple):
    ID: str
    data: str
    locked: bool 
    issued: bool
    status: bool
    
    
def get_context(req: HttpRequest, id: int, column: str = "", locked: str = "", status: str = "", issued: str = "" ,value: str = "", page: str = "0"):
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
        _page = int(page)
        groupBy = Literal(task.groupByColumn)
        page = Literal(_page)
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
            sql_query = SQL('select * from (select {data_column}::jsonb ->>{groupBy} as "ID", jsonsum({data_column}::jsonb)::jsonb as "data", bool_and({locked_column}) as "locked", bool_and({issued_column}) as "issued", bool_and({status_column}) as "status" from {table_name} where {taskID_column}={taskID} group by "ID" order by length({data_column}::jsonb ->>{groupBy}), {data_column}::jsonb ->>{groupBy}) as "A" where {searchQuery} limit 5 offset {page};').format(
                data_column=data_column,
                groupBy=groupBy,
                locked_column=locked_column,
                issued_column=issued_column,
                status_column=status_column,
                table_name=table_name,
                taskID_column=taskID_column,
                searchQuery=searchQuery,
                taskID=taskID,
                page=page,
            ).as_string(cursor.connection)
            print(sql_query)
            cursor.execute(sql_query)
            
            records = [Context(*col) for col in cursor.fetchall()]
            
        _, column_list = get_all_columns(id)

        columns: list = column_list.text
        image_idx: list = column_list.images

        pd_data = {
            (row.ID): {
                "status": row.status,
                "locked": row.locked,
                "issued": row.issued,
                "data": json.loads(row.data),
            }
            for row in records
        }

        empty = not bool(pd_data)

        if empty:  # no buffer left
            context["empty"] = True

        if searching and (_page == 0) and empty:
            context["error"] = "No Matching Records Found"

        context.update(
            {
                "result": pd_data,
                "images": image_idx,
                "columns": columns,
                "start": _page,
                "max_record": _page + MAX_RECORD,
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


    return context

@htmx_response
@auth_needed()
@task_permission_check
def column_view(req: HttpRequest, id: int) -> HttpResponse | None:
    if is_hx_get(req):
        context = {"search": [], "column": [], "count": 0}

        try:
            count, (images, text) = get_all_columns(id)

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
@task_permission_check
def complete_row_view(req: HttpRequest, id: int) -> HttpResponse:
    if is_hx_get(req):
        column = req.GET.get("column", "")
        value = req.GET.get("search", "")
        issue = req.GET.get("issue", "")
        status = req.GET.get("status", "")
        lock = req.GET.get("lock", "")
        page = req.GET.get("page", "0")
        context = get_context(req, id, column, lock, status, issue,value, page)
        context.update({"admin": is_admin(get_user(req))})

        return render(req, "Table/HTMX/row.html", context=context)

    return HttpResponse(status=403)