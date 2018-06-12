#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms import edit_content
import json

from django.db.models import F
from django.db.models import Q
from webadmin.views_dir.wenda.message import AddMessage
import datetime
from django.db.models import Count

import os
import time
from wenda_celery_project import tasks

from urllib import parse
import xlrd


# 我的任务-编辑
@pub.is_login
def my_task_edit(request):
    user_id = request.session.get('user_id')
    role_id = request.session.get('role_id')
    print(role_id)

    role_names = models.Role.objects.values_list("id", "name")
    status_choices = models.EditTaskManagement.status_choices

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = [
            "id", "task_id", "number", "status", "task__task__wenda_type", "reference_file_path", "remark",
            "task__create_user_id", "edit_user_id", "create_date", "complete_date", "oper", "task__client_user_id"
        ]
        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column

        q = Q()
        status = request.GET.get("status")

        for index, field in enumerate(column_list):
            if field == "status":
                if request.GET.get("status") == "" or role_id == 14:
                    continue
                q.add(Q(**{field: request.GET.get("status", 1)}), Q.AND)

            elif field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                if field == "complete_date":
                    q.add(Q(**{"complete_date__contains": request.GET[field]}), Q.AND)
                else:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)

        if role_id in [1, 4] or user_id == 69:
            filter_dict = {
                "task__is_delete": False,
                "task__status__lt": 10,      # 已撤销的不显示
            }
        else:
            filter_dict = {
                "task__is_delete": False,
                "task__status__lt": 10,      # 已撤销的不显示
                "edit_user_id": user_id
            }

        objs = models.EditTaskManagement.objects.select_related('task__client_user', 'task__task').filter(**filter_dict).filter(q).order_by(order_column)

        result_data = {
            "recordsFiltered": objs.count(),
            "recordsTotal": objs.count(),
            "data": []
        }

        for index, obj in enumerate(objs[start: (start + length)], start=1):

            create_date = ""
            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")

            complete_date = ""
            if obj.complete_date:
                complete_date = obj.complete_date.strftime("%Y-%m-%d %H:%M:%S")

            reference_file_path = ""
            if obj.task.reference_file_path:
                reference_file_path = """
                    <a href='{reference_file_path}' download="{excel_name}">下载参考资料</a>
                """.format(
                    reference_file_path=obj.task.reference_file_path,
                    excel_name=obj.task.reference_file_path.split("/")[-1],
                )

            oper = ""

            # 如果是等待分配状态,则可以进行分配操作
            if role_id in [13, 14]:
                if obj.status == 1:
                    # if obj.task.task.wenda_type in [1, 10]:# 新问答或新问答补发
                    #     oper += """
                    #         <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="upload/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">
                    #         <i class="icon fa-cloud-upload" aria-hidden="true"></i> 上传任务
                    #         </a>
                    #     """.format(obj_id=obj.id)

                    oper += """
                        <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="upload_file/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">
                        <i class="icon fa-cloud-upload" aria-hidden="true"></i> 上传 excel 表格
                        </a>
                    """.format(obj_id=obj.id)

                else:
                    oper += """
                        <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="search_edit_content/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">
                        <i class="icon fa-search" aria-hidden="true"></i> 查看编写内容
                        </a>
                    """.format(obj_id=obj.id)
            remark_obj =  """
                        <a  href="remark_shuoming/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">
                         任务说明
                        </a>
                    """.format(obj_id=obj.id)
            client_username = "%s-%s" % (obj.task.client_user.username, obj.id)

            number = "%s/%s" % (obj.number, obj.editpublicktaskmanagement_set.filter(status=3).count())

            result_data["data"].append(
                [
                    index, client_username, number, obj.get_status_display(), obj.task.task.get_wenda_type_display(),
                    reference_file_path, obj.task.create_user.username, obj.edit_user.username,
                    create_date, complete_date, remark_obj, oper
                ]
            )
        return HttpResponse(json.dumps(result_data))

    bianji_users = models.UserProfile.objects.filter(is_delete=False, role_id=13)
    client_user_data = models.EditTaskManagement.objects.values('task__client_user_id', 'task__client_user__username').annotate(Count("task__client_user"))
    print(client_user_data)

    wenda_type_choices = models.Task.type_choices

    if "_pjax" in request.GET:
        return render(request, 'wenda/my_task_edit/my_task_edit_pjax.html', locals())
    return render(request, 'wenda/my_task_edit/my_task_edit.html', locals())


@pub.is_login
def my_task_edit_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    role_id = request.session["role_id"]
    response = pub.BaseResponse()

    status_choices = models.EditContentManagement.status_choices

    if request.method == "POST":
        # 添加
        if oper_type == "create":

            client_user_id = request.POST.get('client_user_id')
            remark = request.POST.get('remark')
            number = request.POST.get('number')
            file = request.FILES.get('file')  # 所有提交的文件
            form_data = {
                "client_user_id": client_user_id,
                "remark": remark,
                "number": number,
                "file": file,
            }
            form_obj = edit_content.EditContentForm(form_data)
            if form_obj.is_valid():
                file_name = ".".join([str(int(time.time() * 1000)), file.name.split(".")[1]])
                file_abs_name = os.path.join("statics", "upload_files", file_name)
                with open(file_abs_name, "wb") as f:
                    for chunk in file.chunks():
                        f.write(chunk)

                models.EditContentManagement.objects.create(
                    client_user_id=form_obj.cleaned_data["client_user_id"],
                    create_user_id=user_id,
                    status=1,
                    reference_file_path="/" + file_abs_name,
                    number=form_obj.cleaned_data["number"],
                    remark=form_obj.cleaned_data["remark"]
                )

                response.status = True
                response.message = "添加成功"

            else:
                response.status = False
                for i in ["client_user_id", "number", "file", "remark"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break

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

        elif oper_type == "task_allotment":
            print(request.POST)

            task_obj = models.EditContentManagement.objects.get(id=o_id)

            flag = True
            task_allotment_data = {}
            total = 0
            for i in dict(request.POST):
                if i.startswith("bianji"):
                    pub_num = request.POST.get(i)
                    if (pub_num.isdigit() and int(pub_num) >= 0) or not pub_num:      # 如果是整数类型并且大于等于0 或者为空
                        if pub_num:
                            total += int(pub_num)
                    else:
                        flag = False

                    task_allotment_data[int(i.replace("bianji_", ""))] = request.POST.get(i)

            if not flag or total != task_obj.number:
                response.status = False
                response.message = "分配任务有误"

            else:
                for edit_user_id, number in task_allotment_data.items():
                    print(task_allotment_data, task_allotment_data.values())
                    models.EditTaskManagement.objects.create(
                        task=task_obj,
                        edit_user_id=edit_user_id,
                        number=number,
                        status=1,
                    )

                task_obj.status = 2
                task_obj.save()
                response.status = True
                response.message = "分配成功"

        # 编辑上传任务
        elif oper_type == "upload":
            edit_task_management_obj = models.EditTaskManagement.objects.get(id=o_id)
            form_data = request.POST.get("form_data")
            print("form_data -->", form_data)
            print("json.loads(form_data) -->", json.loads(form_data))

            form_data_obj = json.loads(parse.unquote(form_data).replace("%u", "\\u"))

            print("form_data_obj ->", form_data_obj)

            content_str = form_data_obj["content"]
            title_str = form_data_obj["title"]

            print("content_str -->", content_str)
            print("title_str -->", title_str)

            if not title_str:
                response.status = False
                response.message = "提交问答问题不能为空"

            if response.status and content_str:
                # content_list = [i.strip() for i in content_str.strip().split("\n")]
                # title_list = [i.strip() for i in title_str.strip().split("\n")]

                content_list = [i.strip() for i in content_str.strip().split("\n")]
                print("content_list -->", len(content_list), content_list)
                title_list = [i.strip() for i in title_str.strip().split("\n")]

                # 问题敏感词列表
                SensitiveWordTitle_list = [i[0] for i in models.SensitiveWordLibrary.objects.filter(w_type=1).values_list('name')]

                # 答案敏感词列表
                SensitiveWordContent_list = [i[0] for i in models.SensitiveWordLibrary.objects.filter(w_type=2).values_list('name')]

                content_list_str = " ".join(content_list)
                title_list_str = " ".join(title_list)

                title_err_name_list = []        # 问题中包含的敏感词列表
                content_err_name_list = []      # 答案中包含的敏感词列表
                for name in SensitiveWordTitle_list:
                    if name in title_list_str:
                        title_err_name_list.append(name)

                for name in SensitiveWordContent_list:
                    if name in content_list_str:
                        content_err_name_list.append(name)

                if title_err_name_list or content_err_name_list:
                    response.status = False
                    response.data = {
                        "title_err_name_list": title_err_name_list,
                        "content_err_name_list": content_err_name_list
                    }
                    response.message = "问题或答案中包含敏感词,已标红"

                if response.status and len(set(content_list)) != len(content_list):
                    response.status = False
                    response.message = "提交问答答案有重复"

                if response.status and len(set(title_list)) != len(title_list):
                    response.status = False
                    response.message = "提交问答问题有重复"

                print(len(title_list), len(content_list))
                if response.status and len(title_list) != len(content_list):
                    response.status = False
                    response.message = "提交问答问题与提交问答问题数量不符"

                if response.status:
                    query = []
                    flag = True
                    line_repetition = 0
                    for index in range(len(content_list)):
                        line_repetition += 1

                        content = content_list[index]
                        title = title_list[index]

                        # 判断所有的子任务中是否已经存在该内容
                        for i_obj in models.EditTaskManagement.objects.filter(task_id=edit_task_management_obj.task.id):

                            # 在子任务的详情表中进行查找
                            obj = models.EditPublickTaskManagement.objects.filter(
                                content=content,
                                title=title,
                                task_id=i_obj.id
                            )
                            if obj.count() > 0:
                                flag = False
                                break

                        if not flag:
                            break

                        else:
                            query.append(models.EditPublickTaskManagement(
                                task_id=edit_task_management_obj.id,
                                content=content,
                                title=title,
                                status=1,
                            ))

                    print("query -->", len(query))
                    if not flag:
                        response.status = False
                        response.message = "第 {line_num} 行已经存在".format(
                            line_num=line_repetition
                        )
                    elif flag and len(query) != edit_task_management_obj.number:
                        response.status = False
                        response.message = "提交数量与任务数量不符"

                    else:
                        models.EditPublickTaskManagement.objects.bulk_create(query)

                        edit_task_management_obj.status = 2
                        edit_task_management_obj.complete_date = datetime.datetime.now()
                        edit_task_management_obj.save()

                        # 统计父任务下的子任务是否全部完成
                        edit_content_management_obj = models.EditContentManagement.objects.select_related('create_user').get(id=edit_task_management_obj.task.id)

                        # 该条件如果成立,表示父任务下的所有子任务都已经完成
                        if edit_content_management_obj.edittaskmanagement_set.filter(status=1).count() == 0:
                            edit_content_management_obj.status = 3
                            edit_content_management_obj.save()

                            # 发微信消息告知营销顾问
                            weixin_id = edit_content_management_obj.create_user.weixin_id
                            if not weixin_id:  # 如果没有填写微信id 则告知 zhangcong
                                # 发送微信通知

                                now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                msg = "通知时间: {now_datetime} \n通知平台:诸葛问答\n用户 {username} 未设置微信id".format(
                                    now_datetime=now_datetime,
                                    username=edit_content_management_obj.create_user.username
                                )
                                user_id_str = "zhangcong"
                            else:
                                msg = "您交付给编辑完成的任务都已经完成,请前往问答后台-->编辑内容管理功能中查看"
                                user_id_str = weixin_id
                            tasks.send_msg.delay(user_id_str, msg)

                        response.status = True
                        response.message = "提交成功"

            else:
                response.status = False
                response.message = "提交问答答案不能为空"

        elif oper_type == "upload_file":
            edit_task_management_obj = models.EditTaskManagement.objects.select_related('task__task').get(id=o_id)

            file_obj = request.FILES.get('file')  # 提交的文件
            ext_name = file_obj.name.split(".")[-1]     # 扩展名
            file_name = ".".join([str(int(time.time()) * 1000), ext_name])

            file_abs_name = os.path.join("statics/temp", file_name)

            file_contents = bytes()
            for chunk in file_obj.chunks():
                file_contents += chunk

            # 首先将提交的 excel 表格中的数据读出
            book = xlrd.open_workbook(file_contents=file_contents)
            sh = book.sheet_by_index(0)

            excel_data = []

            url_list = []
            title_list = []
            content_list = []
            for row in range(2, sh.nrows):
                url = sh.cell_value(rowx=row, colx=0)     # 链接
                title = sh.cell_value(rowx=row, colx=1)     # 问题
                content = sh.cell_value(rowx=row, colx=2)     # 答案

                excel_data.append({
                    "url": url,
                    "title": title,
                    "content": content
                })
                url_list.append(url)
                title_list.append(title)
                content_list.append(content)

                if edit_task_management_obj.task.task.wenda_type in [1, 10]:
                    if not title or not content:
                        response.status = False
                        response.message = "上传数据异常"
                        break
                else:
                    if not url or not title or not content:
                        response.status = False
                        response.message = "上传数据异常"
                        break

            print("content_list -->", content_list)
            if response.status:
                # 问题敏感词列表
                if role_id != 14:
                    SensitiveWordTitle_list = [i[0] for i in models.SensitiveWordLibrary.objects.filter(w_type=1).values_list('name')]

                    # 答案敏感词列表
                    SensitiveWordContent_list = [i[0] for i in models.SensitiveWordLibrary.objects.filter(w_type=2).values_list('name')]

                    content_list_str = " ".join(content_list)
                    title_list_str = " ".join(title_list)

                    err_name_list = []  # 问题或答案中包含的敏感词列表

                    if edit_task_management_obj.task.task.wenda_type in [1, 10]:
                        for name in SensitiveWordTitle_list:
                            if name in title_list_str:
                                err_name_list.append(name)

                    for name in SensitiveWordContent_list:
                        if name in content_list_str:
                            err_name_list.append(name)

                    if err_name_list:
                        response.status = False
                        response.data = {
                            "err_name_list": err_name_list
                        }
                        response.message = "问题或答案中包含敏感词"

                    if edit_task_management_obj.task.task.wenda_type in [1, 10]:
                        if response.status and len(set(content_list)) != len(content_list):
                            response.status = False
                            response.message = "提交问答答案有重复"

                    if response.status and len(set(content_list)) != len(content_list):
                        response.status = False
                        response.message = "提交问答答案有重复"

                    print(len(title_list), len(content_list))
                    if response.status and len(title_list) != len(content_list):
                        response.status = False
                        response.message = "提交问答问题与提交问答问题数量不符"

            if response.status:
                response.status = True
                response.message = "添加成功"

                query = []
                flag = True
                line_repetition = 0
                for index in range(len(content_list)):
                    line_repetition += 1

                    content = content_list[index]
                    title = title_list[index]
                    url = url_list[index]

                    # 判断所有的子任务中是否已经存在该内容
                    for i_obj in models.EditTaskManagement.objects.filter(task_id=edit_task_management_obj.task.id):

                        # 在子任务的详情表中进行查找
                        obj = models.EditPublickTaskManagement.objects.filter(
                            content=content,
                            title=title,
                            task_id=i_obj.id
                        )
                        if obj.count() > 0:
                            flag = False
                            break

                    if not flag:
                        break

                    else:
                        if role_id == 14:
                            status = 20
                        else:
                            status = 1
                        query.append(models.EditPublickTaskManagement(
                            task_id=edit_task_management_obj.id,
                            content=content,
                            title=title,
                            url=url,
                            status=status,
                        ))

                print("query -->", len(query))
                if not flag:
                    response.status = False
                    response.message = "第 {line_num} 行已经存在".format(
                        line_num=line_repetition
                    )
                elif flag and len(query) != edit_task_management_obj.number:
                    response.status = False
                    response.message = "提交数量与任务数量不符"

                else:
                    models.EditPublickTaskManagement.objects.bulk_create(query)

                    edit_task_management_obj.status = 2
                    edit_task_management_obj.complete_date = datetime.datetime.now()
                    edit_task_management_obj.save()

                    # 统计父任务下的子任务是否全部完成
                    edit_content_management_obj = models.EditContentManagement.objects.select_related(
                        'create_user').get(id=edit_task_management_obj.task.id)

                    # 该条件如果成立,表示父任务下的所有子任务都已经完成
                    if edit_content_management_obj.edittaskmanagement_set.filter(status=1).count() == 0:
                        edit_content_management_obj.status = 3
                        edit_content_management_obj.save()

                        # 发微信消息告知营销顾问
                        weixin_id = edit_content_management_obj.create_user.weixin_id
                        if not weixin_id:  # 如果没有填写微信id 则告知 zhangcong
                            # 发送微信通知

                            now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            msg = "通知时间: {now_datetime} \n通知平台:诸葛问答\n用户 {username} 未设置微信id".format(
                                now_datetime=now_datetime,
                                username=edit_content_management_obj.create_user.username
                            )
                            user_id_str = "zhangcong"
                        else:
                            msg = "您交付给编辑完成的任务都已经完成,请前往问答后台-->编辑内容管理功能中查看"
                            user_id_str = weixin_id
                        tasks.send_msg.delay(user_id_str, msg)

                    response.status = True
                    response.message = "提交成功"

            print(title_list)
            print(content_list)
            print(response.message)

        # 任务说明
        elif oper_type == "remark_shuoming":
            renwushuoming = request.POST.get('renwushuoming')
            objs = models.EditTaskManagement.objects.filter(id=o_id)
            task_id = objs[0].task.id
            models.EditContentManagement.objects.filter(id=task_id).update(remark=renwushuoming)
            response.status = True
            response.message = '修改成功'


        return JsonResponse(response.__dict__)

    else:
        roles_dict = models.Role.objects.all().values("id", "name")

        # 编辑上传任务
        if oper_type == "upload":
            return render(request, 'wenda/my_task_edit/my_task_edit_modal_upload.html', locals())

        elif oper_type == "upload_file":
            return render(request, 'wenda/my_task_edit/my_task_edit_modal_upload_file.html', locals())

        # 查看编写内容
        elif oper_type == "search_edit_content":
            edit_content_objs = models.EditPublickTaskManagement.objects.filter(task_id=o_id).order_by("-status")
            return render(request, 'wenda/my_task_edit/my_task_edit_modal_search_edit_content.html', locals())

        # 任务说明
        elif oper_type == "remark_shuoming":
            objs = models.EditTaskManagement.objects.filter(id=o_id)
            obj_remark = objs[0].task.remark
            return render(request,'wenda/my_task_edit/my_task_edit_modal_remark_shuoming.html',locals())


