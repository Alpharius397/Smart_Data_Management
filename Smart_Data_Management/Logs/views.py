from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from Main.models import MongoConnection
from django.db.models import Q
from django.urls import reverse
from django.conf import settings
from User.models import get_post_id, get_user_by_id, is_authenticated, is_admin, is_manager, get_manager_by_name, get_admin_by_name
from tools.url_auth import *
from tools.encrypt import decrypt_data
import typing
from PIL import Image
import re
from Main.models import *
from django.contrib.auth.models import User
from Logs.loggers import AppLogger, DEFAULT_ERROR
from Logs.models import LogMessage
from datetime import datetime
from User.models import Manager, Admin
from Logs.forms import DateForm, LogQuery


MAX_RECORD:int = 5

def log_board(req: HttpRequest) -> HttpResponse:
    if(not (is_authenticated(req.user))):
        return auth_needed(req)
    
    if(is_auth_get(req)):
        return render(req,'Logs/dash.html',context={'form':DateForm()})

    elif(is_auth_post(req) and is_hx_post(req)):

        f = DateForm(req.POST)
        post = get_post_id(req.user)
        
        context = {}
        query = Q()

        if(f.is_valid()):
            order = f.cleaned_data.get("query",None)
            date_log = f.cleaned_data.get("date",None)
            
            if(order and date_log):
                match(order):
                    case "after": query = Q(timestamp__gte=date_log)
                    case "on": query = Q(timestamp__icontains=date_log)
                    case "before": query = Q(timestamp__lte=date_log)
        
        try:
            managers = list(map(lambda x: x[0], Manager.objects.filter(belongs__id=post.get("branch")).values_list("user_id")))
            admins = list(map(lambda x: x[0], Admin.objects.filter(belongs__id=post.get("branch")).values_list("user_id")))
            all_records:list[datetime] = list(map(lambda x: x[0], LogMessage.objects.filter((query)&(Q(userID__in=admins)|Q(userID__in=managers)) ).values_list("timestamp")))
            
            context['logs'] = sorted(list(set(map(lambda x: x.replace(hour=0,second=0,minute=0,microsecond=0), all_records))), reverse=True)

            
        except Exception as e:
            context['error'] = DEFAULT_ERROR

        return render(req,'Logs/HTMX/log.list.html',context=context)

    return HttpResponse(status=403)

def single_log(req: HttpRequest, date:str) -> HttpResponse:
    
    if(not is_authenticated(req.user)):
        return auth_needed(req)
    
    if(is_auth_get(req)):

        f = LogQuery(req.POST)
        
        post = get_post_id(req.user)
        
        context = {"date":date,"form":f}
        post = get_post_id(req.user)
        
        query = Q(timestamp__icontains=date)

        try:            
            
            managers = list(map(lambda x: x[0], Manager.objects.filter(belongs__id=post.get("branch")).values_list("user_id")))
            admins = list(map(lambda x: x[0], Admin.objects.filter(belongs__id=post.get("branch")).values_list("user_id")))
            all_records = LogMessage.objects.filter((query)&(Q(userID__in=admins)|Q(userID__in=managers))).values()

            if(all_records): context['empty'] = False
            else: context['empty'] = True

            context['column'] = list(map(lambda x: x.name ,LogMessage._meta.fields))
            
        except Exception as e:
            context['error'] = DEFAULT_ERROR
    
        return render(req,'Logs/read.html',context=context)
    
    return HttpResponse(status=403)


def row_query(req: HttpRequest, date:str) -> HttpResponse:
    
    if(is_auth_get(req) and is_hx_get(req)):

        f = LogQuery(req.GET)
        
        page = req.GET.get("page",'0')
        post = get_post_id(req.user)
        
        context = {"date":date,"form":f}
        post = get_post_id(req.user)
        query = Q(timestamp__icontains=date)
        
        value, order = None, None
        if(f.is_valid()):
            order = f.cleaned_data.get("query",None)
            value = f.cleaned_data.get("search",None)
            
            if(order and value):
                match(order):
                    case "fileName": query &= Q(fileName__contains=value)
                    case "index": query &= Q(index__contains=value)
                    case "type": query &= Q(type__contains=value)
                    case "username": query &= Q(username__contains=value)
                    case "authLevel": query &= Q(authLevel__contains=value)
                    case "timestamp": query &= Q(timestamp__contains=f"{date} {value}")
        
        column = list(map(lambda x: x.name ,LogMessage._meta.fields))
        column.remove("id")
        context = {'date':date, "columns":column}

        try:
            page = int(page)
            managers = list(map(lambda x: x[0], Manager.objects.filter(belongs__id=post.get("branch")).values_list("user_id")))
            admins = list(map(lambda x: x[0], Admin.objects.filter(belongs__id=post.get("branch")).values_list("user_id")))
            all_records = LogMessage.objects.filter((query)&(Q(userID__in=admins)|Q(userID__in=managers))).dates("timestamp","day","DESC").values(*column)

            context['empty'] = not bool(all_records)
        
            
        except Exception as e:
            context['error'] = DEFAULT_ERROR
        return render(req,'Logs/HTMX/table.html',context=context)
    
    return HttpResponse(status=403)


def row_search(req: HttpRequest, date:str) -> HttpResponse:
    
    if(is_auth_get(req) and is_hx_get(req)):
        f = LogQuery(req.GET)
        
        page = req.GET.get("page",'0')
        post = get_post_id(req.user)
        
        context = {"date":date,"form":f}
        post = get_post_id(req.user)
        query = Q(timestamp__icontains=date)
        
        value, order = None, None
        if(f.is_valid()):
            order = f.cleaned_data.get("query",None)
            value = f.cleaned_data.get("search",None)
            
            if(order and value):
                match(order):
                    case "fileName": query &= Q(fileName__icontains=value)
                    case "index": query &= Q(index__icontains=value)
                    case "type": query &= Q(type__icontains=value)
                    case "username": query &= Q(username__icontains=value)
                    case "authLevel": query &= Q(authLevel__icontains=value)
                    case "timestamp": query &= Q(timestamp__icontains=f"{date} {value}")
        
        column = list(map(lambda x: x.name ,LogMessage._meta.fields))
        column.remove("id")
        
        context = {'date':date, "columns":column}

        try:
            page = int(page)
            managers = list(map(lambda x: x[0], Manager.objects.filter(belongs__id=post.get("branch")).values_list("user_id")))
            admins = list(map(lambda x: x[0], Admin.objects.filter(belongs__id=post.get("branch")).values_list("user_id")))
            all_records = LogMessage.objects.filter(((query))&(Q(userID__in=admins)|Q(userID__in=managers))).values(*column)

            context['logs'] = sorted(all_records,key=lambda x: x.get("timestamp"),reverse=True)[page:page+MAX_RECORD]
            context['max_record'] = page+MAX_RECORD
            
        except Exception as e:
            context['error'] = DEFAULT_ERROR
        return render(req,'Logs/HTMX/log.row.html',context=context)
    
    return HttpResponse(status=403)