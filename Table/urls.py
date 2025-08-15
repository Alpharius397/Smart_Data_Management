from django.urls import path # type: ignore
from Table.views import complete_view, column_view, suggest_view, complete_row_view, refresh_row, sem_view, sem_column_view, sem_suggest_view, sem_row_view, sem_refresh_row, edit_form, edit_image_form

app_name = "Table"
urlpatterns = [
    path("<int:id>/", complete_view, name="index"),  # For combined View
    path("htmx/<int:id>/columns", column_view, name="htmxColumns"),
    path("htmx/<int:id>/suggest/", suggest_view, name="htmxSuggest"),
    path("htmx/<int:id>/rows/", complete_row_view, name="htmxRows"),
    path("htmx/<int:id>/<str:idx>/", refresh_row, name="htmxRefresh"),
    
    path("<int:id>/<int:idx>/", sem_view, name="semIndex"),  # For Semester View
    path("htmx/<int:id>/<int:idx>/columns", sem_column_view, name="htmxSemColumns"),
    path("htmx/<int:id>/<int:idx>/suggest/", sem_suggest_view, name="htmxSemSuggest"),
    path("htmx/<int:id>/<int:idx>/rows/", sem_row_view, name="htmxSemRows"),
    path("htmx/<int:id>/<int:idx>/<int:rowID>/refresh", sem_refresh_row, name="htmxSemRefresh"),
    path("<int:id>/<int:idx>/<int:rowID>/edit", edit_form, name="htmxSemEditText"),
    path("<int:id>/<int:idx>/<int:rowID>/edit_image", edit_image_form, name="htmxSemEditImage"),
]
