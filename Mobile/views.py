import json
from typing import TypedDict # type: ignore
from django.http import HttpRequest, JsonResponse, QueryDict # type: ignore
from Register.errors import UserExists
from Mobile.forms import RegisterForm
from University.models import Branch
from constants import DEFAULT_ERROR
from Mobile.models import razorPayment
from tools.url_auth import AccessPayLoad, RefreshPayLoad, auth_needed, getRequestToken, is_auth_get_student, is_auth_post_student, is_auth_put_student, jwt_required, noneCheck, read_body_as_json, student_auth_needed # type: ignore
from django.contrib.auth.models import User # type: ignore
from django.db.models import Q # type: ignore
from django.views.decorators.csrf import csrf_exempt # type: ignore
from django.forms import ValidationError # type: ignore
from django.db import transaction # type: ignore
from User.models import User, Role, RoleType, is_student


class LoginResponse(TypedDict):
    status: bool
    error: str | None
    access: str | None
    refresh: str | None

class RegisterResponse(TypedDict):
    status: bool
    error: str | None

class SubscriberResponse(TypedDict):
    status: bool
    error: str | None
    access: str
    refresh: str
    

class SubscriberResponse(TypedDict):
    status: bool
    error: str | None
    access: str
    refresh: str

class CardData(TypedDict):
    cardID: str
    timestamp: str
    

class CardResponse(TypedDict):
    status: bool
    error: str | None
    cards: list[CardData]
    access: str
    refresh: str


@csrf_exempt
@read_body_as_json
def mobile_login(req: HttpRequest) -> JsonResponse:
    if(req.method=="POST"):
        
        response = LoginResponse(status=False, error=None, access=None, refresh=None)
        status: int = 500
        
        try:
            username = req.POST.get('user')
            password = req.POST.get('password')
            user = User.objects.get(username=username)
            
            if(is_student(user) and user.check_password(password)):
                response['access'] = AccessPayLoad(user).getToken()
                response['refresh'] = RefreshPayLoad(user).getToken()
                response['status'] = True
                status = 200
            
            else:
                response['error'] = 'Incorrect Credentials'
                status = 403
                

        except User.DoesNotExist:
            status = 401
            response['error'] = 'Invalid credentials'

        except Exception as e:
            status = 500
            response['error'] = DEFAULT_ERROR
    
        return JsonResponse(data=response, safe=False, status=status)

@csrf_exempt
@read_body_as_json
def mobile_register(req: HttpRequest) -> JsonResponse:
    if(req.method == "POST"):

        response = RegisterResponse(status=False, error=None)
        status = 500
        f = RegisterForm(req.POST)
        
        try:
            with transaction.atomic():
                if f.is_valid():
                    user = f.cleaned_data.get("username", "")
                    email = f.cleaned_data.get("email", "")
                    password = f.cleaned_data.get("password", "")
                    branch = f.cleaned_data.get("branch", "")
                    
                    exists = User.objects.filter(Q(username=user)|Q(email=email)).exists()

                    if(exists): raise UserExists()
                    
                    branchID = Branch.objects.get(id=branch)

                    user = User.objects.create_user(user,email,password,is_active=False)
                    role = Role(user=user, belongs=branchID, role=RoleType.STUDENT)
                    role.save()
                    response['status'] = True
                    status=200
                else:
                    response['error'] = f.getErrors()
                    
        except UserExists as f:
            status = 403
            response['error'] = "Username or Email is already registered!"
        
        except Branch.DoesNotExist as g:
            status = 401
            response['error'] = "Branch was not found!"
        
        except Exception:
            status = 500
            response['error'] = DEFAULT_ERROR
            

        return JsonResponse(data=response, safe=False, status=status)

@csrf_exempt
@jwt_required
@read_body_as_json
@student_auth_needed
def subscriber_check(req: HttpRequest):
    
    response = SubscriberResponse(**{'status':False, 'error': None, **getRequestToken(req)})
    status = 500
    
    if(is_auth_post_student(req)): # Check if user has paid money
        
        try:
            
            cardID = req.GET.get("cardID")
            paymentDone = razorPayment.objects.filter(Q(user=req.user) | Q(cardID__cardID = cardID)).exists()
            
            if(paymentDone):
                response['status'] = True
                status = 200
            else:
                response['error'] = "Payment is missing for this card!"
                status = 403
                
        except Exception as e:
            print(e)
            response['error'] = DEFAULT_ERROR
        
        return JsonResponse(data=response, safe=False, status=status)
    
    elif(is_auth_put_student(req)): # Change payment status
        
        try:
            order_id = req.POST.get("order_id")
            payment_id = req.POST.get("payment_id")
            
            if(not (order_id or payment_id)):
                response['error'] = "Payment was unsuccessful"
                status = 422
            
            paymentDone = razorPayment.objects.filter(user=req.user).exists()
            
            if(paymentDone):
                response['error'] = "Payment is Already Done"
                response['status'] = True
                status = 409
            else:
                payment = razorPayment(order_id=order_id, payment_id=payment_id, user = req.user)
                payment.save()
                
                response['status'] = True
        
        except Exception as e:
            response['error'] = DEFAULT_ERROR

        return JsonResponse(data=response, safe=False, status=status)
    
    
@csrf_exempt
@jwt_required
@read_body_as_json
@student_auth_needed
def available_card(req: HttpRequest):
    
    if(is_auth_get_student(req)): # Check if user has paid money
        
        response = CardResponse(**{'status':False, 'error': None,  "cards": [], **getRequestToken(req)})
        status = 500
        try:
            cards: list[CardData] = []
            available_card = razorPayment.objects.filter(Q(user=req.user)).defer("cardID", "timestamp")
            
            for card in available_card.iterator():
                cards.append(CardData(cardID=card.cardID.cardID, timestamp=card.timestamp.isoformat()))
            
            response['cards'] = cards
            response['status'] = True
            status = 200
                
        except Exception as e:
            response['error'] = DEFAULT_ERROR
        
        return JsonResponse(data=response, safe=False, status=status)
    
    elif(is_auth_post_student(req)): # Change payment status
        
        try:
            order_id = req.POST.get("order_id")
            payment_id = req.POST.get("payment_id")
            
            if(not (order_id or payment_id)):
                response['error'] = "Payment was unsuccessful"
                status = 422
            
            paymentDone = razorPayment.objects.filter(user=req.user).exists()
            
            if(paymentDone):
                response['error'] = "Payment is Already Done"
                response['status'] = True
                status = 409
            else:
                payment = razorPayment(order_id=order_id, payment_id=payment_id, user = req.user)
                payment.save()
                
                response['status'] = True
        
        except Exception as e:
            response['error'] = DEFAULT_ERROR

        return JsonResponse(data=response, safe=False, status=status)