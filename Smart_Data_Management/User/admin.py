from django.contrib import admin
from User.models import Admin, Manager, is_admin, get_post_id
from django.db.models import Q
from University.models import Branch
from django.contrib.auth.models import User
from django.utils.translation import gettext, gettext_lazy as _
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.utils import unquote
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import (AdminPasswordChangeForm,UserChangeForm,UserCreationForm,)
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import router, transaction
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import escape
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

csrf_protect_m = method_decorator(csrf_protect)
sensitive_post_parameters_m = method_decorator(sensitive_post_parameters())

class UniversityFilter(admin.SimpleListFilter):
    title = "University"
    
    parameter_name = "uni"
    
    def lookups(self, request, model_admin: admin.ModelAdmin):
        assign_user:set[tuple[str,str]] = set()

        for i in model_admin.get_queryset(request).all():
            assign_user.add((i.belongs.institute.university.id,i.belongs.institute.university.name))
        
        return list(assign_user)
        
    
    def queryset(self, request, queryset):
        if(self.value() is None): return queryset
        
        id = self.value()
        
        query = Q()
        
        if(id):
            query = query | Q(belongs__institute__university__id=id)
        
        return queryset.filter(query)

@admin.register(Manager)
class ManagerAdmin(admin.ModelAdmin):
    list_filter = (UniversityFilter,)
    search_fields = ('user__username',)
    search_help_text = "Search by username"
    
    def get_queryset(self, request):
        
        if(is_admin(request.user)):
            return Manager.objects.filter(Q(belongs__id=request.user.admin.belongs.id))
        
        return super().get_queryset(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if (db_field.name=="user"):
            
            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                kwargs["queryset"] = User.objects.filter((Q(is_staff=False)|Q(is_superuser=False))&(Q(admin__isnull=False)))&(Q(manager__belongs__id=user))
        
        elif(db_field.name=="belongs"):

            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                kwargs["queryset"] = Branch.objects.filter(id=request.user.admin.belongs.id)
                            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_filter = (UniversityFilter,)
    search_fields = ('user__username',)
    search_help_text = "Search by username"
    
    def get_queryset(self, request):
        
        if(is_admin(request.user)):
            return Admin.objects.filter(Q(belongs__id=request.user.admin.belongs.id))
        
        return super().get_queryset(request)
    
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if (db_field.name=="user"):
            
            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                
                kwargs["queryset"] = User.objects.filter((Q(is_staff=False)|Q(is_superuser=False))&(~(Q(manager__isnull=False)))&(Q(admin__belongs__id=user)))
        
        elif(db_field.name=="belongs"):
            if(is_admin(request.user)):
                user:Admin = request.user.admin.belongs.id
                kwargs["queryset"] = Branch.objects.filter(id=request.user.admin.belongs.id)
                            
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.unregister(User)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    add_form_template = "admin/auth/user/add_form.html"
    change_user_password_template = None

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("username",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )
    
    def get_queryset(self, request):
        
        if(not request.user.is_superuser):
            branch = get_post_id(request.user).get('branch',None)
            
            
            return User.objects.filter((Q(manager__isnull=False)|Q(admin__isnull=False))&(Q(admin__belongs__id=branch)|Q(manager__belongs__id=branch)))
        
        return super().get_queryset(request)

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        
        if(request.user.is_superuser):
            perm_field = ("is_active","is_staff","is_superuser","groups","user_permissions",)
        else:
            perm_field = ("is_active","is_staff",)
            
        
        fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": perm_field,
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
        
        
        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults["form"] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def get_urls(self):
        return [
            path(
                "<id>/password/",
                self.admin_site.admin_view(self.user_change_password),
                name="auth_user_password_change",
            ),
        ] + super().get_urls()

    # RemovedInDjango60Warning: when the deprecation ends, replace with:
    # def lookup_allowed(self, lookup, value, request):
    def lookup_allowed(self, lookup, value, request=None):
        # Don't allow lookups involving passwords.
        return not lookup.startswith("password") and super().lookup_allowed(
            lookup, value, request
        )

    @sensitive_post_parameters_m
    @csrf_protect_m
    def add_view(self, request, form_url="", extra_context=None):
        with transaction.atomic(using=router.db_for_write(self.model)):
            return self._add_view(request, form_url, extra_context)

    def _add_view(self, request, form_url="", extra_context=None):
        # It's an error for a user to have add permission but NOT change
        # permission for users. If we allowed such users to add users, they
        # could create superusers, which would mean they would essentially have
        # the permission to change users. To avoid the problem entirely, we
        # disallow users from adding users if they don't have change
        # permission.
        if not self.has_change_permission(request):
            if self.has_add_permission(request) and settings.DEBUG:
                # Raise Http404 in debug mode so that the user gets a helpful
                # error message.
                raise Http404(
                    'Your user does not have the "Change user" permission. In '
                    "order to add users, Django requires that your user "
                    'account have both the "Add user" and "Change user" '
                    "permissions set."
                )
            raise PermissionDenied
        if extra_context is None:
            extra_context = {}
        username_field = self.opts.get_field(self.model.USERNAME_FIELD)
        defaults = {
            "auto_populated_fields": (),
            "username_help_text": username_field.help_text,
        }
        extra_context.update(defaults)
        return super().add_view(request, form_url, extra_context)

    @sensitive_post_parameters_m
    def user_change_password(self, request, id, form_url=""):
        user = self.get_object(request, unquote(id))
        if not self.has_change_permission(request, user):
            raise PermissionDenied
        if user is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {
                    "name": self.opts.verbose_name,
                    "key": escape(id),
                }
            )
        if request.method == "POST":
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                change_message = self.construct_change_message(request, form, None)
                self.log_change(request, user, change_message)
                msg = gettext("Password changed successfully.")
                messages.success(request, msg)
                update_session_auth_hash(request, form.user)
                return HttpResponseRedirect(
                    reverse(
                        "%s:%s_%s_change"
                        % (
                            self.admin_site.name,
                            user._meta.app_label,
                            user._meta.model_name,
                        ),
                        args=(user.pk,),
                    )
                )
        else:
            form = self.change_password_form(user)

        fieldsets = [(None, {"fields": list(form.base_fields)})]
        admin_form = admin.helpers.AdminForm(form, fieldsets, {})

        context = {
            "title": _("Change password: %s") % escape(user.get_username()),
            "adminForm": admin_form,
            "form_url": form_url,
            "form": form,
            "is_popup": (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            "is_popup_var": IS_POPUP_VAR,
            "add": True,
            "change": False,
            "has_delete_permission": False,
            "has_change_permission": True,
            "has_absolute_url": False,
            "opts": self.opts,
            "original": user,
            "save_as": False,
            "show_save": True,
            **self.admin_site.each_context(request),
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.change_user_password_template
            or "admin/auth/user/change_password.html",
            context,
        )

    def response_add(self, request, obj, post_url_continue=None):
        """
        Determine the HttpResponse for the add_view stage. It mostly defers to
        its superclass implementation but is customized because the User model
        has a slightly different workflow.
        """
        # We should allow further modification of the user just added i.e. the
        # 'Save' button should behave like the 'Save and continue editing'
        # button except in two scenarios:
        # * The user has pressed the 'Save and add another' button
        # * We are adding a user in a popup
        if "_addanother" not in request.POST and IS_POPUP_VAR not in request.POST:
            request.POST = request.POST.copy()
            request.POST["_continue"] = 1
        return super().response_add(request, obj, post_url_continue)