from django.db.models import CharField,RESTRICT,OneToOneField,ForeignKey,Model,SET_NULL,IntegerField,RESTRICT
from django.core.validators import MinValueValidator, RegexValidator

MongoID = RegexValidator(r"^[0-9a-f]{24}$", message="Invalid MongoID")


class Card(Model):
    cardID = CharField(max_length=200,null=False,blank=False,verbose_name='Card ID')
    mongoID = CharField(max_length=24,null=False,blank=False,verbose_name='Mongo ID', validators=[MongoID])
    rowIndex = IntegerField(null=False,blank=False,verbose_name='Location',validators=[MinValueValidator(0,"Row Index cannot be negative")])
    
    class Meta:
        verbose_name = "Card"
        verbose_name_plural = "Cards"
    
    def __str__(self):
        return f"{self.cardID} => {self.mongoID}:{self.rowIndex}"
