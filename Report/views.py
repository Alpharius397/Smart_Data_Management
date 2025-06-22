from base64 import b64decode, b64encode
import functools
from io import BytesIO
import json
from PIL import Image
from typing import Any, NamedTuple
import typing
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render  # type: ignore
from django.urls import reverse  # type: ignore
from django.http import HttpRequest, HttpResponse, JsonResponse, FileResponse  # type: ignore
from Report.errors import DataNotLocked, InvalidSchema, RedisFailed
from University.models import Subject, Schema
from Task.models import DataTable, TaskTable
from Main.settings import settingsInterface as settings
from tools.get_image import compress_image
from User.models import (
    get_post_id,
    get_user,
    is_admin,
    is_manager,
    get_post,
    get_user_by_id,
    get_post_by_ID,
    User,
)
import pandas as pd
from tools.encrypt import encrypt_data, decrypt_data
from Main.templatetags.bad_image import bad_image
from tools.url_auth import (
    file_permission_check,
    get_color,
    htmx_response,
    is_auth_get,
    is_auth_post,
    is_hx_delete,
    is_hx_get,
    is_hx_post,
    is_hx_put,
    login_needed,
    api_key_required,
    auth_needed,
    semester_permission_check,
    task_permission_check,
)
from Report.forms import CompleteFeedBack, FeedBackForm, FeedBackView, CompleteFeedBackView
from django.utils import timezone  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, Task
from tools.utils import ColumnType, get_2_value, get_3_value, get_SQL_boolean, get_string_value, get_string_value, setSwalAlert
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from tools.token import hash_token, get_token
from Card.models import Card
from django.db import transaction
from constants.constants import DEFAULT_ERROR, DONE, FAILED, MAX_RECORD, WRITE_TOKEN
from .sockets import cardWriteWebSocket
from Main.models import RedisConnection
from psycopg2.sql import SQL, Identifier, Literal
from django.db import connection

############ TYPES ############
class SubjectMeta(NamedTuple):
    sem: int
    marks: int

class SemMeta(NamedTuple):
    marks: int
    total: int

class CompleteMeta(NamedTuple):
    ID: str
    data: dict

class CompleteFeed(NamedTuple):
    ID: str
    locked: bool
    issued: bool
    status: bool | None

############ UTILS ############
def get_complete_data(req: HttpRequest, id: int, idx: str):
    
    table_name = Identifier(DataTable._meta.db_table)
    data_column = Identifier(DataTable.data.field.column)  # type: ignore
    locked_column = Identifier(DataTable.locked.field.column)  # type: ignore
    issued_column = Identifier(DataTable.issued.field.column)  # type: ignore
    status_column = Identifier(DataTable.status.field.column)  # type: ignore
    taskID_column = Identifier(DataTable.taskID.field.column)  # type: ignore
    identifier = Literal(idx)
    taskID = Literal(id)
    
    records = CompleteMeta("", {})
    task: TaskTable = req.__getattribute__("task")
    groupBy = Literal(task.groupByColumn)
    
    with connection.cursor() as cursor:
        sql_query = SQL('select * from (select {data_column}::jsonb ->>{groupBy} as "ID", jsonsum({data_column}::jsonb)::jsonb as "data" from {table_name} where {taskID_column}={taskID} and ({data_column}::jsonb ->>{groupBy})={identifier} group by "ID") as "A" limit 1;').format(
            data_column=data_column,
            groupBy=groupBy,
            locked_column=locked_column,
            issued_column=issued_column,
            status_column=status_column,
            table_name=table_name,
            taskID_column=taskID_column,
            taskID=taskID,
            identifier=identifier
        )

        cursor.execute(sql_query)
        (ID, data) = cursor.fetchone()
        records = CompleteMeta(ID, json.loads(data))

    return records

def get_complete_feed(req: HttpRequest, id: int, idx: str):
    
    table_name = Identifier(DataTable._meta.db_table)
    data_column = Identifier(DataTable.data.field.column)  # type: ignore
    locked_column = Identifier(DataTable.locked.field.column)  # type: ignore
    issued_column = Identifier(DataTable.issued.field.column)  # type: ignore
    status_column = Identifier(DataTable.status.field.column)  # type: ignore
    taskID_column = Identifier(DataTable.taskID.field.column)  # type: ignore
    identifier = Literal(idx)
    taskID = Literal(id)
    
    records = CompleteFeed("", False, False, None)
    task: TaskTable = req.__getattribute__("task")
    groupBy = Literal(task.groupByColumn)
    
    with connection.cursor() as cursor:
        sql_query = SQL('select * from (select {data_column}::jsonb ->>{groupBy} as "ID", bool_and({locked_column}) as "locked", bool_and({issued_column}) as "issued", bool_and({status_column}) as "status" from {table_name} where {taskID_column}={taskID} and ({data_column}::jsonb ->>{groupBy})={identifier} group by "ID") as "A" limit 1;').format(
            data_column=data_column,
            groupBy=groupBy,
            locked_column=locked_column,
            issued_column=issued_column,
            status_column=status_column,
            table_name=table_name,
            taskID_column=taskID_column,
            taskID=taskID,
            identifier=identifier
        )

        cursor.execute(sql_query)
        (ID, locked, issued, status) = cursor.fetchone()
        records = CompleteFeed(ID, locked, issued, status)

    return records


def set_complete_feed(req: HttpRequest, id: int, idx: str, locked: bool, issued: bool, status: bool | None) -> int:
    
    table_name = Identifier(DataTable._meta.db_table)
    locked_column = Identifier(DataTable.locked.field.column)
    issued_column = Identifier(DataTable.issued.field.column)
    status_column = Identifier(DataTable.status.field.column)
    taskID_column = Identifier(DataTable.taskID.field.column)
    rowColumn = Identifier(DataTable.data.field.column)
    identifier = Literal(idx)
    taskID = Literal(id)
    locked = get_SQL_boolean(locked) # type: ignore
    issued = get_SQL_boolean(issued) # type: ignore
    status = get_SQL_boolean(status) # type: ignore
    
    task: TaskTable = req.__getattribute__("task")
    groupBy = Literal(task.groupByColumn)
    updated: int = 0
    
    with connection.cursor() as cursor:

        sql_query = SQL('''
                        update {table_name} set {locked_column}=%(locked)s, {issued_column}=%(issued)s, {status_column}=%(status)s
                        where {taskID_column}={taskID} and {rowColumn}::jsonb?{groupBy} and {rowColumn}::jsonb->>{groupBy}={identifier};
                        '''% {
                                "locked":locked,
                                "issued":issued,
                                "status":status,
                        }).format(
                            groupBy=groupBy,
                            locked_column=locked_column,
                            issued_column=issued_column,
                            status_column=status_column,
                            table_name=table_name,
                            taskID_column=taskID_column,
                            taskID=taskID,
                            rowColumn=rowColumn,
                            identifier=identifier
                        )

        cursor.execute(sql_query)
        updated = cursor.rowcount

    return updated

########### HTTP Request #############
@login_needed()
@semester_permission_check
def sem_view(req: HttpRequest, id: int, idx: int, rowID: int) -> HttpResponse:
    if is_auth_get(req):
        return render(req, "Report/HTML/sem.index.html", { "id": id, "idx": idx, "rowID": rowID})
    
@login_needed()
@task_permission_check
def index_view(req: HttpRequest, id: int, idx: str) -> HttpResponse:
    if is_auth_get(req):
        return render(req, "Report/HTML/index.html", { "id": id, "idx": idx, **get_post(req.user), "isManager": is_manager(req.user) })

@login_needed()
@task_permission_check
def generate_report(req: HttpRequest, id: int, idx: str) -> FileResponse:
    context = {"id": id, "idx": idx}
    user = get_user(req)
    
    if is_auth_get(req):

        schema_id = req.GET.get("schema", "")
        
        try:
            post = get_post_id(user)
            records = get_complete_data(req, id, idx)
            sem_dict = getSubjects(schema_id, post["branch"])
                
            personal_data: dict[str, str] = {}
            image_data: dict[str, str] = {}
            sem_data: dict[int, dict[str, tuple[int, int]]] = {}
            
            for column, values in records.data.items():
                if(column[-1]=='I'):
                    image_data[column[:-1]] = values
                else:
                    if((sub := column[:-1]) in sem_dict):
                        if(sem_dict[sub].sem not in sem_data): sem_data[sem_dict[sub].sem] = {}
                        sem_data[sem_dict[sub].sem][sub] = SemMeta(values, sem_dict[sub].marks) 
                    else:
                        personal_data[sub] = values
            
            sem_data = { key: sem_data[key] for key in sorted(sem_data.keys()) }
            
            context.update(get_post(user))
            context.update({"images": image_data, "personal": personal_data, "sem_data": sem_data})
            
        except Exception as e:
            print(e)
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Report/HTML/generated.report.html", context=context)

############ HTMX Request ############
@auth_needed()
@htmx_response
def htmx_schema(req: HttpRequest):
    context: dict[str, list[tuple[int, str]]] = {"options":[]}
    user = get_user(req)
    
    if is_hx_get(req):
        try:
            post = get_post_id(user)
            schemas = Schema.objects.filter(branch__id = post["branch"]).only("id", "name").values("id", "name")
            options: list[tuple[int, str]] = []
            
            for schema in schemas.iterator():
                id: int = int(schema["id"])
                name: str = str(schema["name"])

                options.append((id, name))

            context['options'] = options
            
        except Exception as e:
            print(e)
            setSwalAlert(context, DEFAULT_ERROR)
            
        return render(req, "Report/HTMX/schema.html", context=context)

def getSubjects(schema_id: int, branch_id: int):
    
    sem_dict: dict[str, SubjectMeta] = {} # semester wise subjects with max marks
    
    try:
        
        subjects = Subject.objects.filter(schema__id=schema_id, schema__branch__id=branch_id).values("name", "semester", "marks")
            
        for subs in subjects.iterator():
            name = subs["name"]
            semester = subs["semester"]
            marks = subs["marks"]
                
            sem_dict[name] = SubjectMeta(semester, marks)
            
    except Exception as e:
        print(e)
        
    return sem_dict

@auth_needed()
@htmx_response
@task_permission_check
def report_view(req: HttpRequest, id: int, idx: str):
    context = {"id": id, "idx": idx}
    user = get_user(req)
    
    if is_hx_get(req):

        schema_id = req.GET.get("schema", "")
        
        try:
            post = get_post_id(user)
            records = get_complete_data(req, id, idx)
            sem_dict = getSubjects(schema_id, post["branch"])
                
            personal_data: dict[str, str] = {}
            image_data: dict[str, str] = {}
            sem_data: dict[int, dict[str, tuple[int, int]]] = {}
            
            for column, values in records.data.items():
                if(column[-1]=='I'):
                    image_data[column[:-1]] = values
                else:
                    if((sub := column[:-1]) in sem_dict):
                        if(sem_dict[sub].sem not in sem_data): sem_data[sem_dict[sub].sem] = {}
                        sem_data[sem_dict[sub].sem][sub] = SemMeta(values, sem_dict[sub].marks) 
                    else:
                        personal_data[sub] = values
            
            sem_data = { key: sem_data[key] for key in sorted(sem_data.keys()) }
            
            context.update(get_post(user))
            context.update({"images": image_data, "personal": personal_data, "sem_data": sem_data, "schema":schema_id})

        except InvalidSchema as f:
            messages.error(req, f.get_error())

        except Exception as e:
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/report.html", context=context)


@htmx_response
@auth_needed()
@task_permission_check
def htmx_feedBack(req: HttpRequest, id: int, idx: str):
    context = {"id": id, "idx": idx, "form": CompleteFeedBackView()}
    user = get_user(req)
    
    if is_hx_get(req) and is_admin(user):
        
        try:
            records = get_complete_feed(req, id, idx)
            context.update({"form": CompleteFeedBackView(initial={"status": get_string_value(records.status), "locked": get_string_value(records.locked), "issued": get_string_value(records.issued)})})

        except ValueError as f:
            messages.error(req, str(f))

        except Exception as e:
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/complete/admin.form.html", context=context)

    elif is_hx_get(req) and is_manager(user):

        try:
            records = get_complete_feed(req, id, idx)
            context.update({"form": CompleteFeedBack(initial={"status": get_string_value(records.status), "locked": get_string_value(records.locked), "issued": get_string_value(records.issued)})})

        except InvalidSchema as f:
            setSwalAlert(context, f.get_error(), title="Feedback Fetch")

        except Exception as e:
            setSwalAlert(context, DEFAULT_ERROR, title="Feedback Fetch")

        return render(req, "Report/HTMX/complete/manager.form.html", context=context)
    
    elif is_hx_post(req) and is_manager(user):
        try:
            form = CompleteFeedBack(req.POST)
            setSwalAlert(context, title="Feedback Status")
            
            with transaction.atomic():
                if form.is_valid():
                    
                    locked = form.cleaned_data.get("locked")
                    issued = form.cleaned_data.get("issued")
                    status = form.cleaned_data.get("status")
                    
                    updated = set_complete_feed(req, id, idx, get_2_value(locked), get_2_value(issued), get_3_value(status)) 
                    setSwalAlert(context, f"Status of {updated} records was updated successfully", "success")
                else:
                    setSwalAlert(context, form.getErrors())
                
        except Exception as e:
            setSwalAlert(context, DEFAULT_ERROR)
        
        return render(req, "Report/HTMX/message.html", context=context)

@htmx_response
@auth_needed()
@task_permission_check
def sem_report_view(req: HttpRequest, id: int, idx: int, rowID: int) -> HttpResponse:
    context = {"id": id, "idx": idx, "rowID": rowID}
    
    if is_hx_get(req):

        try:
            records = DataTable.objects.get(taskID__id=id,semester=idx,id=rowID)

            context.update({"result": records.data})

        except Exception as e:
            messages.error(req, "Data Fetching Failed")
            return render(req, "Report/HTMX/sem.report.html", context=context)


        return render(req, "Report/HTMX/sem.report.html", context=context)
    
@htmx_response
@auth_needed()
@semester_permission_check
def sem_feed_view(req: HttpRequest, id: int, idx: int, rowID: int) -> HttpResponse:
    context = {"id": id, "idx": idx, "rowID": rowID}
    user = get_user(req)
    
    if is_hx_post(req) and is_manager(req.user):

        f = FeedBackForm(req.POST)

        try:
            if f.is_valid():
                status = f.cleaned_data.get("status")
                feedBack = f.cleaned_data.get("feedBack")
                locked = f.cleaned_data.get("locked")
                issued = f.cleaned_data.get("issued")
                
                data = DataTable.objects.get(taskID__id=id,semester=idx,id=rowID)
                data.status = get_3_value(status)
                data.feed = feedBack
                data.locked = get_2_value(locked)
                data.issued = get_2_value(issued)
                data.save()

                messages.success(req, f"Status for Row ID: {rowID} was updated successfully")
            else:
                for field, error in f.errors.items(): 
                    messages.error(req, "{}: {}".format(FeedBackForm.declared_fields.get(field).label, ",".join([','.join(i) for i in error.data])))

        except DataTable.DoesNotExist:
            messages.error(req, f"RowID: '{rowID}' does not exits")

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION,
                    taskID=id,
                    index=idx,
                    user=req.user,
                    exception=e,
                )
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/message.html")

    elif is_hx_get(req) and is_manager(user):

        try:
            data = DataTable.objects.get(taskID__id=id,semester=idx,id=rowID)
            status = get_string_value(data.status)
            feedBack = data.feed
            locked = get_string_value(data.locked)
            issued = get_string_value(data.issued)
            
            context["form"] = FeedBackForm(initial={"status": status, "feedBack": feedBack, "locked": locked, "issued": issued})
            
        except DataTable.DoesNotExist:
            messages.error(req, f"RowID: '{rowID}' does not exits")

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION,
                    taskID=id,
                    index=idx,
                    user=req.user,
                    exception=e,
                )
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/sem/manager.form.html", context=context)

    elif is_hx_get(req) and is_admin(req.user):

        try:
            data = DataTable.objects.get(taskID__id=id,semester=idx,id=rowID)
            status = data.status
            feedBack = data.feed
            locked = data.locked
            issued = data.issued
            
            context["form"] = FeedBackView(initial={"status": get_string_value(status), "feedBack": feedBack, "locked": get_string_value(locked), "issued": get_string_value(issued)})
            
        except DataTable.DoesNotExist:
            messages.error(req, f"RowID: '{rowID}' does not exits")

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION,
                    taskID=id,
                    index=idx,
                    user=req.user,
                    exception=e,
                )
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/sem/admin.form.html", context=context)

"""
    Generally idea for card write:
        1) Generate a read-token and store it in req.session
        2) Compute actual token by generating sha256 of token and userID

"""


def writeBegin(user: User, token: str) -> bool:
    with RedisConnection() as redis: return redis.set(token, {"id": user.id, "processing": True})
    return False


@htmx_response
@auth_needed(manager_only=True)
@task_permission_check
def issue_view(req: HttpRequest, id: int, idx: str) -> HttpResponse:
    user = get_user(req)
    context = {"ok":False, "url":"", "path": settings.WRITE_REGISTRY, "msg": None}
    
    if is_hx_get(req):
        schema = req.GET.get("schema", "")
        
        try:
            feed = get_complete_feed(req, id, idx)
            chosen_schema = Schema.objects.filter(id=schema).exists()
            
            if chosen_schema is False:
                raise Schema.DoesNotExist()
            
            if feed.locked is False:
                raise DataNotLocked()
            
            
            writeToken = get_token()
            req.session[WRITE_TOKEN] = writeToken
            token = hash_token(writeToken, user.id)
            setFlag = writeBegin(user, token)

            if not setFlag:
                raise RedisFailed()
            
            context["url"] = req.build_absolute_uri(reverse("Report:writeBase", args=(id,idx,token,schema)))
            context["ok"] = True
            context["msg"] = "Issuing of Card is possible. Would you like to proceed?"
    
        except RedisFailed as r:
            context["msg"] = r.get_error()
            
        except Schema.DoesNotExist:
            context["msg"] = "Chosen schema does not exist"
    
        except DataNotLocked as f:
            context["msg"] = f.get_error()
            
        except Exception as e:
            context["msg"] = DEFAULT_ERROR
            
        return render(req, "Report/HTMX/write/begin.html", context=context)
