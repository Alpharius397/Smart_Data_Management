from User.models import is_admin, is_manager, User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

class AdminValidator():
    message = "User must be a admin"
    code = "invalid"
    
    def __call__(self, user:User) -> None:
        
        if(not is_admin(user)):
            raise ValidationError(self.message, code=self.code, params={"value": user})
        
    
class ManagerValidator():
    message = "User must exist and be a manager"
    code = "invalid"
    
    def __call__(self, userID: int) -> None:
        
        try:
            user:User = User.objects.get(id=userID)
            
            if(not is_manager(user)):
                raise ValidationError(self.message, code=self.code, params={"value": user})
        except:
            raise ValidationError(self.message, code=self.code, params={"value": user})