from django.urls import reverse # type: ignore
from Main.settings import settingsInterface as settings
from django.shortcuts import redirect # type: ignore
from django.contrib.auth import logout # type: ignore
from django.http import HttpRequest, HttpResponse # type: ignore
from constants import SUCCESS
from tools.url_auth import require_http_methods

@require_http_methods(['GET'])
def logout_view(req:HttpRequest) -> HttpResponse:
    logout(req)
    return redirect(reverse(settings.LOGIN_URL) + f'?{SUCCESS}=Logout Successfully')