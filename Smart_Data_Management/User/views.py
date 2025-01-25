from django.views.generic import ListView
from .models import Manager, Uploader
from University.models import Branch

class MangerOption(ListView):
    model = Manager
    template_name = "manager/option.html"

    def get_queryset(self):
        
        user_id = self.request.GET.get("belongs")
        user:Uploader = None
        
        if(self.request.user.is_authenticated and self.request.user.is_superuser):
        
            if user_id:
                try:
                    user = Uploader.objects.get(pk=user_id)
                except Uploader.DoesNotExist:
                    pass
                if user:
                    branch_id:Branch = user.belongs
                    
                    if(branch_id):
                        return Manager.objects.filter(belongs__id=branch_id.id)

        return Manager.objects.none()
    
    
class UploaderOption(ListView):
    model = Manager
    template_name = "manager/option.html"

    def get_queryset(self):
        
        user_id = self.request.GET.get("belongs")
        user:Uploader = None
        
        if(self.request.user.is_authenticated and self.request.user.is_superuser):
        
            if user_id:
                try:
                    user = Uploader.objects.get(pk=user_id)
                except Uploader.DoesNotExist:
                    pass
                if user:
                    branch_id:Branch = user.belongs
                    
                    if(branch_id):
                        return Manager.objects.filter(belongs__id=branch_id.id)

        return Manager.objects.none()