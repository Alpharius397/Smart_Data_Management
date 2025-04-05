from django.contrib import admin
from .models import *

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    search_fields = ('cardID',)
    search_help_text = "Search by card ID"