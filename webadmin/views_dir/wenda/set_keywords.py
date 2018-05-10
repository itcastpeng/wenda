#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms import user
import json

from django.db.models import F
from django.db.models import Q
from webadmin.views_dir.wenda.message import AddMessage


# 指定关键词
@pub.is_login
def set_keywords(request):
    role_id = request.session["role_id"]
    user_id = request.session["user_id"]
    role_names = models.Role.objects.values_list("id", "name")
    status_choices = models.UserProfile.status_choices

    # 营销顾问可以选择跟自己关联的客户
    filter_data = {
        "is_delete": False,
        "status": 1,
        "role_id": 5,
    }

    if role_id not in [1, 4]:  # 如果不是管理员角色和超级管理员角色
        if role_id == 12:
            filter_data["xiaoshou"] = user_id
        else:
            filter_data["guwen_id"] = user_id

    wendaClientUserObjs = models.UserProfile.objects.filter(**filter_data).values('id', 'username')

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = ["id", "client_user_id", "keywords", "create_date", "oper_user", "oper"]
        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column

        q = Q()
        for index, field in enumerate(column_list):
            if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                q.add(Q(**{field: request.GET[field]}), Q.AND)

        objs = models.SearchKeywordsRank.objects.select_related('client_user', 'oper_user').filter(is_delete=False, type=1).filter(q).order_by(order_column)

        result_data = {
            "recordsFiltered": objs.count(),
            "recordsTotal": objs.count(),
            "data": []
        }

        type_choices = models.SearchKeywordsRank.type_choices

        for index, obj in enumerate(objs[start: (start + length)], start=1):

            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""


            oper = ""
            # oper = """
            #     <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="recharge/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="fa fa-jpy" aria-hidden="true"></i>充值</a>
            #     <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="update/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-pencil-square-o"></i>修改</a>
            #     <a class="btn btn-round btn-sm bg-danger" aria-hidden="true" href="delete/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="fa fa-trash-o fa-fw"></i>删除</a>
            # """.format(obj_id=obj.id)

            result_data["data"].append([index, obj.client_user.username, obj.keywords, create_date, obj.oper_user.username, oper])

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, 'wenda/set_keywords/set_keywords_pjax.html', locals())
    return render(request, 'wenda/set_keywords/set_keywords.html', locals())


@pub.is_login
def set_keywords_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]

    response = pub.BaseResponse()

    if request.method == "POST":
        # 添加
        if oper_type == "create":

            keywords = request.POST.get("keywords")
            keywords__client_user_id = request.POST.get("keywords__client_user_id")
            if not keywords:
                response.status = False
                response.message = "关键词不能为空"

            if not keywords__client_user_id:
                response.status = False
                response.message = "请选择客户名称"

            if response.status:
                keywords_list = keywords.strip().split()

                query = []
                for keyword in keywords_list:
                    keyword = keyword.strip()

                    obj = models.SearchKeywordsRank.objects.filter(
                        client_user_id=keywords__client_user_id,
                        keywords=keyword,
                        is_delete=False
                    )

                    if not obj:
                        models.SearchKeywordsRank.objects.create(
                            client_user_id=keywords__client_user_id,
                            type=1,
                            oper_user_id=user_id,
                            keywords=keyword
                        )

                response.status = True
                response.message = "添加成功"

        # 修改
        elif oper_type == "update":
            response.status = True
            response.message = "修改成功"
            print(request.POST.get("id"))

            shouyi_role_ids = [8, 9, 6]
            uid = request.POST.get("id")
            role_id = models.UserProfile.objects.select_related('role').get(id=uid).role.id

            post_data = {}
            for k, v in dict(request.POST).items():
                post_data[k] = v[0]

            print(post_data)
            if role_id not in shouyi_role_ids:
                post_data["xie_wenda_money"] = ''
                post_data["fa_wenda_money"] = ''

            form_obj = user.UserProfileUpdateForm(post_data)

            if form_obj.is_valid():
                if not form_obj.cleaned_data["password"]:
                    del form_obj.cleaned_data["password"]

                print(form_obj.cleaned_data)

                models.UserProfile.objects.filter(id=request.POST.get("id")).update(**form_obj.cleaned_data)
            else:
                response.status = False
                print(form_obj.errors)
                for i in ["username", "password", "role_id", "xie_wenda_money", "fa_wenda_money"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break

        # 删除用户
        elif oper_type == "delete":
            user_profile_obj = models.UserProfile.objects.get(id=o_id)
            user_profile_obj.is_delete = True
            user_profile_obj.save()

            response.status = True
            response.message = "删除成功"

        return JsonResponse(response.__dict__)

    else:
        roles_dict = models.Role.objects.all().values("id", "name")

        # 添加
        if oper_type == "create":
            return render(request, 'wenda/set_keywords/set_keywords_modal_create.html', locals())

        # 修改
        elif oper_type == "update":
            user_profile_obj = models.UserProfile.objects.select_related("role").get(id=o_id)
            guwen_objs = models.UserProfile.objects.filter(role_id=7, is_delete=False)
            xiaoshou_objs = models.UserProfile.objects.filter(role_id=12, is_delete=False)

            # 问答编辑、问答渠道、兼职发帖角色的id
            print(user_profile_obj.role.id)
            shouyi_role_ids = [8, 9, 6]

            return render(request, 'myadmin/user_management/user_management_modal_update.html', locals())

        # 删除
        elif oper_type == "delete":
            user_profile_obj = models.UserProfile.objects.get(id=o_id)
            return render(request, 'wenda/set_keywords/set_keywords_modal_delete.html', locals())
