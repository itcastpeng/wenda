#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms import role
import json, collections


# 角色管理
@pub.is_login
def role_management(request):

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        role_objs = models.Role.objects.select_related("oper_user").all()[start: (start + length)]

        result_data = {
            "recordsFiltered": role_objs.count(),
            "recordsTotal": role_objs.count(),
            "data": []
        }

        for index, obj in enumerate(role_objs, start=1):

            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            oper = """
                <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="update/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-pencil-square-o"></i>修改</a>
                <a class="btn btn-round btn-sm bg-danger" aria-hidden="true" href="delete/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="fa fa-trash-o fa-fw"></i>删除</a>
            """.format(obj_id=obj.id)

            result_data["data"].append([index, obj.name, create_date, obj.oper_user.username, oper])

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, 'myadmin/role_management/role_management_pjax.html', locals())
    return render(request, 'myadmin/role_management/role_management.html', locals())


@pub.is_login
def role_management_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":
        # 添加
        if oper_type == "create":

            response.status = True
            response.message = "添加成功"

            form_obj = role.RoleForm(request.POST)

            if form_obj.is_valid():

                models.Role.objects.create(
                    name=form_obj.cleaned_data["name"],
                    access_rules=form_obj.cleaned_data["access_rules"],
                    oper_user_id=user_id
                )
            else:

                response.status = False
                for i in ["name", "access_rules"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break

        # 修改
        elif oper_type == "update":
            response.status = True
            response.message = "修改成功"
            form_obj = role.RoleForm(request.POST)

            if form_obj.is_valid():
                models.Role.objects.filter(id=o_id).update(**form_obj.cleaned_data)

            else:
                response.status = False
                for i in ["name", "access_rules"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break

        # 删除用户
        elif oper_type == "delete":
            models.Role.objects.get(id=o_id).delete()
            response.status = True
            response.message = "删除成功"

        return JsonResponse(response.__dict__)

    else:
        roles_dict = models.Role.objects.all().values("id", "name")

        # 添加用户
        if oper_type == "create":
            request.session["rights_ids"] = ""
            return render(request, 'myadmin/role_management/role_management_modal_create.html', locals())

        # 修改用户
        elif oper_type == "update":

            role_obj = models.Role.objects.get(id=o_id)
            request.session["rights_ids"] = role_obj.access_rules

            return render(request, 'myadmin/role_management/role_management_modal_update.html', locals())

        # 删除用户
        elif oper_type == "delete":
            role_obj = models.Role.objects.get(id=o_id)
            return render(request, 'myadmin/role_management/role_management_modal_delete.html', locals())

        # 获取权限对应的html代码
        elif oper_type == "jstree_json_data":

            result_data = collections.OrderedDict()
            result_data = sort_rights_data("", result_data)

            # 角色拥有权限的id
            if "rights_ids" in request.session:
                rights_ids = request.session["rights_ids"].split(",")
            else:
                rights_ids = ""

            rights_html = create_rights_html(result_data, rights_ids)

            return HttpResponse(json.dumps(rights_html))


# 对权限进行排序, 并生成 jstree 对应的字典
def sort_rights_data(pid, result_data):

    if not pid:
        rights_obj = models.AccessRules.objects.filter(super_id__isnull=True)
    else:
        rights_obj = models.AccessRules.objects.filter(super_id_id=pid)

    for obj in rights_obj:
        # 表示是最顶层
        if not pid:
            result_data[obj.id] = {
                "name": obj.name,
                "children": collections.OrderedDict()
            }
        else:
            result_data[obj.id] = {
                "name": obj.name,
                "children": collections.OrderedDict()
            }

        pid = obj.id
        sort_rights_data(pid, result_data[obj.id]["children"])

    return result_data


def create_rights_html(rights_dict, rights_ids):

    return_html = []
    for k, v in rights_dict.items():
        temp_html = {
            "text": v["name"],
            "id": k,
            "state": {}
        }
        if str(k) in rights_ids:
            temp_html["state"]["selected"] = True

        if "children" in v and v["children"]:
            temp_html["state"]["opened"] = True
            temp_html["children"] = create_rights_html(v["children"], rights_ids)
        return_html.append(temp_html)
    return return_html

