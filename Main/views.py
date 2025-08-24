from pathlib import Path
import posixpath
from typing import Optional
from django.http import HttpRequest, HttpResponse  # type: ignore
from tools.url_auth import media_access
from django.utils.translation import gettext as _  # type: ignore
from django.http import Http404
from django.utils._os import safe_join  # type: ignore


@media_access
def serve_media(
    request: HttpRequest,
    path: str,
    document_root: Optional[str | bytes] = None,
    *args,
    **kwargs,
):
    path = posixpath.normpath(path).lstrip("/")
    fullpath = Path(safe_join(document_root, path))  # type: ignore

    if not fullpath.exists():
        raise Http404(_("“%(path)s” does not exist") % {"path": fullpath})

    response = HttpResponse(status=200)

    response["Content-Type"] = ""  # Let Nginx detect
    response["X-Accel-Redirect"] = "/Media/" + request.path

    return response
