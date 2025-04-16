import json
from django.http import HttpRequest, JsonResponse
from Logs.loggers import DEFAULT_ERROR
from Mobile.models import razorPayment
from User.models import is_student, Student
from django.db.models.expressions import Q
from tools.url_auth import AccessPayLoad, PayLoad, RefreshPayLoad, is_auth_get, is_auth_post, is_auth_put, jwt_required, noneCheck
from django.contrib.auth.models import User
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.forms import ValidationError

def getTokens(req: HttpRequest) -> dict[str, str]:
    return {'access': req.headers.get("access", ''), 'refresh': req.headers.get("refresh", '')}

@csrf_exempt
def mobile_login(req: HttpRequest) -> JsonResponse:
    if(req.method=="POST"):
        
        response = {'status':False, 'error':None, 'access':None, 'refresh':None}
        
        try:
            body:dict[str, str] = json.loads(req.body)
            username = req.POST.get('user',body.get('user',None))
            password = req.POST.get('password',body.get('password',None))

            user = User.objects.get(username=username)
            
            if(is_student(user) and user.check_password(password)):
                response['access'] = AccessPayLoad(user).getToken()
                response['refresh'] = RefreshPayLoad(user).getToken()
                response['status'] = True
                return JsonResponse(data=response, safe=False, status=200)
            
            else:
                response['error'] = 'Incorrect Credentials'
                return JsonResponse(data=response, safe=False, status=401)

        except User.DoesNotExist:
            response['error'] = 'Invalid credentials'
            return JsonResponse(data=response, safe=False, status=401)

        except Exception as e:
            print(e)
            response['error'] = DEFAULT_ERROR
            return JsonResponse(data=response, safe=False, status=500)
    
    return JsonResponse(data={'error':DEFAULT_ERROR}, safe=False, status=403)

@csrf_exempt
def mobile_register(req: HttpRequest) -> JsonResponse:
    if(req.method == "POST"):

        try:
            body:dict[str, str] = json.loads(req.body)

            username = req.POST.get('user', body.get('user', None))
            email = req.POST.get('email', body.get('email', None))
            password = req.POST.get('password_1', body.get('password_1', None))
            confirm_password = req.POST.get('password_2', body.get('password_2', None))
            response = {'status': False, 'error': None}
            
            if(noneCheck(username, email, password, confirm_password)):
                response['error'] = "All fields must not be empty"
                return JsonResponse(data=response, safe=False, status=401)
            
            if(confirm_password != password):
                response['error'] = "Passwords don't match"

                return JsonResponse(data=response, safe=False, status=401)
            
            userExists = User.objects.filter(Q(username=username)|Q(email=email)).exists()
            
            if(userExists):
                response['error'] = 'User exists with same username or email'
                return JsonResponse(data=response, safe=False, status=422)
                
            user = User.objects.create_user(username, email,password)
            
            user.clean_fields()
            
            user.save()
            
            Student(user=user).save()

            response['status'] = True
            return JsonResponse(data=response, safe=False, status=200)

        except ValidationError as v:
            errorMsg = ", ".join(v.messages)
            response['error'] = errorMsg
            return JsonResponse(data=response, safe=False, status=401)
            
        except Exception as e:
            response['error'] = DEFAULT_ERROR
            return JsonResponse(data=response, safe=False, status=500)

    return JsonResponse(data={'error': DEFAULT_ERROR}, safe=False, status=403)

@csrf_exempt
@jwt_required
def subscriber(req: HttpRequest):
    if(is_student(req.user) and req.method=="GET"): # Check if user has paid money
        response = {'status':False, 'error': None}
        
        try:
            paymentDone = razorPayment.objects.filter(user=req.user).exists()
            
            if(paymentDone):
                response['status'] = True
                return JsonResponse(data=response, safe=False, status=200)
            else:
                response['error'] = "Payment is missing..."
                return JsonResponse(data=response, safe=False, status=403)
            
        except Exception as e:
            response['error'] = DEFAULT_ERROR
            return JsonResponse(data=response, safe=False, status=500)
        
    if(is_student(req.user) and req.method=="PUT"): # Change payment status
        
        response = {'status':False, 'error': None}
        
        try:
            data:dict[str, str] = json.loads(req.body)
            order_id = data.get("order_id", None)
            payment_id = data.get("payment_id", None)
            
            if(order_id is None):
                response['error'] = "Payment was unsuccessful"
                return JsonResponse(data=response, safe=False, status=422)
            
            paymentDone = razorPayment.objects.filter(user=req.user).exists()
            
            if(paymentDone):
                response['error'] = "Payment is Already Done"
                response['status'] = True
                return JsonResponse(data=response, safe=False, status=409)
            else:
                
                payment = razorPayment(order_id=order_id, payment_id=payment_id, user = req.user)
                payment.save()
                
                response['status'] = True
                return JsonResponse(data=response, safe=False, status=200)
        
        except Exception as e:
            print(e)
            response['error'] = DEFAULT_ERROR
            return JsonResponse(data=response, safe=False, status=500)