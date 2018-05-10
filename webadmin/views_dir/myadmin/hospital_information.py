#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms.hospital_information import HospitalInformationForm


# 医院信息
@pub.is_login
def hospital_information(request):
    print(dict(request.session))

    user_id = request.session["user_id"]
    user_profile_obj = models.UserProfile.objects.get(id=user_id)

    hospital_information_objs = models.HospitalInformation.objects.filter(user_id=user_id)

    if hospital_information_objs:
        hospital_information_obj = hospital_information_objs[0]
        print()
        if hospital_information_obj.content_direction:
            content_direction = [int(i) for i in hospital_information_obj.content_direction.split(",")]
        else:
            content_direction = []

        reply_role = [int(i) for i in hospital_information_obj.reply_role.split(",")]

    department_objs = models.Department.objects.all()

    content_direction_choices = models.HospitalInformation.content_direction_choices
    reply_role_choices = models.HospitalInformation.reply_role_choices

    if "_pjax" in request.GET:
        return render(request, 'wenda/hospital_information/hospital_information_pjax.html', locals())
    return render(request, 'wenda/hospital_information/hospital_information.html', locals())


@pub.is_login
def hospital_information_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":
        # 添加
        if oper_type == "update":

            response.status = True
            response.message = "保存成功"

            form_obj = HospitalInformationForm(
                data={
                    "name": request.POST.get("name"),
                    "department_id": request.POST.get("department_id"),
                    "web_site": request.POST.get("web_site"),
                    "content_direction": request.POST.getlist("content_direction"),
                    "reply_role": request.POST.getlist("reply_role"),
                    "content_direction_custom": request.POST.get("content_direction_custom"),
                }
            )

            if form_obj.is_valid():
                print(form_obj.cleaned_data)
                hospital_information_objs = models.HospitalInformation.objects.filter(user_id=user_id)
                if not hospital_information_objs:
                    models.HospitalInformation.objects.create(user_id=user_id, **form_obj.cleaned_data)
                else:
                    hospital_information_objs.update(**form_obj.cleaned_data)

            else:
                response.status = False
                for i in ["name", "department_id", "web_site", "content_direction", "reply_role"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        response.key = i
                        break

        return JsonResponse(response.__dict__)
