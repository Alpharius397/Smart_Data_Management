import io
from django.shortcuts import render  # type: ignore
from django.urls import reverse  # type: ignore
from django.http import FileResponse, HttpRequest  # type: ignore
from Card.sockets import getCardData
from Main.settings import settingsInterface as settings
from User.models import (
    get_user,
)
from tools.signer import addSign
from tools.url_auth import (
    pdf_access,
    token_check,
    require_http_methods,
)

from Logs.loggers import APP_LOG, LogStructure, LogType
from tools.utils import (
    setSwalAlert,
    tryCatchThis,
)
from tools.token import hash_token, get_token
from constants import ACCESS_PDF, ACCESS_TOKEN, DEFAULT_ERROR
from Main.models import (
    AsyncRedisConnection,
    PdfToken,
    RedisDataBase,
)
from playwright.async_api import async_playwright
from Mobile.url_auth import (
    acard_owner_check,
    ajwt_required,
    card_owner_check,
    is_auth_get_student,
    astudent_auth_needed,
    student_auth_needed,
)


@require_http_methods(["GET"])  # type: ignore
@ajwt_required  # type: ignore
@astudent_auth_needed  # type: ignore
@acard_owner_check  # type: ignore
async def generate_report(req: HttpRequest, cardID: str):
    if is_auth_get_student(req):
        sem = req.GET.get("sem", "")
        user = get_user(req)
        pdf_bytes = io.BytesIO()

        try:
            async with (
                AsyncRedisConnection(RedisDataBase.PDF_TOKEN) as redis,
                async_playwright() as p,
            ):
                token = hash_token(get_token(), user.id)
                await redis.setDict(token, dict(PdfToken(ID=user.id)))

                browser = await p.chromium.launch()
                page = await browser.new_page()

                await page.set_extra_http_headers(
                    {ACCESS_PDF: settings.ACCESS_PDF, ACCESS_TOKEN: token}
                )
                await page.goto(
                    req.build_absolute_uri(
                        reverse(
                            "Mobile:Mobile-Report:mobilePDF",
                            kwargs={"cardID": cardID, "token": token},
                        )
                        + f"?sem={sem}"
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

                with open("sample/test.pdf", "wb") as f:
                    f.write(pdf_bytes.read())
                pdf_bytes.seek(0)

        except Exception as e:
            APP_LOG.write_error(
                LogStructure().set_request(req, LogType.EXCEPTION).set_error(e)
            )

        return FileResponse(
            pdf_bytes,
            as_attachment=True,
            filename=f"Report-{cardID}-{(sem or 'all')}.pdf",
        )


@pdf_access
@require_http_methods(["GET"])
@token_check(RedisDataBase.PDF_TOKEN, close_after=False)
@student_auth_needed  # type: ignore
@card_owner_check
def mobile_pdf_report(req: HttpRequest, cardID: str, token: str):
    context = {"cardID": cardID}

    if is_auth_get_student(req):
        sem = req.GET.get("sem", "")

        try:
            card = req.__getattribute__("card")
            context.update(getCardData(card, tryCatchThis(int, None)(sem)))

        except Exception as e:
            APP_LOG.write_info(
                LogStructure()
                .set_request(req, LogType.EXCEPTION)
                .set_meta(req)
                .set_error(e)
            )
            setSwalAlert(context, DEFAULT_ERROR)

        return render(req, "Report/HTML/generated.report.html", context=context)
