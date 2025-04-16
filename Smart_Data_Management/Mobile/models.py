from django.contrib.auth.models import User
from django.db.models import OneToOneField,CharField,Model,RESTRICT

class razorPayment(Model):
    user = OneToOneField(to=User,on_delete=RESTRICT,related_name='subscriber')
    order_id = CharField(max_length=255, verbose_name="Order ID",null=False,blank=False,unique=True)
    payment_id = CharField(max_length=255, verbose_name="Payment ID",null=False,blank=False,unique=True)

    def __str__(self):
        return f"{self.user} => [{self.order_id}:{self.payment_id}]"