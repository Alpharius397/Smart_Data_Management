from base64 import b64decode, b64encode
import functools
from io import BytesIO
import json
from PIL import Image
from typing import Any, NamedTuple, TypedDict, Literal
import typing
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render  # type: ignore
from django.urls import reverse  # type: ignore
from django.http import HttpRequest, HttpResponse, JsonResponse, FileResponse  # type: ignore
from Report.errors import DataNotLocked, InvalidSchema, RedisFailed
from University.models import Subject, Schema, SemMeta
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
    is_auth_post,
    api_key_required,
    auth_needed,
    task_permission_check,
    token_check,
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
from Main.models import RedisConnection, ReadToken, WriteToken
from psycopg2.sql import SQL, Identifier
from django.db import connection

############ TYPES ############

class FetchJson(TypedDict):
    data: str
    
class ReadJson(TypedDict):
    message: str
    status: Literal['true', 'false', 'none']
    card: str
    data: str

class ConfirmJson(TypedDict):
    message: str
    status: Literal['true', 'false', 'none']
    card: str
    
class SubjectMeta(TypedDict):
    sem: int
    marks: int

class SemMeta(NamedTuple):
    marks: int
    total: int

@csrf_exempt
@api_key_required
@token_check
@auth_needed(manager_only=True)
@task_permission_check
def fetch_data(req: HttpRequest, id: int, idx: str, schema: int, token: str):
    
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")
    context:dict[str, Any] = {}
    
    if(is_auth_post(req)):
        try:
            post = get_post_id(user)
            
            record = DataTable.get_complete_data(task, id, idx)
            feed = DataTable.get_complete_feed(task, id, idx)
            
            if feed.locked is False:
                raise DataNotLocked()
            
            sem_dict = Subject.getSubjects(schema, post["branch"])
                
            personal_data: dict[str, str] = {}
            image_data: dict[str, str] = {}
            sem_data: dict[int, dict[str, tuple[int, int]]] = {}
            
            for column, values in record.data.items():
                if(column[-1]=='I'):
                    image_data[column[:-1]] = values
                else:
                    if((sub := column[:-1]) in sem_dict):
                        if(sem_dict[sub].sem not in sem_data): sem_data[sem_dict[sub].sem] = {}
                        sem_data[sem_dict[sub].sem][sub] = SemMeta(values, sem_dict[sub].marks) 
                    else:
                        personal_data[sub] = values
                        
            context.update(get_post(user))
            context.update({"images": image_data, "personal": personal_data, "sem_data": sem_data})
            
            encrypted = encrypt_data(settings.KEY, context)
            
            return JsonResponse(data=FetchJson(data=encrypted), safe=True, status=200)
        except:
            pass
        
        
@csrf_exempt
@api_key_required
@token_check
@auth_needed(manager_only=True)
@task_permission_check
def confirm_view(req: HttpRequest, id: int, idx: str, schema: int, token: str):
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")
    context:dict[str, Any] = {}
    
    if is_auth_post(req):
        
        try:
            data = ReadJson(**req.POST.dict()) # type: ignore
            
            with RedisConnection() as redis:
                redis.unset(token)
            
            issued = data["status"]
            
            DataTable.set_complete_feed(task, id, idx, issued=get_2_value(issued))
            print(data)
            
        except Exception as e:
            print(e)
            
    return JsonResponse(data={"status": "We are trying to reach you out about your car's extended warranty"}, status=200)