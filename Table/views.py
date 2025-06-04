from io import BytesIO
from typing import Any
from django.contrib import messages
from django.db.models import Q
from PIL import Image, UnidentifiedImageError
from django.shortcuts import render  # type: ignore
from django.http import HttpRequest, HttpResponse  # type: ignore
from Upload.models import DataTable, AssignTable, UploadTable
from User.models import (
    RoleType,
    get_user,
    is_admin,
    is_manager,
    User,
)
from tools.url_auth import (
    file_permission_check,
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
from Table.errors import ColumnDoesNotExist, ManagerAlreadyAssigned, ManagerDoesNotExist, OnlyImageAllowed, OnlyTextAllowed, RowLocked
from Logs.loggers import APP_LOG, LogStructure, Task
from tools.utils import ColumnType, segregateColumns
from django.http import QueryDict
from constants.constants import DEFAULT_ERROR, MAX_RECORD
from Main.models import *
from psycopg2.sql import SQL, Identifier, Literal
from django.db import connection
from tools.get_image import b64encode

############ TYPES ############
class ManagerList(NamedTuple):
    id: int
    username: str
    
############ UTILS ############
def get_columns(ID: int) -> tuple[int, ColumnType]:
    columns: list[str] = []
    table_name = Identifier(DataTable.objects.model._meta.db_table)
    data_column = Identifier(DataTable.data.field.column)  # type: ignore
    fileID_column = Identifier(DataTable.fileID.field.column)  # type: ignore
    fileID = Literal(ID)

    columns: list[str] = []
    count: int = 0

    with connection.cursor() as cursor:
        sql_query = SQL(
            'select "A"."option" as "option" from (select distinct(jsonb_object_keys({data})) as "option" from {table} where {file}={fileID}) as "A" order by length("A"."option"), "A"."option";'
        )
        sql_query = sql_query.format(
            data=data_column, table=table_name, file=fileID_column, fileID=fileID
        )
        sql_query = sql_query.as_string(connection.connection)

        cursor.execute(sql_query)

        for col in cursor.fetchall():
            columns.append(col[0])
            count += 1
    return count, segregateColumns(columns)


def get_2_value(value: str) -> bool:
    assert value in [
        "true",
        "false",
    ], f"Invalid Boolean Type. Value '{value}' not in ['true', 'false']"

    if value == "true":
        return True
    else:
        return False


def get_3_value(value: str) -> bool | None:
    assert value in [
        "true",
        "false",
        "none",
    ], (
        f"Invalid Nullable Boolean Type. Value '{value}' not in ['true', 'false', 'none']"
    )

    if value == "true":
        return True
    elif value == "none":
        return None
    else:
        return False
    
def get_context(
    req: HttpRequest,
    id: int,
    column: str = "",
    value: str = "",
    issue: str = "",
    status: str = "",
    lock: str = "",
    page: str = "0",
) -> dict[str, str | bool | None]:
    context: dict[str, Any] = {"id": id}
    search = False
    user = get_user(req)
    column_list: ColumnType = ColumnType([], [], [])

    try:
        _page: int = int(page)

        query = Q(fileID__id=id) & (
            Q(fileID__uploader__role__belongs__id=user.role.belongs.id) | Q(fileID__assigned__manager__id=user.id)
        )

        searching = status or issue or lock or (column and value)

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

        records = DataTable.objects.filter(query).order_by("id")[
            _page : _page + MAX_RECORD
        ]

        _, column_list = get_columns(id)

        columns: list = column_list.semester + column_list.personal
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

    if search:
        context["error"] = "No matching records found"
    else:
        context.update(
            {
                "result": pd_data,
                "images": image_idx,
                "columns": columns,
                "start": _page,
                "max_record": _page + MAX_RECORD,
            }
        )

    return context

def getAssignForm(req: HttpRequest, id: int) -> dict[str, list[ManagerList] | str]:
    context: dict[str, list[ManagerList] | str] = {"uploader": "", "manager": [], "all_managers": []}

    try:
        user = get_user(req)

        fileObj = UploadTable.objects.get(id=id, uploader__role__belongs__id = user.role.belongs.id)

        uploader = fileObj.uploader.username
        managers: list[ManagerList] = fileObj.assigned.distinct().values_list(
            "manager__id", "manager__username"
        )
        all_managers: list[ManagerList] = (
            User.objects.filter(
                role__role=RoleType.MANAGER, role__belongs__id=user.role.belongs.id
            )
            .exclude(id__in=[i[0] for i in managers])
            .distinct()
            .values_list("id", "username")
        )

        context["uploader"] = uploader
        context["managers"] = all_managers
        context["all_managers"] = managers

    except Exception:
        pass

    return context

########### HTTP Request #############
@login_needed()
@file_permission_check
def default_view(req: HttpRequest, id: int) -> HttpResponse | None:
    user = get_user(req)

    if is_auth_get(req):
        get_color(req)
        
        if is_admin(user):
            return render(req, "Table/table/admin.html", {"id": id})

        elif is_manager(user):
            return render(req, "Table/table/manager.html", {"id": id})

    return None


############ HTMX Request ############
@htmx_response
@auth_needed()
@file_permission_check
def column_view(req: HttpRequest, id: int) -> HttpResponse | None:
    if is_hx_get(req):
        context = {"search": [], "column": [], "count": 0}

        try:
            count, (images, personal, semester) = get_columns(id)

            personal.extend(semester)

            context["search"] = personal.copy()

            personal.extend(images)

            context["column"] = personal
            context["count"] = count

        except Exception as e:
            print(e)

            messages.error(req, DEFAULT_ERROR)
        return render(req, "Table/HTMX/column.html", context=context)

    return None

@htmx_response
@auth_needed(admin_only=True)
@file_permission_check
def assign_form(req: HttpRequest, id: int) -> HttpResponse | None:
    context: dict[str, Any] = {"id": id}
    user = get_user(req)

    if is_hx_get(req):
        try:
            context.update(getAssignForm(req, id))

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )

            context["error"] = DEFAULT_ERROR

        return render(req, "Table/HTMX/form.html", context=context)

    elif is_hx_put(req):
        value = QueryDict(req.body)  # type: ignore

        managerID = value.get("user", "")

        try:
            manager = User.objects.get(id=managerID)

            fileObj = UploadTable.objects.get(id=id, uploader=user)

            assignFlag = fileObj.assigned.filter(manager__id=managerID).exists()  # type: ignore

            if assignFlag:
                raise ManagerAlreadyAssigned(managerID, id)

            assignee = AssignTable(fileID=fileObj, manager=manager)
            assignee.save()

            context.update(getAssignForm(req, id))
            messages.success(
                req, f"Manager ID: {managerID} is added to the Task ID: {id}"
            )

        except User.DoesNotExist:
            messages.error(req, "Manager ID: {managerID} does not exists!")

        except ManagerAlreadyAssigned as f:
            messages.error(req, f.get_error())

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )

            messages.error(req, DEFAULT_ERROR)

        return render(req, "Table/HTMX/form.html", context=context)

    elif is_hx_delete(req):
        value = req.GET  # type: ignore

        managerID = value.get("user", "")

        try:
            manager = User.objects.get(id=managerID)

            fileObj = UploadTable.objects.get(id=id, uploader=user)

            notassignFlag = fileObj.assigned.filter(manager__id=managerID).exists()  # type: ignore

            if not notassignFlag:
                raise ManagerDoesNotExist(managerID, id)

            assignee = AssignTable.objects.get(fileID=fileObj, manager=manager)
            assignee.delete()

            context.update(getAssignForm(req, id))
            messages.success(
                req, f"Manager ID: {managerID} is removed from Task ID: {id}"
            )
        except User.DoesNotExist:
            messages.error(req, "Manager ID: {managerID} does not exists!")

        except ManagerDoesNotExist as f:
            messages.error(req, f.get_error())

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=str(id), user=user, exception=e
                )
            )

            messages.error(req, DEFAULT_ERROR)

        return render(req, "Table/HTMX/form.html", context=context)
    
    return None


@htmx_response
@auth_needed()
@file_permission_check
def row_view(req: HttpRequest, id: int) -> HttpResponse:
    if is_hx_get(req):
        column = req.GET.get("column", "")
        value = req.GET.get("search", "")
        issue = req.GET.get("issue", "")
        status = req.GET.get("status", "")
        lock = req.GET.get("lock", "")
        page = req.GET.get("page", "0")

        context = get_context(req, id, column, value, issue, status, lock, page)
        context.update({"admin": is_admin(get_user(req))})

        return render(req, "Table/HTMX/row.html", context=context)

    return HttpResponse(status=403)


@htmx_response
@auth_needed()
@file_permission_check
def quick_query(req: HttpRequest, id: int):
    if is_hx_get(req):
        column = req.GET.get("column", "")
        value = req.GET.get("search", "")
        context: dict[str, list[str]] = {"option": []}

        try:
            column_name = Literal(column)
            table_name = Identifier(DataTable.objects.model._meta.db_table)
            _value = Literal(f"%{value}%")
            file_column = Identifier(DataTable.fileID.field.column)
            fileID = Literal(id)
            data_column = Identifier(DataTable.data.field.column)
            
            with connection.cursor() as cursor:
                sql_query = SQL('select "A"."option" from (select distinct {data}::json ->> {column} as "option" from {table} where {file_column}={fileID} and {data}::json ->> {column} is not null and {data}::json ->> {column} like {value}) as "A" order by length("A"."option"), "A"."option" limit 5')
                sql_query = sql_query.format(data=data_column, column=column_name, table=table_name, file_column=file_column, fileID=fileID, value=_value)
                sql_query = sql_query.as_string(connection.connection)
                
                cursor.execute(sql_query)
                
                suggestions = [col[0] for col in cursor.fetchall() if bool(col)]
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
@file_permission_check
def refresh_row(req: HttpRequest, id: int, idx: int) -> HttpResponse:
    if is_hx_get(req):
        context: dict[str, Any] = {"id": id, "idx": idx}

        try:
            records = DataTable.objects.get(fileID__id = id, id = idx)

            _, column_list = get_columns(id)

            columns: list = column_list.semester + column_list.personal
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

        return render(req, "Table/HTMX/refresh.html", context=context)

class RowStatus(NamedTuple):
    locked: bool
    exists: bool
    value: str
    
    def __iter__(self):
        yield self.locked
        yield self.exists
        yield self.value

def getColumnValue(id: int, idx: int, column: str) -> RowStatus:
    
    value = RowStatus(True, False, "")
    try:
        
        column = Literal(column)
        table_name = Identifier(DataTable.objects.model._meta.db_table)
        rowID = Literal(idx)
        fileID = Literal(id)
        rowColumn = Identifier(DataTable.data.field.column)
        fileColumn = Identifier(DataTable.fileID.field.column)
        
        with connection.cursor() as cursor:
            sql_query = SQL('select "locked", {data_column}::jsonb?{column} ,{data_column}::json ->> {column} from {table} where {file}={fileID} and "id"={rowID} limit 1;')
            sql_query = sql_query.format(data_column=rowColumn, column=column, table=table_name, file=fileColumn, fileID=fileID, rowID=rowID)
            sql_query = sql_query.as_string(connection.connection)
            
            cursor.execute(sql_query)
            
            value = cursor.fetchone() or value
        
        return value
        
    except Exception as e:
        print(e)
        pass
    
    return value

class UpdateStatus(NamedTuple):
    updated: bool
    exists: bool
    locked: bool

def setColumnValue(id: int, idx: int, column: str, value: str) -> bool:
    result = False
    
    try:
        
        dicts:dict = json.loads(value)
        
        if (column not in dicts) or (len(dicts.keys())>1) :
            raise ValueError("Invalid values detected")
        
        _column = Literal(column)
        table_name = Identifier(DataTable.objects.model._meta.db_table)
        rowID = Literal(idx)
        fileID = Literal(id)
        rowColumn = Identifier(DataTable.data.field.column)
        fileColumn = Identifier(DataTable.fileID.field.column)
        locked = Identifier(DataTable.locked.field.column)
        _value = Literal(value)
        
        with connection.cursor() as cursor:
            sql_query = SQL("""update {table} set {data_column} = {data_column}::jsonb || {value}::jsonb 
                                where {fileColumn} = {fileID} and "id" = {rowID} and {data_column}::jsonb?{column} and {locked} is false;
                            """)
            
            sql_query = sql_query.format(table=table_name, data_column=rowColumn, value=_value, fileColumn=fileColumn, fileID=fileID, rowID=rowID, column=_column, locked=locked)
            sql_query = sql_query.as_string(cursor.connection)
        
            cursor.execute(sql_query)
            result = (cursor.rowcount==1) or result
        
    except Exception as e:
        pass
    
    return result

@htmx_response
@auth_needed(admin_only=True)
@file_permission_check
def edit_form(req: HttpRequest, id: int, idx: int) -> HttpResponse:
    if is_hx_put(req):
        body = QueryDict(req.body)
        column = body.get("column", "")
        value = body.get("value", "")
        
        context = {"id": id, "idx": idx, "column": column, "locked": False, "value": ""}
        
        try:
            _column = bytes.fromhex(column).decode()
            
            if _column[-2:] == 'II':
                raise OnlyTextAllowed(_column[:-2])
            
            locked, exists, value = getColumnValue(id,idx,_column)
            
            if(not exists):
                raise ColumnDoesNotExist(idx,_column[:-2])
            
            context["locked"] = locked
            context["value"] = value
            
            if (locked):
                raise RowLocked(idx)
        
        except ColumnDoesNotExist as f:
            messages.error(req, f.get_error())
            
        except RowLocked as a:
            messages.error(req, a.get_error())
            
        except OnlyTextAllowed as g:
            messages.error(req, g.get_error())
            
        except ValueError:
            messages.error(req, "Invalid Column Name detected! Request Aborted")
            
        return render(
            req,
            "Table/HTMX/edit/edit_form.html",
            context=context
        )

    elif is_hx_get(req):
        column: str = req.GET.get("column", "")

        context = {"id": id, "idx": idx, "column": column, "locked": False, "value": "Data Not Found"}

        try:
            _column = bytes.fromhex(column).decode()
            if _column[-2:] == 'II':
                raise OnlyTextAllowed(_column[:-2])
            
            locked, exists, value = getColumnValue(id,idx,_column)
            
            if(not exists):
                raise ColumnDoesNotExist(idx,_column[:-2])
            
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
        
        context = {"id": id, "idx": idx, "updated": False, "column": column}
        try:
            _column = bytes.fromhex(column).decode()
            
            if _column[-2:] == 'II':
                raise OnlyTextAllowed(_column[:-2])
            
            updated = setColumnValue(id, idx, _column, json.dumps({_column: value}))
    
            
            context["updated"] = updated
            
            if (updated):
                messages.success(req, f"Column '{_column[:-2]}' of Row ID: '{idx}' was successfully updated")
            else:
                messages.error(req, f"Updating Column '{_column[:-2]}' of Row ID: '{idx}' failed!")
        
        except OnlyTextAllowed as g:
            messages.error(req, g.get_error())
            
        except RowLocked as f:
            messages.error(req, f.get_error())
            
        except ValueError:
            messages.error(req, "Invalid Column Name detected! Request Aborted")
            
        return render(req, "Table/HTMX/update/text.html", context=context)


@htmx_response
@auth_needed(admin_only=True)
@file_permission_check
def edit_image_form(req: HttpRequest, id: int, idx: int) -> HttpResponse:
    if is_hx_put(req):
        column = QueryDict(req.body).get("column", "")
        
        context = {"id": id, "idx": idx, "column": column, "locked": False,}
        
        try:
            _column = bytes.fromhex(column).decode()
            
            if _column[-2:] != 'II':
                raise OnlyImageAllowed(_column[:-2])
            
            locked, exists, value = getColumnValue(id,idx,_column)
            
            if(not exists):
                raise ColumnDoesNotExist(idx,_column[:-2])
            
            context["locked"] = locked
            
            if (locked):
                raise RowLocked(idx)
        
        except ColumnDoesNotExist as f:
            messages.error(req, f.get_error())
            
        except RowLocked as a:
            messages.error(req, a.get_error())
            
        except OnlyImageAllowed as g:
            messages.error(req, g.get_error())
            
        except ValueError:
            messages.error(req, "Invalid Column Name detected! Request Aborted")
            
        return render(
            req,
            "Table/HTMX/edit/edit_image_form.html",
            context=context
        )

    elif is_hx_get(req):
        column: str = req.GET.get("column", "")

        context = {"id": id, "idx": idx, "column": column, "locked": False, "value": "Data Not Found"}

        try:
            _column = bytes.fromhex(column).decode()
            
            if _column[-2:] != 'II':
                raise OnlyImageAllowed(_column[:-2])
            
            locked, exists, value = getColumnValue(id,idx,_column)
            
            if(not exists):
                raise ColumnDoesNotExist(idx,_column[:-2])
            
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
        
        context = {"id": id, "idx": idx, "updated": False, "column": column}
        try:
            image = req.FILES["file"]
            _column = bytes.fromhex(column).decode()
            
            if _column[-2:] != 'II':
                raise OnlyImageAllowed(_column[:-2])
            
            
            with image.open() as img, BytesIO() as b:
                IMAGE = Image.open(img)
                
                IMAGE.save(b, IMAGE.format, quality=95)
                
                value = f"{IMAGE.width}:{IMAGE.height}:{b64encode(b.getvalue()).decode()}"
            
                updated = setColumnValue(id, idx, _column, json.dumps({_column: value}))
            
                context["updated"] = updated
            
            if (updated):
                messages.success(req, f"Column '{_column[:-2]}' of Row ID: '{idx}' was successfully updated")
            else:
                messages.error(req, f"Updating Column '{_column[:-2]}' of Row ID: '{idx}' failed!")
        
        except OnlyImageAllowed as g:
            messages.error(req, g.get_error())
            
        except RowLocked as f:
            messages.error(req, f.get_error())
            
        except ValueError:
            messages.error(req, "Invalid Column Name detected! Request Aborted")
        
        except UnidentifiedImageError:
            messages.error(req, "Invalid Image Uploaded! Request Aborted")
            
        return render(req, "Table/HTMX/update/image.html", context=context)