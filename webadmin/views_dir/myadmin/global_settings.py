#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms.global_settings import GlobalSettingsForm
import json

from django.db.models import F, Q


# 全局设置
@pub.is_login
def global_settings(request):

    if request.method == "POST":

        response = pub.BaseResponse()

        if request.GET["oper_type"] == "update":

            form_obj = GlobalSettingsForm(request.POST)
            if form_obj.is_valid():

                response.status = True
                response.message = "保存成功"

                models.GlobalSettings.objects.update(**form_obj.cleaned_data)
                obj = models.GlobalSettings.objects.values('fugaibaobiao_shengcheng_moshi')
                obj_status = obj[0]['fugaibaobiao_shengcheng_moshi']
            else:
                response.status = False
                for i in ["new_wenda_money", "old_wenda_money", "xie_wenda_money", "fa_wenda_money"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break

        return JsonResponse(response.__dict__)
    else:

        global_settings_obj = models.GlobalSettings.objects.all()[0]

        if "_pjax" in request.GET:
            return render(request, 'myadmin/global_settings/global_settings_pjax.html', locals())
        return render(request, 'myadmin/global_settings/global_settings.html', locals())