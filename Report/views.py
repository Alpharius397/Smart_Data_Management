from django.utils import timezone  # type: ignore
import io
from typing import Any, Literal, TypedDict
from django.contrib import messages  # type: ignore
from django.shortcuts import render  # type: ignore
from django.urls import reverse  # type: ignore
from django.http import FileResponse, HttpRequest  # type: ignore
from Report.errors import DataNotLocked, InvalidSchema, RedisFailed
from University.models import Subject, Schema, SubjectMeta
from Task.models import DataTable, TaskTable
from Main.settings import settingsInterface as settings
from User.models import (
    PostIdDict,
    get_post_id,
    get_user,
    is_admin,
    is_manager,
    get_post,
    User,
)
from tools.encrypt import DES_3_KEY_SIZE, encrypt_key, generate_key, b64decode
from tools.signer import addSign
from tools.url_auth import (
    aauth_needed,
    async_task_permission_check,
    htmx_response,
    is_auth_get,
    is_hx_delete,
    is_hx_get,
    is_hx_post,
    login_needed,
    auth_needed,
    pdf_access,
    semester_permission_check,
    task_permission_check,
    token_check,
    require_http_methods,
)
from Report.forms import (
    CompleteFeedBack,
    FeedBackForm,
    FeedBackView,
    CompleteFeedBackView,
)
from Logs.loggers import APP_LOG, SMTP_LOG, LogStructure, LogType
from tools.utils import (
    get_2_value,
    get_3_value,
    get_string_value,
    setSwalAlert,
)
from tools.get_image import compress_image
from tools.token import hash_token, get_token
from django.db import transaction  # type: ignore
from constants import ACCESS_PDF, ACCESS_TOKEN, DEFAULT_ERROR, WRITE_TOKEN
from Main.models import (
    AsyncRedisConnection,
    PdfToken,
    RedisConnection,
    RedisDataBase,
    WriteToken,
)
from playwright.async_api import async_playwright
from protobuf.build.cardData import v3_pb2


########### TYPES #############
class SubjectProto(TypedDict):
    id: str
    total: int
    other: dict[str, Any]


class ReportData(TypedDict):
    images: dict[str, str]
    personal: dict[str, str]
    sem_data: dict[int, dict[str, SubjectProto]]


########### UTILS #############


def writeBegin(user: User, token: str) -> bool:
    with RedisConnection(RedisDataBase.CARD_WRITE_TOKEN) as redis:
        key = encrypt_key(generate_key(DES_3_KEY_SIZE))
        return redis.setDict(
            token, dict(WriteToken(ID=user.id, processing=True, key=key))
        )


def writeEnd(token: str) -> bool:
    with RedisConnection(RedisDataBase.CARD_WRITE_TOKEN) as redis:
        return redis.unset(token)


def getReport(
    sem_dict: dict[str, SubjectMeta],
    task: TaskTable,
    id: int,
    idx: str,
    compress: bool = False,
) -> ReportData:
    records = DataTable.get_complete_data(task, id, idx)

    personal_data: dict[str, str] = {}
    image_data: dict[str, str] = {}
    sem_data: dict[int, dict[str, SubjectProto]] = {}

    for column, values in records.data.items():
        if column[-1] == "I":
            image_data[column[:-1]] = compress_image(values) if compress else values
        else:
            subData = column[:-1].split("_")

            if (sub := subData[0]) in sem_dict and (len(subData) == 2):
                semester = sem_dict[sub]["sem"]
                key = subData[1].lower()

                if semester not in sem_data:
                    sem_data[semester] = {}

                if sub not in sem_data[semester]:
                    sem_data[semester][sub] = SubjectProto(
                        id=sem_dict[sub]["id"], total=sem_dict[sub]["marks"], other={}
                    )

                sem_data[semester][sub]["other"].update({key: values})
            else:
                personal_data[column[:-1]] = values

    sem_data = {key: sem_data[key] for key in sorted(sem_data.keys())}

    return ReportData(images=image_data, sem_data=sem_data, personal=personal_data)


def getProtoReport(report: ReportData, header: PostIdDict, schema: int):
    cardData = v3_pb2.CardData()

    cardData.header.CopyFrom(v3_pb2.Header(**header, schema=schema))

    for i, j in report["personal"].items():
        cardData.personal[i] = j

    for i, j in report["images"].items():
        cardData.image[i] = b64decode(j)

    semDict: dict[int, v3_pb2.Subject] = {}

    for key, val in report["sem_data"].items():
        if key not in semDict:
            semDict[key] = v3_pb2.Subject()

        for subject, meta in val.items():
            """key: semester, x: subject, y: [marks, total]"""
            cardData.semester[key].subject[subject].CopyFrom(v3_pb2.Meta(**meta))

    return cardData.SerializeToString()


########### HTTP Request #############
@login_needed()
@require_http_methods(["GET"])
@semester_permission_check
def sem_view(req: HttpRequest, id: int, idx: int, rowID: int):
    if is_auth_get(req):
        return render(
            req, "Report/HTML/sem.index.html", {"id": id, "idx": idx, "rowID": rowID}
        )


@login_needed()
@require_http_methods(["GET"])
@task_permission_check
def index_view(req: HttpRequest, id: int, idx: str):
    if is_auth_get(req):
        return render(
            req,
            "Report/HTML/index.html",
            {
                "id": id,
                "idx": idx,
                **get_post(get_user(req)),
                "isManager": is_manager(get_user(req)),
            },
        )


@require_http_methods(["GET"])
@aauth_needed()
@async_task_permission_check  # type: ignore
async def generate_report(req: HttpRequest, id: int, idx: str):
    if is_auth_get(req):
        schema_id = req.GET.get("schema", "")
        user = get_user(req)
        pdf_bytes = io.BytesIO()

        try:
            async with (
                AsyncRedisConnection(RedisDataBase.PDF_TOKEN) as redis,
                async_playwright() as p,
            ):
                token = hash_token(get_token(), user.id)
                await redis.setDict(token, dict(PdfToken(ID=user.id, processing=True)))

                browser = await p.chromium.launch()
                page = await browser.new_page()

                await page.set_extra_http_headers(
                    {ACCESS_PDF: settings.ACCESS_PDF, ACCESS_TOKEN: token}
                )
                await page.goto(
                    (
                        f"{req.scheme}://{settings.WEBSITE_HOST}{reverse('Report:pdf', kwargs={'id': id, 'idx': idx, 'token': token})}?schema={schema_id}"
                    )
                )

                _pdf_bytes = await page.pdf(
                    format="A4",
                    print_background=True,
                    margin={
                        "top": "10mm",
                        "bottom": "10mm",
                        "left": "10mm",
                        "right": "10mm",
                    },
                    display_header_footer=False,
                    scale=1.0,
                )

                pdf_bytes.write(_pdf_bytes)

                pdf_bytes = await addSign(pdf_bytes, get_user(req))  # type: ignore
                pdf_bytes.seek(0)

        except Exception as e:
            APP_LOG.write_error(
                LogStructure().set_request(req, LogType.EXCEPTION).set_error(e)
            )

        return FileResponse(
            pdf_bytes,
            as_attachment=True,
            filename=f"Report-{id}-{idx}-{(schema_id or 'default')}.pdf",
        )


@pdf_access
@require_http_methods(["GET"])
@token_check(RedisDataBase.PDF_TOKEN, close_after=False)
@login_needed()
@task_permission_check
def pdf_report(req: HttpRequest, id: int, idx: str, token: str):
    context = {"id": id, "idx": idx}
    user = get_user(req)

    if is_auth_get(req):
        schema_id = req.GET.get("schema", "")

        try:
            task: TaskTable = req.__getattribute__("task")
            sem_dict = Subject.getSubjects(schema_id, post["branch"])  # type: ignore
            """ post is NullStr cause logging, but don't worry it's int in this context """

            report_data = getReport(sem_dict, task, id, idx)

            schema_details = Schema.getSchema(schema_id)
            report_data = getReport(sem_dict, task, id, idx)
            columns: dict[int, set[str]] = {}

            for sem, subs in report_data["sem_data"].items():
                if sem not in columns:
                    columns[sem] = set()

                for meta in subs.values():
                    columns[sem].update(meta["other"].keys())

            context.update(report_data)
            context.update(schema_details)
            context.update(get_post(user))
            context.update({"timestamp": timezone.now().strftime("%d/%m/%Y, %H:%M:%S")})
            context.update({"columns": columns, "schema": schema_id})

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Report/HTML/generated.report.html", context=context)


############ HTMX Request ############
@auth_needed()
@require_http_methods(["GET"])
@htmx_response
def htmx_schema(req: HttpRequest):
    context: dict[str, list[tuple[int, str]]] = {"options": []}
    user = get_user(req)

    if is_hx_get(req):
        try:
            post = get_post_id(user)
            schemas = (
                Schema.objects.filter(branch__id=post["branch"])
                .only("id", "name")
                .values("id", "name")
            )
            options: list[tuple[int, str]] = []

            for schema in schemas.iterator():
                id: int = int(schema["id"])
                name: str = str(schema["name"])

                options.append((id, name))

            context["options"] = options

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Report/HTMX/schema.html", context=context)


@auth_needed()
@require_http_methods(["GET"])
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

            sem_dict = Subject.getSubjects(schema_id, post["branch"])  # type: ignore

            schema_details = Schema.getSchema(schema_id)
            report_data = getReport(sem_dict, task, id, idx)

            columns: dict[int, set[str]] = {}

            for sem, subs in report_data["sem_data"].items():
                if sem not in columns:
                    columns[sem] = set()

                for meta in subs.values():
                    columns[sem].update(meta["other"].keys())

            context.update(report_data)
            context.update(schema_details)
            context.update({"timestamp": timezone.now().strftime("%d/%m/%Y, %H:%M:%S")})
            context.update({"columns": columns, "schema": schema_id})
        except InvalidSchema as f:
            messages.error(req, f.get_error())

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/report.html", context=context)


@htmx_response
@require_http_methods(["GET", "POST"])
@auth_needed()
@task_permission_check
def htmx_feedBack(req: HttpRequest, id: int, idx: str):
    context = {"id": id, "idx": idx, "form": CompleteFeedBackView()}
    user = get_user(req)
    task: TaskTable = req.__getattribute__("task")

    if is_hx_get(req) and is_admin(user):
        try:
            records = DataTable.get_complete_feed(task, id, idx)
            context.update(
                {
                    "form": CompleteFeedBackView(
                        initial={
                            "status": get_string_value(records.status),
                            "locked": get_string_value(records.locked),
                            "issued": get_string_value(records.issued),
                        }
                    )
                }
            )

        except ValueError as f:
            messages.error(req, str(f))

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/complete/admin.form.html", context=context)

    elif is_hx_get(req) and is_manager(user):
        try:
            records = DataTable.get_complete_feed(task, id, idx)
            context.update(
                {
                    "form": CompleteFeedBack(
                        initial={
                            "status": get_string_value(records.status),
                            "locked": get_string_value(records.locked),
                            "issued": get_string_value(records.issued),
                        }
                    )
                }
            )

        except InvalidSchema as f:
            setSwalAlert(context, f.get_error(), title="Feedback Fetch")

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            setSwalAlert(context, DEFAULT_ERROR, title="Feedback Fetch")

        return render(req, "Report/HTMX/complete/manager.form.html", context=context)

    elif is_hx_post(req) and is_manager(user):
        try:
            form = CompleteFeedBack(req.POST)
            setSwalAlert(context, title="Feedback Status")

            with transaction.atomic():
                if form.is_valid():
                    locked: Literal["true", "false"] = str(
                        form.cleaned_data.get("locked")
                    )  # type: ignore
                    status: Literal["true", "false", "none"] = str(
                        form.cleaned_data.get("status")
                    )  # type: ignore
                    issued: Literal["true", "false"] = str(
                        form.cleaned_data.get("issued")
                    )  # type: ignore

                    updated = DataTable.set_complete_feed(
                        task,
                        id,
                        idx,
                        locked=get_2_value(locked),
                        status=get_3_value(status),
                        issued=get_2_value(issued),
                    )

                    setSwalAlert(
                        context,
                        f"Status of {updated} records was updated successfully",
                        "success",
                    )
                    APP_LOG.write_info(
                        LogStructure()
                        .set_request(req, LogType.DATA_EDIT, rowID=idx)
                        .set_meta(req)
                    )

                else:
                    setSwalAlert(context, form.getErrors())

        except Exception as e:
            SMTP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
                .get_log()
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Report/HTMX/message.html", context=context)


@htmx_response
@auth_needed()
@require_http_methods(["GET"])
@task_permission_check
def sem_report_view(req: HttpRequest, id: int, idx: int, rowID: int):
    context: dict[str, Any] = {"id": id, "idx": idx, "rowID": rowID}

    if is_hx_get(req):
        try:
            records = DataTable.objects.get(taskID__id=id, semester=idx, id=rowID)

            context.update({"result": records.data})

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            messages.error(req, "Data Fetching Failed")

        return render(req, "Report/HTMX/sem.report.html", context=context)


@htmx_response
@require_http_methods(["GET", "POST"])
@auth_needed()
@semester_permission_check
def sem_feed_view(req: HttpRequest, id: int, idx: int, rowID: int):
    context: dict[str, Any] = {
        "id": id,
        "idx": idx,
        "rowID": rowID,
        **setSwalAlert(title="Feedback status"),
    }
    user = get_user(req)

    if is_hx_post(req) and is_manager(get_user(req)):
        f = FeedBackForm(req.POST)

        try:
            if f.is_valid():
                status = f.cleaned_data.get("status")
                feedBack = f.cleaned_data.get("feedBack")
                locked = f.cleaned_data.get("locked")
                issued = f.cleaned_data.get("issued")

                data = DataTable.objects.get(taskID__id=id, semester=idx, id=rowID)
                data.status = get_3_value(status)  # type: ignore
                data.feed = feedBack
                data.locked = get_2_value(locked)  # type: ignore
                data.issued = get_2_value(issued)  # type: ignore
                data.save()

                setSwalAlert(
                    context,
                    f"Status for Row ID: {rowID} was updated successfully",
                    "success",
                )
                APP_LOG.write_info(
                    LogStructure()
                    .set_request(req, LogType.DATA_EDIT, semester=idx, rowID=rowID)
                    .set_meta(req)
                )

            else:
                setSwalAlert(context, f.getErrors())

        except DataTable.DoesNotExist:
            setSwalAlert(context, f"RowID: '{rowID}' does not exits")

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Report/HTMX/message.html", context)

    elif is_hx_get(req) and is_manager(user):
        try:
            data = DataTable.objects.get(taskID__id=id, semester=idx, id=rowID)
            status = get_string_value(data.status)
            feedBack = data.feed
            locked = get_string_value(data.locked)
            issued = get_string_value(data.issued)

            context["form"] = FeedBackForm(
                initial={
                    "status": status,
                    "feedBack": feedBack,
                    "locked": locked,
                    "issued": issued,
                }
            )

        except DataTable.DoesNotExist:
            messages.error(req, f"RowID: '{rowID}' does not exits")

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/sem/manager.form.html", context=context)

    elif is_hx_get(req) and is_admin(get_user(req)):
        try:
            data = DataTable.objects.get(taskID__id=id, semester=idx, id=rowID)
            status = data.status
            feedBack = data.feed
            locked = data.locked
            issued = data.issued

            context["form"] = FeedBackView(
                initial={
                    "status": get_string_value(status),
                    "feedBack": feedBack,
                    "locked": get_string_value(locked),
                    "issued": get_string_value(issued),
                }
            )

        except DataTable.DoesNotExist:
            messages.error(req, f"RowID: '{rowID}' does not exists")

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Report/HTMX/sem/admin.form.html", context=context)


@htmx_response
@require_http_methods(["GET", "DELETE"])
@auth_needed(manager_only=True)
@task_permission_check
def issue_view(req: HttpRequest, id: int, idx: str):
    user = get_user(req)
    context = {"id": id, "idx": idx, **setSwalAlert(title="Card Issue Request")}

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

            context["url"] = req.build_absolute_uri(
                reverse(
                    "Card:writeBase",
                    kwargs={"id": id, "idx": idx, "token": token, "schema": schema},
                )
            )
            context["ws"] = f"/ws/write/{id}/{idx}/{token}/"
            context["path"] = settings.WRITE_REGISTRY
            context["ok"] = True  # type: ignore

            setSwalAlert(
                context,
                "Issuing of Card is possible. Would you like to proceed?",
                "info",
            )

        except RedisFailed as r:
            setSwalAlert(context, r.get_error())

        except Schema.DoesNotExist:
            setSwalAlert(context, "Chosen schema does not exist")

        except InvalidSchema as g:
            setSwalAlert(context, g.get_error())

        except DataNotLocked as f:
            setSwalAlert(context, f.get_error())

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Report/HTMX/write/begin.html", context=context)

    elif is_hx_delete(req):
        try:
            writeToken = req.session[WRITE_TOKEN]
            token = hash_token(writeToken, user.id)
            setFlag = writeEnd(token)

            if not setFlag:
                raise RedisFailed()

            setSwalAlert(context, "Issuing of Card is stopped", "info")

        except RedisFailed as r:
            setSwalAlert(context, r.get_error())

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Report/HTMX/write/end.html", context=context)
