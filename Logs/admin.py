from django.contrib import admin
from Logs.models import LogMessage # type: ignore
from django.db.models import Q, QuerySet # type: ignore
from User.models import User, get_user, is_admin


@admin.register(LogMessage)
class CardAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "branchID", "userID", "logType")
    search_fields = ("timestamp", "branchID", "userID", "logType")

    def get_queryset(self, request) -> QuerySet:
        user: User = get_user(request)

        if is_admin(user):
            return LogMessage.objects.filter(Q(branchID=user.role.belongs.id))
        
        elif user.is_superuser:
            return LogMessage.objects.all()

        return LogMessage.objects.none()