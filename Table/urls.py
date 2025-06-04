from django.urls import path
from Table.views import default_view, column_view, row_view, quick_query, assign_form, refresh_row, edit_form, edit_image_form

app_name = "Table"
urlpatterns = [
    path("<int:id>", default_view, name="index"),
    path("<int:id>/columns", column_view, name="column"),
    path("<str:id>/search/", row_view, name="search"),
    path("<str:id>/quick_search/", quick_query, name="suggest"),
    path("<str:id>/assign/", assign_form, name="assign"),
    path("<str:id>/<int:idx>/refresh", refresh_row, name="refresh"),
    path("<str:id>/<int:idx>/edit", edit_form, name="edit_text"),
    path("<str:id>/<int:idx>/edit_image", edit_image_form, name="edit_image"),
]
