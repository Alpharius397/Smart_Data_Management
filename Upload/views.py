from asgiref.sync import async_to_sync
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import render  # type: ignore
from django.http import HttpRequest  # type: ignore
from Upload.forms import ExcelForm
from django.db import transaction
from django.db.models import QuerySet
from Logs.loggers import APP_LOG, LogStructure, Task
from constants.constants import DEFAULT_ERROR
from tools.get_image import image_load
from tools.url_auth import (
    htmx_response,
    is_auth_get,
    is_hx_delete,
    is_hx_post,
    auth_needed,
    login_needed,
)
from User.models import get_post_id
from .models import UploadTable, DataTable
from University.models import Subject
from django.contrib import messages  # type: ignore
import pandas as pd  # type: ignore
from tools.utils import processSubjects
from University.errors import SubjectsNotDefined
from .errors import (
    FileDoesNotExists,
    FileLocked,
    FileNameExists,
    FileProcessFailed,
    InvalidForm,
)


@login_needed(admin_only=True)
def upload_screen(req: HttpRequest):
    if is_auth_get(req):
        f = ExcelForm(initial={"username": req.user.username})

        return render(req, "Upload/upload.html", {"form": f})


@login_needed(admin_only=True)
def edit_screen(req: HttpRequest, id: int):
    if is_auth_get(req):
        context = {"id": id, "form": ExcelForm()}

        try:
            file_name = UploadTable.objects.get(id=id).fileName
            context["form"] = ExcelForm(
                initial={"username": req.user.username, "file_name": file_name}
            )

        except UploadTable.DoesNotExist:
            messages.error(req, FileDoesNotExists(id).get_error())

        except Exception as f:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=f)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Upload/edit.html", context=context)


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


@htmx_response
@auth_needed(admin_only=True)
def delete(req: HttpRequest, id: int):
    if is_hx_delete(req):
        try:
            files = UploadTable.objects.filter(id=id, data__locked=True).only("id")

            if files.exists():
                raise FileLocked(id)

            file = UploadTable.objects.get(id=id)
            file.delete()
            messages.success(req, "File was deleted successfully")

        except UploadTable.DoesNotExist:
            messages.error(req, FileDoesNotExists(id).get_error())

        except FileLocked as e:
            messages.error(req, e.get_error())

        except Exception as f:
            APP_LOG.write_error(
                LogStructure()
                .set_request(req)
                .set_description(type=Task.EXCEPTION, user=req.user, exception=f)
            )
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Upload/HTMX/message.html")


@htmx_response
@auth_needed(admin_only=True)
def upload(req: HttpRequest):
    if is_hx_post(req):
        form = ExcelForm(req.POST, req.FILES)
        pd_data: pd.DataFrame = pd.DataFrame()
        image_id: list[int] = []
        post = get_post_id(req.user)

        try:
            with transaction.atomic():
                if not form.is_valid():
                    raise InvalidForm()

                excel_file = req.FILES["file"]
                file_name: str = form.cleaned_data.get("file_name", "")

                assert isinstance(excel_file, UploadedFile), "Incompatible File Type!"

                if UploadTable.objects.filter(fileName=file_name).exists():
                    raise FileNameExists()

                with excel_file.open() as file:
                    image_id, pd_data = image_load(file.read())

                    if pd_data.empty:
                        raise FileProcessFailed()

                branchSubjects = Subject.objects.filter(
                    branch__id=post["branch"]
                ).values("name", "semester")

                if not branchSubjects.exists():
                    raise SubjectsNotDefined(post["branch"])

                pd_data.rename(
                    columns=processSubjects(
                        branchSubjects.iterator(), list(pd_data.columns), image_id
                    ),
                    inplace=True,
                )

                fields = pd_data.columns
                fileObj = UploadTable.objects.create(
                    fileName=file_name, uploader=req.user
                )

                rows: list[DataTable] = []
                for row in pd_data.itertuples(index=False):
                    rowJson = {fields[idx]: str(row[idx]) for idx in range(len(row))}
                    rows.append(DataTable(fileID=fileObj, data=rowJson))

                DataTable.objects.bulk_create(rows)

                messages.success(req, "Excel Uploaded and Processed Successfully")

        except AssertionError as e:
            messages.error(req, str(e))

        except ValueError:
            messages.error(req, FileProcessFailed().get_error())

        except InvalidForm:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(req, str(error))

        except FileNameExists as f:
            messages.error(req, f.get_error())

        except SubjectsNotDefined as g:
            messages.error(req, g.get_error())

        except Exception as e:
            print(e)
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Upload/HTMX/message.html")


@htmx_response
@auth_needed(admin_only=True)
def edit(req: HttpRequest, id: int):
    if is_hx_post(req):
        form = ExcelForm(req.POST, req.FILES)
        pd_data: pd.DataFrame = pd.DataFrame()
        image_id: list[int] = []
        post = get_post_id(req.user)

        try:
            with transaction.atomic():
                if not form.is_valid():
                    raise InvalidForm()

                excel_file = req.FILES["file"]
                file_name: str = form.cleaned_data.get("file_name", "")

                assert isinstance(excel_file, UploadedFile), "Incompatible File Type!"

                fileObjs = UploadTable.objects.filter(id=id, data__locked=True).only(
                    "id"
                )

                if fileObjs.exists():
                    raise FileLocked(id)

                if (
                    UploadTable.objects.filter(fileName=file_name)
                    .exclude(id=id)
                    .exists()
                ):
                    raise FileNameExists()

                with excel_file.open() as file:
                    image_id, pd_data = image_load(file.read())

                    if pd_data.empty:
                        raise FileProcessFailed()

                branchSubjects = Subject.objects.filter(
                    branch__id=post["branch"]
                ).values("name", "semester")

                if not branchSubjects.exists():
                    raise SubjectsNotDefined(post["branch"])

                pd_data.rename(
                    columns=processSubjects(
                        branchSubjects.iterator(), list(pd_data.columns), image_id
                    ),
                    inplace=True,
                )

                fields: list[str] = list(pd_data.columns)
                fileObj = UploadTable.objects.get(id=id)
                fileObj.fileName = file_name

                rows: QuerySet[DataTable] = fileObj.data.all()  # type: ignore
                count = 0
                rowLimit = rows.count()

                updateRow: list[DataTable] = []
                createRow: list[DataTable] = []

                for row in pd_data.itertuples(index=False):
                    rowJson: dict[str, str] = {
                        fields[i]: str(row[i]) for i in range(len(row))
                    }

                    if count < rowLimit:
                        updateRow.append(rows[count].update_data(rowJson))
                        count += 1
                    else:
                        createRow.append(DataTable(fileID=fileObj, data=rowJson))

                async_to_sync(DataTable.objects.abulk_update)(
                    updateRow,
                    fields=[
                        "data",
                        "issued",
                        "locked",
                        "time_of_issue",
                        "time_of_lock",
                        "status",
                        "feed",
                    ],
                )

                async_to_sync(UploadTable.objects.abulk_create)(createRow)  # type: ignore
                async_to_sync(fileObj.asave)()

                messages.success(req, "Filed was Edited Successfully")

        except AssertionError as p:
            messages.error(req, str(p))

        except FileLocked as f:
            messages.error(req, f.get_error())

        except FileNameExists as g:
            messages.error(req, g.get_error())

        except SubjectsNotDefined as s:
            messages.error(req, s.get_error())

        except UploadTable.DoesNotExist:
            messages.error(req, FileDoesNotExists(id).get_error())

        except InvalidForm:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(req, str(error))

        except FileProcessFailed as e:
            messages.error(req, e.get_error())

        except Exception as e:
            print(e)
            messages.error(req, DEFAULT_ERROR)

        return render(req, "Upload/HTMX/message.html")
