from django.contrib import messages
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.db.models import Q
from Logs.loggers import LogType
from User.models import get_post_id, is_authenticated
from tools.url_auth import *
from Main.models import *
from constants import * 
from Logs.models import LogMessage
from User.models import Manager, Admin
from Logs.forms import DateForm
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractDay

COLUMNS_VALUE = ("timestamp", "taskID", "userID", "authLevel", "logType", "action")
COLUMNS_HEADING = ("Timestamp", "Task ID", "User ID", "Auth Level", "Log Type", "Description")

@login_needed()
def log_board(req: HttpRequest):    
    if(is_auth_get(req)):
        return render(req,'Logs/HTML/dash.html',context={'form':DateForm()})

@auth_needed()
@htmx_response
def get_logs(req: HttpRequest):
    
    if(is_hx_get(req)):

        _page = req.GET.get("page", "0")
        page = 0
        
        f = DateForm(req.GET)
        post = get_post_id(req.user)
        
        context: dict[str, str | int | list] = {}
        query = Q(branchID=post["branch"])

        if(f.is_valid()):
            order: typing.Literal["after", "on", "before"] = f.cleaned_data.get("query",None)
            date_log = f.cleaned_data.get("date",None)

            if(order and date_log):
                match(order):
                    case "after": query = Q(timestamp__gte=date_log)
                    case "on": query = Q(timestamp__icontains=date_log)
                    case "before": query = Q(timestamp__lte=date_log)
        
        try:
            page = int(_page)
        except:
            page = 0
        
        context["page"] = page + MAX_RECORD
        
        try:
            
            all_records = LogMessage.objects.filter((query)&(Q(branchID=post["branch"]))).annotate(
                day=ExtractDay("timestamp"), 
                month=ExtractMonth("timestamp"), 
                year=ExtractYear("timestamp"), 
                ).distinct("day", "month", "year").order_by("day", "month", "year")[page:page+MAX_RECORD]
            
            if(all_records.count() == 0):
                if(page == 0): messages.error(req, "No Logs Found!")
            else:
                logs = all_records.values("day", "month", "year")
                context['logs'] = sorted(logs, reverse=True)
            
        except Exception as e:
            messages.error(req, DEFAULT_ERROR)

        return render(req,'Logs/HTMX/log.list.html',context=context)

@login_needed()
def single_log(req: HttpRequest, year: int, month: int, day: int) -> HttpResponse:
    
    if(is_auth_get(req)):

        context = {"types": [], "columns": [], "day": day, "month": month, "year": year}
        try:            
            context["columns"] = COLUMNS_HEADING
            context["types"] = sorted(LogType())
        except Exception as e:
            context['error'] = DEFAULT_ERROR
    
        return render(req,'Logs/HTML/read.html',context=context)

@auth_needed()
@htmx_response
def search_log(req: HttpRequest, year: int, month: int, day: int) -> HttpResponse:
    
    if(is_hx_get(req)):

        post = get_post_id(req.user)
        _page = req.GET.get("page",'0')
        
        post = get_post_id(req.user)
        
        try:
            page = int(_page)
        except:
            page = 0
        
        context = { "day": day, "month": month, "year": year, "page": page+MAX_RECORD }

        query = Q(branchID=post["branch"]) & Q(timestamp__day=day) & Q(timestamp__month=month) & Q(timestamp__year=year)

        search = req.GET.get("search",None)
        column: typing.Literal['userID', 'action', 'branchID'] = req.GET.get("column",None)
        level: typing.Literal["Unknown", "Student", "Manager", "Admin"] = req.GET.get("level", None)
        logType = req.GET.get("logType", None)
        
        match(column):
            case 'userID': query &= Q(userID__icontains=search)
            case 'branchID': query &= Q(taskID__icontains=search)
            case 'action': query &= Q(action__icontains=search)

        if(level):
            query &= Q(authLevel=level)
            
        if(logType):
            value: NullStr = None
            
            try:
                value = LogType().__getattribute__(logType)
                query &= Q(logType=value)
            except:
                pass
            
        
        try:            
            
            all_records = LogMessage.objects.filter((query)).order_by("-timestamp")[page:page+MAX_RECORD]
            if(all_records.count() == 0):
                if(page == 0): messages.error(req, "No Logs Found!")
            else:
                logs = all_records.values_list(*COLUMNS_VALUE)
                context['logs'] = logs

        except Exception as e:
            print(e)
            messages.error(req, DEFAULT_ERROR)
    
        return render(req,'Logs/HTMX/log.row.html',context=context)
    
