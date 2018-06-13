from django.shortcuts import render, HttpResponse, redirect, reverse
from webadmin.views_dir import pub
from webadmin import models
from django.http import JsonResponse
from django.db import connection
from webadmin.forms import user
import json
from webadmin.forms.form_cover_update_jifei import jifeiupdateForm
from django.db.models import F
from django.db.models import Q
from webadmin.views_dir.wenda.message import AddMessage
from django.db.models import Count,Sum
import os
import time
from wenda_celery_project import tasks
import datetime
from webadmin.views_dir import pub


def according_geturl(request):
    response = pub.BaseResponse()
    url = request.GET.get('url')
    # url = 'https://zhidao.baidu.com/question/1674396040757875467.html'
    # objs = models.WendaRobotTask.objects.filter(wenda_url=url)
    objs = models.RobotAccountLog.objects.filter(wenda_robot_task__wenda_url=url)

    if objs:
        data_list = []
        print('objs = = >',objs)

        for obj in objs:
            phone = obj.phone_num
            status = obj.get_status_display()
            # print('obj ----- > ',phone)
            data_list.append({
                'phone':phone,
                'statu':status
            })
        # print('data_list = = >',data_list)
        response.code = 200
        response.data = data_list
        response.message = '查询成功'
        # return HttpResponse('查询成功')
    else:
        response.message = '链接不存在'
        # return HttpResponse('链接不存在')
    return JsonResponse(response.__dict__)
