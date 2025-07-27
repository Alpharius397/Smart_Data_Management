from typing import NamedTuple, TypedDict
import zlib
from django.contrib import messages
from django.shortcuts import render  # type: ignore
from django.urls import reverse  # type: ignore
from django.http import HttpRequest, HttpResponse, FileResponse  # type: ignore
from Report.errors import DataNotLocked, InvalidSchema, RedisFailed
from University.models import SemMeta, Subject, Schema, SubjectMeta
from Task.models import DataTable, TaskTable
from Main.settings import settingsInterface as settings
from User.models import (
    get_post_id,
    get_user,
    is_admin,
    is_manager,
    get_post,
    User,
)
from tools.encrypt import b64decode, b64encode
from tools.url_auth import (
    htmx_response,
    is_auth_get,
    is_hx_get,
    is_hx_post,
    login_needed,
    auth_needed,
    semester_permission_check,
    task_permission_check,
)
from Report.forms import CompleteFeedBack, FeedBackForm, FeedBackView, CompleteFeedBackView
from Logs.loggers import APP_LOG, LogStructure, LogType
from tools.utils import get_2_value, get_3_value, get_string_value, get_string_value, setSwalAlert
from tools.get_image import compress_image
from tools.token import hash_token, get_token
from django.db import transaction # type: ignore
from constants import DEFAULT_ERROR, WRITE_TOKEN
from Main.models import RedisConnection, WriteToken

########### TYPES #############
class ReportData(TypedDict):
    images: dict[str, str]
    personal: dict[str, str]
    sem_data: dict[int, dict[str, tuple[int, int]]]

########### UTILS #############

def writeBegin(user: User, token: str) -> bool:
    with RedisConnection() as redis: 
        return redis.set(token, WriteToken(ID=user.id, processing=True))
    return False

def writeEnd(user: User, token: str) -> bool:
    with RedisConnection() as redis: 
        return redis.set(token, WriteToken(ID=user.id, processing=False))
    return False

def getReport(sem_dict: dict[str, SubjectMeta], task: TaskTable, id: int, idx: str, compress: bool = False) -> ReportData:
    records = DataTable.get_complete_data(task, id, idx)
    
    personal_data: dict[str, str] = {}
    image_data: dict[str, str] = {}
    sem_data: dict[int, dict[str, tuple[int, int]]] = {}
    
    for column, values in records.data.items():
        if(column[-1]=='I'):
            image_data[column[:-1]] = compress_image(values) if compress else values
        else:
            if((sub := column[:-1]) in sem_dict):
                if(sem_dict[sub].sem not in sem_data): sem_data[sem_dict[sub].sem] = {}
                sem_data[sem_dict[sub].sem][sub] = SemMeta(values, sem_dict[sub].marks) 
            else:
                personal_data[sub] = values
    
    sem_data = { key: sem_data[key] for key in sorted(sem_data.keys()) }
    
    return ReportData(images=image_data, sem_data=sem_data, personal=personal_data)

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
            task: TaskTable = req.__getattribute__("task")
            sem_dict = Subject.getSubjects(schema_id, post["branch"]) # post is NullStr cause logging, but don't worry it's int in this context
            
            report_data = getReport(sem_dict, task, id, idx)
            
            context.update(get_post(user))
            context.update(report_data)
            
        except Exception as e:
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
            setSwalAlert(context, DEFAULT_ERROR)
            
        return render(req, "Report/HTMX/schema.html", context=context)

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
            task: TaskTable = req.__getattribute__("task")

            sem_dict = Subject.getSubjects(schema_id, post["branch"])
            schema_details = Schema.getSchema(schema_id)
            report_data = getReport(sem_dict, task, id, idx)
            
            context.update(post)
            context.update(report_data)
            context.update(schema_details)
            context.update(get_post(user))
            context.update({**report_data, "schema":schema_id})

        except InvalidSchema as f:
            messages.error(req, f.get_error())

        except Exception as e:
            print(e)
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/report.html", context=context)


@htmx_response
@auth_needed()
@task_permission_check
def htmx_feedBack(req: HttpRequest, id: int, idx: str):
    context = {"id": id, "idx": idx, "form": CompleteFeedBackView()}
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")
    
    if is_hx_get(req) and is_admin(user):
        
        try:
            records = DataTable.get_complete_feed(task, id, idx)
            context.update({"form": CompleteFeedBackView(initial={"status": get_string_value(records.status), "locked": get_string_value(records.locked), "issued": get_string_value(records.issued)})})

        except ValueError as f:
            messages.error(req, str(f))

        except Exception as e:
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/complete/admin.form.html", context=context)

    elif is_hx_get(req) and is_manager(user):

        try:
            records = DataTable.get_complete_feed(task, id, idx)
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
                    status = form.cleaned_data.get("status")
                    issued = form.cleaned_data.get("issued")
                    
                    updated = DataTable.set_complete_feed(task, id, idx, locked=get_2_value(locked), status=get_3_value(status), issued=get_2_value(issued)) 
                    setSwalAlert(context, f"Status of {updated} records was updated successfully", "success")
                    APP_LOG.write_info(LogStructure().set_request(req, LogType.DATA_EDIT, rowID=idx).set_meta(req))
                    
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
                APP_LOG.write_info(LogStructure().set_request(req, LogType.DATA_EDIT, semester=idx, rowID=rowID).set_meta(req))
                
            else:
                for field, error in f.errors.items(): 
                    messages.error(req, "{}: {}".format(FeedBackForm.declared_fields.get(field).label, ",".join([','.join(i) for i in error.data])))

        except DataTable.DoesNotExist:
            messages.error(req, f"RowID: '{rowID}' does not exits")

        except Exception as e:
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
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/sem/admin.form.html", context=context)

@htmx_response
@auth_needed(manager_only=True)
@task_permission_check
def issue_view(req: HttpRequest, id: int, idx: str) -> HttpResponse:
    user = get_user(req)
    context = setSwalAlert(title="Card Issue Request")
    
    if is_hx_get(req):
        schema = req.GET.get("schema", "")
        
        try:
            task: TaskTable = req.__getattribute__("task")
            feed = DataTable.get_complete_feed(task, id, idx)
            
            if not schema:
                raise InvalidSchema()
            
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
            
            context["url"] = req.build_absolute_uri(reverse("Card:writeBase", kwargs={"id":id,"idx":idx,"token":token,"schema":schema}))
            context["ws"] = f"/write/{id}/{idx}/{token}/"
            context["path"] = settings.WRITE_REGISTRY
            context["ok"] = True
            
            setSwalAlert(context, "Issuing of Card is possible. Would you like to proceed?", 'info')
    
        except RedisFailed as r:
            setSwalAlert(context, r.get_error())
            
        except Schema.DoesNotExist:
            setSwalAlert(context,"Chosen schema does not exist")
    
        except InvalidSchema as g:
            setSwalAlert(context,g.get_error())        
            
        except DataNotLocked as f:
            setSwalAlert(context,f.get_error())
            
        except Exception as e:
            setSwalAlert(context, DEFAULT_ERROR)
            
        return render(req, "Report/HTMX/write/begin.html", context=context)
