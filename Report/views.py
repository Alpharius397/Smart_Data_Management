from base64 import b64decode, b64encode
from collections import defaultdict
from bisect import bisect_right, insort_left
import functools
from io import BytesIO
import json
from PIL import Image
from typing import Any
import typing
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render  # type: ignore
from django.urls import reverse  # type: ignore
from django.http import HttpRequest, HttpResponse, JsonResponse  # type: ignore
from University.models import Grade, Subject
from Task.models import DataTable, AssignTable, UploadTable
from Main.settings import settingsInterface as settings
from tools.get_image import compress_image
from User.models import (
    RoleType,
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
)
from Report.errors import ManagerAlreadyAssigned, ManagerDoesNotExist
from Report.forms import VerifyForm
from django.utils import timezone  # type: ignore
from Logs.loggers import APP_LOG, LogStructure, Task
from tools.utils import ColumnType, ReportStructure, segregateColumns
from django.views.decorators.csrf import csrf_exempt  # type: ignore
from tools.token import get_token, hash_token
from Card.models import Card
from django.http import QueryDict
from django.db import transaction
from constants.constants import DEFAULT_ERROR, DONE, FAILED, MAX_RECORD, WRITE_TOKEN
from .sockets import cardWriteWebSocket
from Main.models import *
from psycopg2.sql import SQL, Identifier, Literal
from django.db import connection


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
            Q(fileID__uploader__id=user.id) | Q(fileID__assigned__manager__id=user.id)
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


########### HTTP Request #############
@login_needed()
@file_permission_check
def index_view(req: HttpRequest, id: str, idx: int) -> HttpResponse:
    if is_auth_get(req):
        get_color(req)
        return render(
            req,
            "Report/index.html",
            {
                "id": id,
                "idx": idx,
            },
        )


############ HTMX Request ############
@auth_needed()
@htmx_response
@file_permission_check
def report_view(req: HttpRequest, id: int, idx: int) -> HttpResponse:
    context: dict[str, Any] = {"id": id, "idx": idx}

    if is_hx_get(req):

        try:
            post = get_post_id(req.user)
            records = DataTable.objects.get(fileID__id = id, id = idx)
            subjects = Subject.objects.filter(branch__id=post["branch"]).values("name", "semester", "marks")
            grades = Grade.objects.filter(subject__branch__id=post["branch"]).values("grade", "minMarks", "subject__name")
            
            sem_dict: dict = defaultdict(dict) # semester wise subjects with max marks
            grade_dict: dict = defaultdict(dict) # minimum marks for a grade in sub 
            grade_list: dict = defaultdict(list) # sorted list of grades to calculate grade
            
            for subs in subjects.iterator():
                name = subs["name"]
                semester = subs["semester"]
                marks = subs["marks"]
                
                sem_dict[semester][name] = marks
                
            for gra in grades.iterator():
                grade = gra["grade"]
                minMarks = gra["minMarks"]
                sub = gra["subject__name"]
                grade_dict[sub][minMarks] = grade
                
                insort_left(grade_list[sub], minMarks) 
                
            _, column_list = get_columns(id)

            sem: list = column_list.semester
            personal: list = column_list.personal
            images: list = column_list.images
            
            personal_data: dict[str, str] = {}
            image_data: dict[str, str] = {}
            sem_data: dict[int, tuple[str, str, str]] = {}

            for column in personal:
                personal[column] = records.data.get(column, "-")
                
            for column in images:
                image_data[column] = records.data.get(column, "-")
                
            
            


        except Exception as e:
            print(e)
            context["error"] = DEFAULT_ERROR
            return render(req, "View/HTMX/report.html", context=context)


        return render(req, "View/HTMX/report.html", context=context)


@htmx_response
@auth_needed()
def feed_view(req: HttpRequest, id: str, idx: int) -> HttpResponse:
    if is_hx_post(req) and is_manager(req.user):
        conn = MongoConnection().connect()
        context = {"id": id, "idx": idx}

        f = VerifyForm(req.POST)

        if f.is_valid():
            _status, feed = f.cleaned_data.get("status"), f.cleaned_data.get("feed")

            if _status == "True":
                status = True
            elif _status == "False":
                status = False
            else:
                status = None

            try:
                status_col = f"data.excel.{idx}.feed.status"
                feed_col = f"data.excel.{idx}.feed.feed"
                where, updates = MongoTemplate.update_query(
                    {"_id": ObjectId(id), "$or": auth_view(req.user)},
                    {status_col: status, feed_col: feed},
                )
                success = conn.update_one(where, updates)

                conditions, filters = MongoTemplate.merge_everything(
                    MongoTemplate.get_buffer_query(start=idx),
                    initial_a={
                        "$and": [
                            {
                                "_id": ObjectId(id),
                                "header.manager": req.user.id,
                                "header.post": get_post_id(req.user),
                            }
                        ]
                    },
                )
                result: Document | None = conn.find_one(conditions, filters)

                if result is None:
                    context["error"] = MONGO_ERROR
                else:
                    meta_data: Feed.FeedDict = result.data.excel[0].feed.to_dict()
                    manager: list[str | None] = list(
                        map(get_user_by_id, result.header.manager)
                    )
                    context.update({"form": VerifyForm(data=meta_data)})
                    context.update({**meta_data, "manager": manager})

                if success:
                    context["msg"] = "Status Updated!"
                    APP_LOG.write_info(
                        LogStructure()
                        .set_request(req)
                        .set_description(
                            type=Task.FEED_EDIT, taskID=id, index=idx, user=req.user
                        )
                    )
                else:
                    context["error"] = "Mongo ID %s not found" % id

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
                context["error"] = DEFAULT_ERROR

            finally:
                conn.close()
        else:
            context["error"] = f.errors.as_text()

        return render(req, "View/single/manager.html", context=context)

    elif is_hx_get(req) and is_manager(req.user):
        conn = MongoConnection().connect()
        context = {"id": id, "idx": idx}

        try:
            conditions, filters = MongoTemplate.merge_everything(
                MongoTemplate.get_buffer_query(start=idx),
                initial_a={
                    "$and": [
                        {
                            "_id": ObjectId(id),
                            "header.manager": req.user.id,
                            "header.post": get_post_id(req.user),
                        }
                    ]
                },
            )
            result = conn.find_one(conditions, filters)

            if result is None:
                context["error"] = MONGO_ERROR
            else:
                meta_data = result.data.excel[0].feed.to_dict()
                manager = list(map(get_user_by_id, result.header.manager))
                context.update({**meta_data, "manager": manager})

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=id, user=req.user, exception=e
                )
            )
            context["error"] = DEFAULT_ERROR
        finally:
            conn.close()

        context.update(
            {
                "form": VerifyForm(
                    data={
                        "status": (
                            lambda x: (
                                "True"
                                if x
                                else ("False")
                                if x is not None
                                else ("None")
                            )
                        )(context.get("status", "None")),
                        "feed": context.get("feed", ""),
                    }
                )
            }
        )
        return render(req, "View/single/manager.html", context=context)

    elif is_hx_get(req) and is_admin(req.user):
        conn = MongoConnection().connect()
        context = {"id": id, "idx": idx}

        try:
            conditions, filters = MongoTemplate.merge_everything(
                MongoTemplate.get_header_query(),
                MongoTemplate.get_feedback_query(start=idx, limit=1),
                initial_a={"$and": [{"_id": ObjectId(id), "$or": auth_view(req.user)}]},
            )
            result = conn.find_one(conditions, filters)

            if result is None:
                context["error"] = MONGO_ERROR
            else:
                meta_data = result.data.excel[0].feed.to_dict()
                manager = list(map(get_user_by_id, result.header.manager))
                context.update({**meta_data, "manager": manager})

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=id, user=req.user, exception=e
                )
            )
            context["error"] = DEFAULT_ERROR

        finally:
            conn.close()

        return render(req, "View/single/admin.html", context=context)


@htmx_response
@auth_needed(manager_only=True)
def compress_view(req: HttpRequest, id: str, idx: int) -> HttpResponse:
    if is_hx_get(req):
        conn = MongoConnection().connect()

        context = {"id": id, "idx": idx}
        try:
            conditions, filters = MongoTemplate.merge_everything(
                MongoTemplate.get_header_query(),
                MongoTemplate.get_feedback_query(start=idx, limit=1),
                initial_a={"$and": [{"_id": ObjectId(id), "$or": auth_view(req.user)}]},
            )
            result: Document | None = conn.find_one(conditions, filters)

            if result is None:
                context["error"] = MONGO_ERROR
            else:
                meta_data: Feed.FeedDict = result.data.excel[0].feed.to_dict()
                context.update(meta_data)

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
            context["error"] = DEFAULT_ERROR

        finally:
            conn.close()

        return render(req, "View/single/manager_form.html", context=context)

    elif is_hx_put(req) or is_hx_delete(req):
        conn = MongoConnection().connect()

        context = {"id": id, "idx": idx}
        timestamp: str | None = None

        time_issue = f"data.excel.{idx}.feed.time_of_lock"
        locked_col = f"data.excel.{idx}.feed.locked"

        if is_hx_put(req):
            timestamp = timezone.now().isoformat()
            updateDict: dict = {
                "where": {"_id": ObjectId(id)},
                "updates": {time_issue: timestamp, locked_col: True},
            }
        else:
            updateDict = {
                "where": {"_id": ObjectId(id)},
                "updates": {time_issue: timestamp, locked_col: False},
            }

        try:
            where, updates = MongoTemplate.update_query(**updateDict)
            res = conn.update_one(where, updates)

            if is_hx_put(req) and res:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req)
                    .set_description(
                        type=Task.DATA_LOCK, taskID=id, index=idx, user=req.user
                    )
                )
                context["msg"] = "Card Issued"

            elif is_hx_delete(req) and res:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req)
                    .set_description(
                        type=Task.DATA_UNLOCK, taskID=id, index=idx, user=req.user
                    )
                )
                context["msg"] = "Card Cancelled"

            else:
                context["error"] = "Data operation failed"

            conditions, filters = MongoTemplate.merge_everything(
                MongoTemplate.get_header_query(),
                MongoTemplate.get_feedback_query(start=idx, limit=1),
                initial_a={"$and": [{"_id": ObjectId(id), "$or": auth_view(req.user)}]},
            )
            result = conn.find_one(conditions, filters)

            if result is None:
                context["error"] = MONGO_ERROR
            else:
                meta_data = result.data.excel[0].feed.to_dict()
                context.update(meta_data)

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
            context["error"] = DEFAULT_ERROR

        finally:
            conn.close()

        return render(req, "View/single/manager_form.html", context=context)


def compress_data(
    result: Document, local_write: bool = True, buffer_out: bool = True
) -> BytesIO | dict:
    columns: list = result.data.header.columns
    image_idx: list = result.data.header.image_columns
    data: dict[str, str | int] = {
        columns[idx % len(columns)]: i for idx, i in enumerate(result.data.excel[0].row)
    }
    header = get_post_by_ID(**result.header.post.to_dict())

    for i in image_idx:
        try:
            assert i >= 0 and i < len(columns), "Index checking"
            img_data = data[columns[i]]
            assert isinstance(img_data, str), "Image needs to be string"

            raw_img = img_data.split(":")
            _, _, img = raw_img
        except Exception as e:
            img = bad_image

        img = compress_image(BytesIO(b64decode(img)))
        data[columns[i]] = img

    if local_write:
        with open(settings.MEDIA_ROOT + "/compress.txt", "w") as f:
            f.write(encrypt_data(settings.KEY, {"data": data, "header": header}))

        with open(settings.MEDIA_ROOT + "/decompress.txt", "w") as f:
            f.write(
                json.dumps(
                    decrypt_data(
                        settings.KEY,
                        encrypt_data(settings.KEY, {"data": data, "header": header}),
                    )
                )
            )

    buffer = BytesIO()
    buffer.write(encrypt_data(settings.KEY, {"data": data, "header": header}).encode())
    buffer.seek(0)

    return buffer if (buffer_out) else data


@htmx_response
@auth_needed(manager_only=True)
def card_view(req: HttpRequest, id: str, idx: int) -> HttpResponse:
    if is_hx_get(req):
        hashToken = hash_token(req.session.get(WRITE_TOKEN), req.user.id)
        api_endpoint = f"{req.build_absolute_uri(reverse('View:__base__', args=(id, idx, hashToken)))}"

        return render(
            req,
            "View/HTMX/exe/end.html",
            context={
                "id": id,
                "idx": idx,
                "data": api_endpoint,
                "path": settings.WRITE_REGISTRY,
            },
        )  # end write op

    if is_hx_post(req):
        Redis = RedisConnection().connect()
        hashToken = hash_token(req.session.get(WRITE_TOKEN), req.user.id)
        Redis.set(hashToken, {"status": LOADING, "user": req.user.id})

        return render(
            req,
            "View/HTMX/exe/begin.html",
            context={"id": id, "idx": idx, "token": hashToken},
        )  # begin write op


@htmx_response
@auth_needed()
def refresh_row(req: HttpRequest, id: str, idx: int) -> HttpResponse:
    if is_hx_get(req):
        conn = MongoConnection().connect()
        context = {"id": id, "idx": idx}

        try:
            match_pipeline: dict[str, dict[str, Any] | str] = {
                "$match": {"_id": ObjectId(id), f"data.excel.{idx}": {"$exists": True}}
            }
            filter_pipeline: dict[str, dict[str, Any] | str] = {
                "$project": {
                    "header": 1,
                    "data.header": 1,
                    "data.excel": {
                        "$filter": {
                            "input": "$data.excel",
                            "as": "i",
                            "cond": {"$eq": ["$$i.feed.index", idx]},
                        }
                    },
                }
            }

            result: list[Document] = list(
                map(Document.get, conn.aggregate(match_pipeline, filter_pipeline))
            )

            if not (result and (result[0])):
                context["error"] = "Row cannot be fetched"
            else:
                value: Document = result[0]

                columns: list = value.data.header.columns
                feed_list: list[Feed.FeedDict] = list(
                    map(lambda x: x.feed.to_dict(), value.data.excel)
                )
                image_idx: list = [columns[i] for i in value.data.header.image_columns]
                data: list[list[str | int]] = list(
                    map((lambda x: x.row), value.data.excel)
                )
                pd_data = pd.DataFrame(
                    data,
                    columns=columns,
                    index=list(map(lambda x: x.feed.index, value.data.excel)),
                )

                context.update(
                    {
                        "column": pd_data.columns,
                        "result": pd_data.iterrows(),
                        "feed": feed_list,
                        "image": image_idx,
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

        return render(req, "View/HTMX/refresh.html", context=context)


@htmx_response
@auth_needed(admin_only=True)
def edit_form(req: HttpRequest, id: str, idx: int) -> HttpResponse:
    if is_hx_get(req):
        column = req.GET.get("column", None)
        value = req.GET.get("value", "")

        return render(
            req,
            "View/HTMX/edit_form/edit_form.html",
            context={
                "id": id,
                "column": column,
                "idx": idx,
                "value": value,
            },
        )

    elif is_hx_post(req):
        column: int = req.POST.get("column", None)
        value: str = req.POST.get(
            "value",
        )
        old: str = req.POST.get("old", "")

        conn = MongoConnection().connect()

        context = {"id": id, "idx": idx, "value": value, "column": column}

        try:
            where: dict = {
                "_id": ObjectId(id),
                "data.header.image_columns": {"$ne": int(column)},
                f"data.excel.{idx}": {"$exists": True},
                f"data.excel.{idx}.feed": {"$exists": True},
                f"data.excel.{idx}.row.{column}": {"$exists": True},
                f"data.excel.{idx}.feed": {"$ne": True},
            }

            update: dict = {"$set": {f"data.excel.{idx}.row.{column}": value}}

            res = conn.update_one(where, update)

            if res:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req)
                    .set_description(
                        type=Task.DATA_EDIT,
                        taskID=id,
                        index=idx,
                        column=column,
                        user=req.user,
                    )
                )
            else:
                context["lock"] = True
                context["error"] = "Cannot Edit this index as its locked"

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
            context["error"] = DEFAULT_ERROR
            context["value"] = old
            return render(
                req, "View/HTMX/normal_view/normal_view.html", context=context
            )

        return render(req, "View/HTMX/normal_view/normal_view.html", context=context)


@htmx_response
@auth_needed(admin_only=True)
def edit_image_form(req: HttpRequest, id: str, idx: int) -> HttpResponse:
    if is_hx_get(req):
        column = req.GET.get("column", None)

        return render(
            req,
            "View/HTMX/edit_form/edit_image_form.html",
            context={"id": id, "column": column, "idx": idx},
        )

    elif is_hx_post(req):
        column: int = req.POST.get("column", None)
        file = req.FILES.get("file")
        context = {
            "id": id,
            "idx": idx,
            "admin": True,
            "column": column,
            "update": False,
        }

        try:
            buffer = BytesIO()
            with file.open("rb") as f:
                buffer.write(f.read())

            img = Image.open(buffer)
            width, height = img.width, img.height
            buffer.seek(0)

            with BytesIO() as b:
                img.save(b, format=img.format, quality=95)
                img_data = f"{width}:{height}:{b64encode(buffer.getvalue()).decode()}"

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=id, user=req.user, exception=e
                )
            )
            context["error"] = "Image Extraction Failed"
            return render(
                req, "View/HTMX/normal_view/normal_image.html", context=context
            )

        conn = MongoConnection().connect()

        try:
            where: dict = {
                "_id": ObjectId(id),
                "data.header.image_columns": int(column),
                f"data.excel.{idx}": {"$exists": True},
                f"data.excel.{idx}.feed": {"$exists": True},
                f"data.excel.{idx}.row.{column}": {"$exists": True},
                f"data.excel.{idx}.feed": {"$ne": True},
            }

            update: dict = {"$set": {f"data.excel.{idx}.row.{column}": img_data}}

            res = conn.update_one(where, update)

            if res:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req)
                    .set_description(
                        type=Task.DATA_EDIT,
                        taskID=id,
                        index=idx,
                        column=column,
                        user=req.user,
                    )
                )
                context.update({"value": img_data})
                context["update"] = True
            else:
                context["error"] = "Cannot Edit this index is locked"
                context["lock"] = True
                return render(
                    req, "View/HTMX/normal_view/normal_image.html", context=context
                )

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
            context["error"] = DEFAULT_ERROR
            return render(
                req, "View/HTMX/normal_view/normal_image.html", context=context
            )

        return render(req, "View/HTMX/normal_view/normal_image.html", context=context)


@htmx_response
@auth_needed(admin_only=True)
def normal_image(req: HttpRequest, id: str, idx: int) -> HttpResponse:
    if is_hx_get(req):
        column = req.GET.get("column", None)
        return render(
            req,
            "View/HTMX/normal_view/normal_image.html",
            context={"id": id, "column": column, "idx": idx},
        )


@htmx_response
@auth_needed(admin_only=True)
def normal_view(req: HttpRequest, id: str, idx: int) -> HttpResponse:
    if is_hx_get(req):
        column = req.GET.get("column", None)
        value = req.GET.get("value", "")
        return render(
            req,
            "View/HTMX/normal_view/normal_view.html",
            context={"id": id, "column": column, "idx": idx, "value": value},
        )


def cardDataSave(card: Card, mongoSave: typing.Callable[[], bool]):
    with transaction.atomic():
        assert mongoSave()
        card.save()
        return True
    return False


def cardDataDelete(card: Card, mongoDelete: typing.Callable[[], bool]):
    with transaction.atomic():
        assert mongoDelete()
        card.delete()
        return True
    return False


@csrf_exempt
@api_key_required
def issued_view(req: HttpRequest, id: str, idx: int, token: str) -> JsonResponse:
    if req.method == "POST":
        status: bool = req.POST.get("status", "")
        cardID = req.POST.get("cardID", None)

        if cardID is None:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.UNAUTH_REQ, taskID=id, index=idx)
            )
            return JsonResponse(data=ERROR_JSON, status=403)

        conn = MongoConnection().connect()
        Redis = RedisConnection().connect()

        match status:
            case "true":
                status = True
            case "false":
                status = False
            case _:
                return JsonResponse(data=ERROR_JSON, status=403)

        error: str = ""
        res = False

        try:
            data: dict[str, str] = Redis.get(token)
            state: bool = data.get("status")

            user: UserObject = User.objects.get(id=data["user"])

            time_of_issue = f"data.excel.{idx}.feed.time_of_issue"
            issued = f"data.excel.{idx}.feed.issued"
            lock_idx = f"data.excel.{idx}.feed.locked"

            if state != LOADING:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req)
                    .set_description(
                        type=Task.INVALID_TOKEN, taskID=id, index=idx, user=user
                    )
                )
                cardWriteWebSocket(token, NONE)
                return JsonResponse(
                    data={"error_occurred": "Invalid Token", "update_occurred": False},
                    status=404,
                )

            cardObject = Card(cardID=cardID, mongoID=id, rowIndex=idx, user=user)

            where, updates = MongoTemplate.update_query(
                {"_id": ObjectId(id), lock_idx: True},
                {time_of_issue: timezone.now().isoformat(), issued: status},
            )
            mongoSaveFuncPartial: typing.Callable[[], bool] = functools.partial(
                conn.update_one, condition=where, update=updates
            )

            if status:
                if cardDataSave(cardObject, mongoSaveFuncPartial):
                    APP_LOG.write_info(
                        LogStructure()
                        .set_request(req)
                        .set_description(
                            type=Task.CARD_ISSUE, taskID=id, index=idx, user=user
                        )
                    )
                    data["status"] = DONE
                else:
                    data["status"] = FAILED

            else:
                if cardDataDelete(cardObject, mongoSaveFuncPartial):
                    APP_LOG.write_info(
                        LogStructure()
                        .set_request(req)
                        .set_description(
                            type=Task.CARD_CANCEL, taskID=id, index=idx, user=user
                        )
                    )
                    data["status"] = DONE
                else:
                    data["status"] = FAILED

            cardWriteWebSocket(token, data["status"])
            Redis.unset(token)

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, taskID=id, index=idx, exception=e)
            )
            cardWriteWebSocket(token, DEFAULT_ERROR)
            error = DEFAULT_ERROR

        finally:
            conn.close()
            Redis.close()

        return JsonResponse(
            data={"error_occurred": error, "update_occurred": res}, status=200
        )

    else:
        APP_LOG.write_error(
            LogStructure()
            .set_request(req)
            .set_description(type=Task.UNAUTH_REQ, taskID=id, index=idx)
        )

    return JsonResponse(data=ERROR_JSON, status=403)


@csrf_exempt
@api_key_required
def fetch_view(req: HttpRequest, id: str, idx: int, token: str) -> JsonResponse:
    if req.method == "POST":
        conn = MongoConnection().connect()
        Redis = RedisConnection().connect()

        jsonResponse: dict[str, Any] = {"data": "Default Data"}

        try:
            data: dict[str, str] = Redis.get(token)
            match_pipeline: dict[str, dict[str, Any] | str] = {
                "$match": {"_id": ObjectId(id), f"data.excel.{idx}": {"$exists": True}}
            }
            filter_pipeline: dict[str, dict[str, Any] | str] = {
                "$project": {
                    "header": 1,
                    "data.header": 1,
                    "data.excel": {
                        "$filter": {
                            "input": "$data.excel",
                            "as": "i",
                            "cond": {"$eq": ["$$i.feed.index", idx]},
                        }
                    },
                }
            }

            result: list[Document] = list(
                map(Document.get, conn.aggregate(match_pipeline, filter_pipeline))
            )

            if not (result and (result[0])):
                return JsonResponse(
                    data={"error": "Row cannot be fetched"}, status=403, safe=False
                )

            vals: Document = result[0]
            user: UserObject = User.objects.get(id=data["user"])

            if data["status"] != LOADING:
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req)
                    .set_description(
                        type=Task.INVALID_TOKEN, taskID=id, index=idx, user=user
                    )
                )
                return JsonResponse(
                    data={"error": "Invalid Token"}, status=403, safe=False
                )

            if vals.data.excel[0].feed.locked:
                compressed: BytesIO | dict = compress_data(vals, True, True)
                assert isinstance(compressed, BytesIO)
                compressed_value: str = compressed.getvalue().decode()

                jsonResponse.update({"data": {"data": compressed_value}, "status": 200})
            else:
                jsonResponse.update(
                    {
                        "data": {
                            "error": f"Mongo ID: {id}, Index: {idx} is not locked"
                        },
                        "status": 403,
                    }
                )

            APP_LOG.write_info(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.CARD_DATA_FETCH, user=user, taskID=id, index=idx
                )
            )

        except Exception as e:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(
                    type=Task.EXCEPTION, taskID=id, index=idx, user=user, exception=e
                )
            )
            jsonResponse.update(
                {"data": {"error": "Some error occurred!"}, "status": 500}
            )

        finally:
            conn.close()
            Redis.close()

        return JsonResponse(**jsonResponse, safe=False)

    return JsonResponse(data=ERROR_JSON, status=403)
