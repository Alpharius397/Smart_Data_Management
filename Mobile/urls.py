from django.urls import path, re_path, include

app_name = "Mobile"
urlpatterns = [
    path("auth/", include("Mobile.Auth.urls")),
    path("card", include("Mobile.Cards.urls")),
    path("change/", include("Mobile.Change.urls")),
]
