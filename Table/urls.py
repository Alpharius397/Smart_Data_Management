from django.urls import path
from Table.views import *

app_name = "Table"
urlpatterns = [
    path("<int:id>/", complete_view, name="index"),  # For combined View
    path("htmx/<int:id>/columns", column_view, name="htmxColumns"),
    path("htmx/<int:id>/suggest/", sem_suggest_view, name="htmxSuggest"),
    path("htmx/<int:id>/rows/", complete_row_view, name="htmxRows"),
    
    path("<int:id>/<int:idx>/", sem_view, name="semIndex"),  # For Semester View
    path("htmx/<int:id>/<int:idx>/columns", sem_column_view, name="htmxSemColumns"),
    path("htmx/<int:id>/<int:idx>/suggest/", sem_suggest_view, name="htmxSemSuggest"),
    path("htmx/<int:id>/<int:idx>/rows/", sem_row_view, name="htmxSemRows"),
    path("htmx/<int:id>/<int:idx>/<int:rowID>/refresh", sem_refresh_row, name="htmxRefresh"),
    path("htmx/<int:id>/<int:idx>/<int:rowID>/edit", edit_form, name="htmxEdit"),
    path("<int:id>/<int:idx>/<int:rowID>/edit", edit_form, name="edit_text"),
    path("<int:id>/<int:idx>/<int:rowID>/edit_image", edit_image_form, name="edit_image"),
]
