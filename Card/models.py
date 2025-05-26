from django.db.models import CharField,Model,IntegerField,ForeignKey,RESTRICT # type: ignore
from django.core.validators import MinValueValidator, RegexValidator # type: ignore
from User.models import _User as User 

MongoID = RegexValidator(r"^[0-9a-f]{24}$", message="Invalid MongoID")

class Card(Model):
    cardID = CharField(max_length=200,null=False,blank=False,verbose_name='Card ID',primary_key=True)
    mongoID = CharField(max_length=24,null=False,blank=False,verbose_name='Mongo ID', validators=[MongoID])
    rowIndex = IntegerField(null=False,blank=False,verbose_name='Row Index',validators=[MinValueValidator(0,"Row Index cannot be negative")])
    user:'User' = ForeignKey(to=User,on_delete=RESTRICT,related_name='card',verbose_name="User")
    
    class Meta:
        verbose_name = "Card"
        verbose_name_plural = "Cards"
    
    def __str__(self):
        return f"{self.cardID} => {self.mongoID}:{self.rowIndex}, Done by: {self.user.username}"
    
    @staticmethod
    def attemptSave(cardID: str, mongoID: str, rowIndex: int, user:User) -> bool:
        try:
            Card(cardID=cardID, mongoID=mongoID, rowIndex=rowIndex, user=user).save()
            return True
        except:
            return False
        
    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)
        
