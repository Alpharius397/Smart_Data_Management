from User.models import User
from django.db.models import ForeignKey,CharField,Model,RESTRICT,DateTimeField # type: ignore
from Card.models import Card
from django.utils import timezone # type: ignore

class razorPayment(Model):
    user = ForeignKey(to=User,on_delete=RESTRICT, verbose_name="Username")
    order_id = CharField(max_length=255, verbose_name="Order ID",null=False,blank=False,unique=True)
    payment_id = CharField(max_length=255, verbose_name="Payment ID",null=False,blank=False,unique=True)
    cardID = ForeignKey(to=Card,on_delete=RESTRICT,verbose_name="CardID")
    timestamp = DateTimeField(default=timezone.now, blank=False, null=False, verbose_name="Timestamp")
    
    def __str__(self):
        return f"{self.user}:{self.cardID.cardID} => [{self.order_id}:{self.payment_id}]"