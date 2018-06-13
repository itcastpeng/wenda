#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse, redirect, reverse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms.my_task import MyTaskCreateForm
import json

from django.db.models import F
from django.db.models import Q

from webadmin.views_dir.wenda.message import AddMessage

import datetime

import xlrd
import os

from wenda_celery_project import tasks


# 我的任务
@pub.is_login
def my_task(request):

    user_id = request.session["user_id"]

    role_id = models.UserProfile.objects.get(id=user_id).role_id

    if role_id == 5:    # 只针对问答客户角色有效
        # 判断是否填写医院信息,如果没填写,则强制跳转到医院信息页面
        hospital_information_objs = models.HospitalInformation.objects.filter(user_id=user_id)
        if not hospital_information_objs:
            return redirect(reverse('hospital_information'))

    release_platform_choices = models.Task.release_platform_choices
    type_choices = models.Task.type_choices
    status_choices = models.Task.status_choices

    # 问答客户角色的所有用户
    if role_id in [1, 4]:   # 管理员和超级管理员看到所有的
        wendaClientUserObjs = models.UserProfile.objects.filter(is_delete=False, status=1, role_id=5).values('id', 'username')
    elif role_id in [6, 8]:     # 问答编辑和问答渠道

        con = Q()
        q1 = Q()
        q1.connector = 'OR'
        q1.children.append(('receive_user_id', user_id))
        q1.children.append(('publish_user_id', user_id))

        q2 = Q()
        q2.connector = 'AND'

        q2.children.append(('release_user__is_delete', False))
        q2.children.append(('release_user__status', 1))
        q2.children.append(('release_user__role_id', 5))

        con.add(q1, 'AND')
        con.add(q2, 'AND')

        wendaClientUserObjs = models.Task.objects.select_related('release_user').filter(con)

        wendaClientUserObjs = [{"id": i["release_user_id"], "username": i["release_user__username"]} for i in wendaClientUserObjs.values('release_user_id', 'release_user__username').distinct()]
    elif role_id == 7:  # 营销顾问
        wendaClientUserObjs = models.UserProfile.objects.filter(is_delete=False, status=1, role_id=5, guwen_id=user_id).values('id', 'username')

    # 可以看到选择用户的下拉框功能的角色id   超级管理员、管理员、问答编辑、营销顾问、问答渠道
    show_select_user_role_ids = [1, 4, 6, 7, 8]

    if "type" in request.GET and request.GET["type"] == "ajax_json":

        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = ["id", "name", "release_platform", "wenda_type", "num", "status", "task_demand_excel", "task_result_excel", "publish_task_result_excel", "yichang", "create_date", "update_date", "complete_date", "remark", "oper", "release_user_id"]
        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]', "asc")  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column

        q = Q()
        for index, field in enumerate(column_list):
            if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                # q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)
                q.add(Q(**{field: request.GET[field]}), Q.AND)

        print(order_column)
        if role_id == 5:  # 问答客户角色
            task_objs = models.Task.objects.filter(is_delete=False).filter(release_user_id=user_id).exclude(
                wenda_type=2).filter(q).order_by(order_column).exclude(status=11)

        else:  # 问答编辑角色
            task_objs = models.Task.objects.filter(is_delete=False).filter(
                Q(receive_user_id=user_id) | Q(publish_user_id=user_id), is_delete=False).filter(q).exclude(
                status=11).order_by(order_column)

        result_data = {
            "recordsFiltered": task_objs.count(),
            "recordsTotal": task_objs.count(),
            "data": []
        }

        status_choices = models.Task.status_choices
        release_platform_choices = models.Task.release_platform_choices
        type_choices = models.Task.type_choices

        for index, obj in enumerate(task_objs[start: (start + length)], start=1):

            # 创建时间
            if obj.create_date:
                create_date = obj.create_date.strftime("%y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            # 更新时间
            if obj.update_date:
                update_date = obj.update_date.strftime("%y-%m-%d %H:%M:%S")
            else:
                update_date = ""

            # 编辑完成时间
            if obj.complete_date:
                complete_date = obj.create_date.strftime("%y-%m-%d %H:%M:%S")
            else:
                complete_date = ""

            # 状态
            status = ""
            for i in status_choices:
                if i[0] == obj.status:
                    status = i[1]
                    break

            # 发布平台
            release_platform = ""
            for i in release_platform_choices:
                if i[0] == obj.release_platform:
                    release_platform = i[1]
                    break

            # 问答类型
            wenda_type = ""
            for i in type_choices:
                if i[0] == obj.wenda_type:
                    wenda_type = i[1]
                    break

            # 任务需求表格
            task_demand_excel = "<a href='/{task_demand_file_path}' download='{task_demand_file_path_name}'>下载</a> / <a href='online_preview_task_demand/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>在线预览</a> ".format(
                task_demand_file_path=obj.task_demand_file_path,
                task_demand_file_path_name=obj.task_demand_file_path.split('/')[-1],
                obj_id=obj.id
            )

            # 写问答结果表格
            task_result_excel = ""
            if obj.task_result_file_path:
                task_result_excel = "<a href='/{task_result_file_path}' download='{task_result_file_path_name}'>下载</a> / <a href='online_preview_task_result/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>在线预览</a>".format(
                    task_result_file_path=obj.task_result_file_path,
                    task_result_file_path_name=obj.task_result_file_path.split('/')[-1],
                    obj_id=obj.id
                )

            wenda_link_obj = models.WendaLink.objects.filter(task=obj)
            if wenda_link_obj.count() == 0:
                wenda_link_flag = False
            elif wenda_link_obj.filter(status=1).count() > 0:
                wenda_link_flag = False
            else:
                wenda_link_flag = True

            # 发问答结果表格
            publish_task_result_excel = ""
            if obj.publish_task_result_file_path:

                if wenda_link_flag:
                    publish_task_result_excel = "<a href='/{task_result_file_path}' download='{task_result_file_path_name}'>下载</a> / ".format(
                        task_result_file_path=obj.publish_task_result_file_path,
                        task_result_file_path_name=obj.publish_task_result_file_path.split('/')[-1],
                    )

                publish_task_result_excel += "<a href='online_preview_publish_task_result/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>在线预览</a>".format(
                    obj_id=obj.id
                )

            # 异常内容
            yichang = ""
            if obj.is_yichang:
                yichang = "<a href='online_preview_yichang/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>查看异常</a>".format(
                    obj_id=obj.id
                )

            oper = ""

            oper += """
                <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="task_detail/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-search" aria-hidden="true"></i>任务进展</a>
            """.format(obj_id=obj.id)

            # 问答编辑角色
            is_bianji_role_ids = [6, 8, 9, 10]  # 属于编辑类型的角色id   10 是机器人角色
            if role_id in is_bianji_role_ids:
                oper += """
                    <a class="btn btn-round btn-sm bg-info" aria-hidden="true" href="hospital_info/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-search" aria-hidden="true"></i>医院信息</a>
                    """.format(obj_id=obj.id)

            # 问答客户角色
            if role_id == 5:

                if obj.status == 1:
                    oper += """
                        <a class="btn btn-round btn-sm bg-danger" aria-hidden="true" href="delete/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="fa fa-trash-o fa-fw"></i> 删除</a>
                    """.format(obj_id=obj.id)

                elif obj.status == 3:
                    oper += """
                        <a class="btn btn-round btn-sm bg-warning" aria-hidden="true" href="bohui/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-close" aria-hidden="true"></i>驳回</a>
                        <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="shenhe/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-check" aria-hidden="true"></i>审核通过</a>
                    """.format(obj_id=obj.id)

                elif obj.status == 7:
                    oper += """
                        <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="yanshou/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-check" aria-hidden="true"></i>验收</a>
                    """.format(obj_id=obj.id)

                elif obj.status == 10:
                    oper += """
                        <a class="btn btn-round btn-sm bg-warning" aria-hidden="true" href="yichang/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-check" aria-hidden="true"></i>异常提交</a>
                    """.format(obj_id=obj.id)

            if role_id in is_bianji_role_ids and obj.status in [2, 3, 4, 6, 7]:
                oper += """
                    <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="upload_task_file/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-upload" aria-hidden="true"></i>上传任务结果</a>
                """.format(obj_id=obj.id)

            if 6 > obj.status > 1:
                # remark = obj.remark
                remark = """
                    <a  href="beizhu_obj_marker/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">备注</a>
                """.format(obj_id=obj.id)

            else:
                # remark = obj.publish_remark
                remark = """
                    <a  href="beizhu_pub_marker/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">备注</a>
                """.format(obj_id=obj.id)

            result_data["data"].append(
                [index, obj.name, release_platform, wenda_type, obj.num, status, task_demand_excel, task_result_excel,
                 publish_task_result_excel, yichang, create_date, update_date, complete_date, remark, oper])

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, 'wenda/my_task/my_task_pjax.html', locals())
    return render(request, 'wenda/my_task/my_task.html', locals())


@pub.is_login
def my_task_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":
        # 添加
        if oper_type == "create":
            print(request.POST)

            release_platform = request.POST.get("release_platform")
            wenda_type = request.POST.get("wenda_type")
            num = request.POST.get("num")

            file_obj = request.FILES.get('file')

            form_obj = MyTaskCreateForm(data={
                "release_platform": release_platform,
                "wenda_type": wenda_type,
                "num": num,
                "file_obj": file_obj,
            })

            if form_obj.is_valid():

                user_profile_obj = models.UserProfile.objects.get(id=user_id)
                # 扣费
                global_settings_obj = models.GlobalSettings.objects.all()[0]

                if int(wenda_type) in [1, 10]:  # 新问答   和 新问答补发
                    money = int(num) * global_settings_obj.new_wenda_money

                else:  # 老问答
                    money = int(num) * global_settings_obj.old_wenda_money

                if user_profile_obj.balance >= money:  # 表示钱够

                    hospital_information_obj = models.HospitalInformation.objects.select_related("department").get(
                        user_id=user_id)
                    task_count = models.Task.objects.filter(release_user_id=user_id).count() + 1

                    release_platform_name = \
                    [i[1] for i in models.Task.release_platform_choices if int(release_platform) == i[0]][0]
                    wenda_type_name = [i[1] for i in models.Task.type_choices if int(wenda_type) == i[0]][0]

                    print(release_platform_name, wenda_type_name)

                    task_name = "%s_%s_%s_%s_%s" % (
                        hospital_information_obj.name,
                        hospital_information_obj.department.name,
                        release_platform_name,
                        wenda_type_name,
                        task_count,
                    )

                    file_name = file_obj.name
                    extension_name = file_name.split(".")[-1]

                    file_save_name = ".".join([task_name, extension_name])
                    file_save_path = "/".join(["statics", "task_excel", "demand", file_save_name])
                    print(file_save_path)

                    file_contents = bytes()
                    for chunk in file_obj.chunks():
                        file_contents += chunk

                    if int(wenda_type) in [1, 10]:  # 新问答或新问答补发

                        # 首先将提交的 excel 表格中的数据读出
                        book = xlrd.open_workbook(file_contents=file_contents)
                        sh = book.sheet_by_index(0)

                        excel_data = []

                        for row in range(2, sh.nrows):

                            line_data = ['']
                            for col in range(sh.ncols):
                                value = sh.cell_value(rowx=row, colx=col)
                                line_data.append(value)

                            excel_data.append(line_data)
                        print(excel_data)

                        # 然后将数据写入新的excel表格中
                        templete_path = os.path.join('statics/task_excel/template/新问答-信息模板2.xlsx')  # 模板存放路径
                        # wb = load_workbook(filename=templete_path)

                        tasks.CreateExcel.delay(excel_data, os.path.join(os.getcwd(), file_save_path))

                    else:  # 老问答
                        with open(file_save_path, "wb") as f:
                            f.write(file_contents)

                    # 添加任务
                    task_obj = models.Task.objects.create(
                        release_user_id=user_id,
                        name=task_name,
                        release_platform=form_obj.cleaned_data["release_platform"],
                        wenda_type=form_obj.cleaned_data["wenda_type"],
                        num=form_obj.cleaned_data["num"],
                        task_demand_file_path=file_save_path,
                        update_date=datetime.datetime.now()
                    )

                    user_profile_obj.balance -= money
                    user_profile_obj.save()

                    # 添加任务日志
                    models.TaskProcessLog.objects.create(
                        task=task_obj,
                        status=1,
                        oper_user_id=user_id
                    )

                    message = "新发布任务 [{task_name}] , 请分配发布人员".format(
                        task_name=task_obj.name,
                    )
                    AddMessage(request, task_obj.release_user.guwen.id, message)

                    response.status = True
                    response.message = "添加成功"
                else:
                    response.status = False
                    response.message = "当前用户余额不足!"

            else:
                response.status = False
                for i in ["release_platform", "wenda_type", "num", "file_obj"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break

        # # 修改
        # elif oper_type == "update":
        #     response.status = True
        #     response.message = "修改成功"
        #     print(request.POST.get("id"))
        #     form_obj = user.UserProfileUpdateForm(request.POST)
        #
        #     if form_obj.is_valid():
        #         if not form_obj.cleaned_data["password"]:
        #             del form_obj.cleaned_data["password"]
        #
        #         print(form_obj.cleaned_data)
        #
        #         models.UserProfile.objects.filter(id=request.POST.get("id")).update(**form_obj.cleaned_data)
        #     else:
        #         response.status = False
        #         for i in ["username", "password", "role_id"]:
        #             if i in form_obj.errors:
        #                 response.message = form_obj.errors[i]
        #                 break

        # 删除
        elif oper_type == "delete":
            task_obj = models.Task.objects.get(id=o_id)

            user_profile_obj = models.UserProfile.objects.get(id=user_id)

            # 扣费
            global_settings_obj = models.GlobalSettings.objects.all()[0]

            if task_obj.wenda_type == 1:  # 新问答
                money = task_obj.num * global_settings_obj.new_wenda_money

            else:  # 老问答
                money = task_obj.num * global_settings_obj.old_wenda_money
            user_profile_obj.balance += money
            user_profile_obj.save()

            task_obj.is_delete = True
            task_obj.update_date = datetime.datetime.now()
            task_obj.save()

            # 删除任务日志
            models.TaskProcessLog.objects.create(
                task=task_obj,
                status=11,
                oper_user_id=user_id
            )

            response.status = True
            response.message = "删除成功"

        # 提交任务结果
        elif oper_type == "upload_task_file":

            file_obj = request.FILES.get('file')

            if not file_obj:
                response.status = False
                response.message = "请选择需要上传的文件!"
            else:
                file_name = file_obj.name
                extension_name = file_name.split(".")[-1]
                task_obj = models.Task.objects.get(id=o_id)
                file_save_name = ".".join([task_obj.name, extension_name])

                if task_obj.status in [2, 4]:
                    file_save_path = "/".join(["statics", "task_excel", "result", file_save_name])

                else:  # task_obj.status = 6
                    file_save_path = "/".join(["statics", "task_excel", "publish", file_save_name])

                with open(file_save_path, "wb") as f:
                    for chunk in file_obj.chunks():
                        f.write(chunk)

                if task_obj.status in [2, 3, 4]:
                    status = 3
                    task_obj.status = 3
                    task_obj.task_result_file_path = file_save_path
                    message = "您的任务 [{task_name}] 编辑已经提交结果,请前去查看,并审核".format(
                        task_name=task_obj.name,
                    )

                else:
                    status = 6
                    task_obj.status = 7
                    task_obj.publish_task_result_file_path = file_save_path
                    task_obj.is_check = False
                    task_obj.yichang_date = None

                    # 将提交的 excel 表格中的数据读出
                    book = xlrd.open_workbook(file_save_path)
                    sh = book.sheet_by_index(0)

                    excel_data = []
                    error_dict = {}

                    for row in range(2, sh.nrows):
                        line_data = []
                        for index, col in enumerate(range(sh.ncols)):
                            value = sh.cell_value(rowx=row, colx=col)
                            line_data.append(value)

                            if index == 0:
                                if value in error_dict:
                                    error_dict[value]["repetition_row"].append(str(row + 1))
                                else:
                                    error_dict[value] = {
                                        'repetition_row': [str(row + 1)]
                                    }
                        excel_data.append(line_data)

                    result_error = ["链接重复,请处理完重新上传"]
                    for k, v in error_dict.items():
                        if len(v["repetition_row"]) > 1:
                            result_error.append("重复链接 --> %s   重复行数: %s" % (k, ",".join(v["repetition_row"])))

                    if len(result_error) > 1:
                        response.status = False
                        response.message = "链接发生重复"
                        response.error = result_error

                        return JsonResponse(response.__dict__)

                    message = "您的任务 [{task_name}] 编辑已经提交结果,请前去查看,并审核".format(
                        task_name=task_obj.name,
                    )

                AddMessage(request, task_obj.release_user.id, message)

                task_obj.update_date = datetime.datetime.now()
                task_obj.save()

                # 编辑提交任务结果
                models.TaskProcessLog.objects.create(
                    task=task_obj,
                    status=status,
                    oper_user_id=user_id
                )

                response.status = True
                response.message = "添加成功"

        # 发布者审核任务
        elif oper_type == "shenhe":
            task_obj = models.Task.objects.get(id=o_id)
            task_obj.status = 5

            response.status = True
            response.message = "审核成功"

            message = "任务 [{task_name}] 发布方已经审核通过".format(
                task_name=task_obj.name,
            )
            AddMessage(request, task_obj.receive_user.id, message)

            message = "任务 [{task_name}] 发布方已经审核通过, 请分配发布人员".format(
                task_name=task_obj.name,
            )
            AddMessage(request, task_obj.release_user.guwen.id, message)

            # 发布者审核任务日志
            models.TaskProcessLog.objects.create(
                task=task_obj,
                status=5,
                oper_user_id=user_id
            )

            task_obj.update_date = datetime.datetime.now()
            task_obj.save()

        # 发布者验收任务
        elif oper_type == "yanshou":
            task_obj = models.Task.objects.get(id=o_id)
            task_obj.status = 10
            task_obj.complete_date = datetime.datetime.now()

            models.EditTaskManagement.objects.filter(task__task=task_obj).update(status=5)

            response.status = True
            response.message = "验收成功"

            message = "任务 [{task_name}] 发布方已经审核通过".format(
                task_name=task_obj.name,
            )
            AddMessage(request, task_obj.publish_user.id, message)

            # 发布者验收任务日志
            models.TaskProcessLog.objects.create(
                task=task_obj,
                status=10,
                oper_user_id=user_id
            )

            task_obj.update_date = datetime.datetime.now()
            task_obj.save()

        # 发布者驳回任务
        elif oper_type == "bohui":
            remark = request.POST["remark"]
            if remark:
                task_obj = models.Task.objects.get(id=o_id)
                task_obj.status = 4

                response.status = True
                response.message = "任务驳回成功"

                message = "任务 [{task_name}] 被发布方驳回".format(
                    task_name=task_obj.name,
                )
                AddMessage(request, task_obj.receive_user.id, message)

                # 发布者验收任务日志
                models.TaskProcessLog.objects.create(
                    task=task_obj,
                    status=4,
                    oper_user_id=user_id,
                    remark=remark
                )

                task_obj.update_date = datetime.datetime.now()
                task_obj.save()
                objs = models.EditContentManagement.objects.filter(task=task_obj)
                print(objs)
                if objs:
                    objs.update(status=2)
                    objs[0].edittaskmanagement_set.update(status=1)
                    models.EditPublickTaskManagement.objects.filter(task__task=objs[0]).delete()

            else:
                response.status = False
                response.message = "驳回理由不能为空"

        # 提交异常
        elif oper_type == "yichang":

            file_obj = request.FILES.get('file')

            if file_obj:

                file_name = file_obj.name
                extension_name = file_name.split(".")[-1]
                task_obj = models.Task.objects.get(id=o_id)
                file_save_name = ".".join([task_obj.name, extension_name])

                file_save_path = "/".join(["statics", "task_excel", "yichang", file_save_name])

                with open(file_save_path, "wb") as f:
                    for chunk in file_obj.chunks():
                        f.write(chunk)

                obj = models.Task.objects.get(id=o_id)
                obj.yichang = file_save_path

                response.status = True
                response.message = "提交成功"

                message = "客户 [{username}] 对任务 [{task_name}]  提出异议,请查看".format(
                    task_name=obj.name,
                    username=obj.release_user.username
                )
                AddMessage(request, obj.release_user.guwen.id, message)

                obj.update_date = datetime.datetime.now()
                obj.save()

            else:
                response.status = False
                response.message = "提交内容不能为空"

        #
        elif oper_type == 'beizhu_pub_marker':
            print('111111111111111111111111111111111')
            pub_remark = request.POST.get('pub_remark')
            print('pub_remark- - ========--> ',pub_remark)
            objs = models.Task.objects.filter(id=o_id)
            if objs[0].publish_remark:
                objs.update(pub_remark=pub_remark)
                response.status = True
                response.message = '修改成功'
            else:
                objs.create(pub_remark=pub_remark)
            response.status = True
            response.message = '修改成功'

        #
        elif oper_type == 'beizhu_obj_marker':
            obj_remark = request.POST.get('obj_remark')
            print('obj_remark- -  = = ============>',obj_remark)
            objs = models.Task.objects.filter(id=o_id)
            if objs[0].remark:
                objs.update(remark=obj_remark)
                response.status = True
                response.message = '修改成功'
            else:
                objs.create(remark=obj_remark)
                response.status = True
                response.message = '修改成功'

        return JsonResponse(response.__dict__)

    else:

        release_platform_choices = models.Task.release_platform_choices
        type_choices = models.Task.type_choices

        # 添加
        if oper_type == "create":

            return render(request, 'wenda/my_task/my_task_modal_create.html', locals())

        # # 修改
        # elif oper_type == "update":
        #     user_profile_obj = models.UserProfile.objects.select_related("role").get(id=o_id)
        #
        #     return render(request, 'myadmin/user_management/user_management_modal_update.html', locals())

        # 删除
        elif oper_type == "delete":
            task_obj = models.Task.objects.get(id=o_id)
            return render(request, 'wenda/my_task/my_task_modal_delete.html', locals())

        # 编辑 上传任务结果的excel表格
        elif oper_type == "upload_task_file":
            task_obj = models.Task.objects.get(id=o_id)

            if task_obj.status in [3, 7]:
                update = True

            return render(request, "wenda/my_task/my_task_modal_upload_task_file.html", locals())

        # 发布方验收编辑上传的结果
        elif oper_type == "yanshou":
            task_obj = models.Task.objects.get(id=o_id)
            return render(request, "wenda/my_task/my_task_modal_yanshou.html", locals())

        # 发布方验收发布的结果
        elif oper_type == "shenhe":
            task_obj = models.Task.objects.get(id=o_id)
            return render(request, "wenda/my_task/my_task_modal_shenhe.html", locals())

        # 下载模板
        elif oper_type == "download_template":
            return render(request, "wenda/my_task/my_task_modal_download_template.html")

        # 在线预览任务需求
        elif oper_type == "online_preview_task_demand":
            task_obj = models.Task.objects.get(id=o_id)

            file_name_path = os.path.join(os.getcwd(), task_obj.task_demand_file_path)
            print(file_name_path)

            book = xlrd.open_workbook(file_name_path)
            sh = book.sheet_by_index(0)

            table_data = []

            for row in range(2, sh.nrows):

                line_data = []
                for col in range(sh.ncols):
                    value = sh.cell_value(rowx=row, colx=col)

                    ctype = sh.cell(row, col).ctype  # 表格的数据类型
                    if ctype == 2 and int(str(value).split(".")[1]) == 0:
                        value = int(value)
                    line_data.append(value)

                table_data.append(line_data)
            print(table_data)
            return render(request, "wenda/my_task/my_task_modal_online_preview.html", locals())

        # 在线预览任务结果
        elif oper_type == "online_preview_task_result":
            task_obj = models.Task.objects.get(id=o_id)

            file_name_path = os.path.join(os.getcwd(), task_obj.task_result_file_path)
            print(file_name_path)

            book = xlrd.open_workbook(file_name_path)
            sh = book.sheet_by_index(0)

            table_data = []

            for row in range(2, sh.nrows):

                line_data = []
                for col in range(sh.ncols):

                    value = sh.cell_value(rowx=row, colx=col)

                    ctype = sh.cell(row, col).ctype  # 表格的数据类型
                    if ctype == 2 and int(str(value).split(".")[1]) == 0:
                        value = int(value)

                    line_data.append(value)

                table_data.append(line_data)
            print(table_data)
            return render(request, "wenda/my_task/my_task_modal_online_preview.html", locals())

        # 在线预览任务结果
        elif oper_type == "online_preview_publish_task_result":
            task_obj = models.Task.objects.get(id=o_id)
            wenda_link_obj = models.WendaLink.objects.filter(task=task_obj)
            if wenda_link_obj.count() == 0:
                wenda_link_flag = False
            elif wenda_link_obj.filter(status=1).count() > 0:
                wenda_link_flag = False
            else:
                wenda_link_flag = True

            file_name_path = os.path.join(os.getcwd(), task_obj.publish_task_result_file_path)
            print(file_name_path)

            book = xlrd.open_workbook(file_name_path)
            sh = book.sheet_by_index(0)

            table_data = []

            for row in range(2, sh.nrows):

                line_data = []
                for col in range(sh.ncols):
                    value = sh.cell_value(rowx=row, colx=col)

                    ctype = sh.cell(row, col).ctype  # 表格的数据类型
                    if ctype == 2 and int(str(value).split(".")[1]) == 0:
                        value = int(value)
                    line_data.append(value)

                table_data.append(line_data)
            print(table_data)
            print("wenda_link_flag -->", wenda_link_flag)
            return render(request, "wenda/my_task/my_task_modal_online_preview.html", locals())

        # 发布方驳回编辑上传的结果
        elif oper_type == "bohui":
            task_obj = models.Task.objects.get(id=o_id)
            return render(request, "wenda/my_task/my_task_modal_bohui.html", locals())

        # 任务明细
        elif oper_type == "task_detail":

            role_id = models.UserProfile.objects.get(id=user_id).role.id
            print(role_id)

            task_process_log_objs = models.TaskProcessLog.objects.select_related('oper_user').filter(
                task_id=o_id).order_by("-create_date")
            return render(request, "wenda/my_task/my_task_modal_task_detail.html", locals())

        # 医院信息
        elif oper_type == "hospital_info":
            user_obj = models.Task.objects.get(id=o_id).release_user
            hospital_information_obj = models.HospitalInformation.objects.select_related('department').get(
                user=user_obj)

            # 问答内容方向
            content_direction_list = [int(i) for i in hospital_information_obj.content_direction.split(",")]
            content_direction = []
            for i in hospital_information_obj.content_direction_choices:
                if i[0] in content_direction_list:
                    content_direction.append(i[1])

            content_direction = ",".join(content_direction)

            if hospital_information_obj.content_direction_custom:
                content_direction += ",%s" % hospital_information_obj.content_direction_custom

            # 表达人称角色
            reply_role_list = [int(i) for i in hospital_information_obj.reply_role.split(",")]
            reply_role = []
            for i in hospital_information_obj.reply_role_choices:
                if i[0] in reply_role_list:
                    reply_role.append(i[1])

            reply_role = ",".join(reply_role)

            return render(request, 'wenda/task_list/task_list_modal_hospital_info.html', locals())

        # 异常提交
        elif oper_type == "yichang":
            return render(request, "wenda/my_task/my_task_modal_yichang.html", locals())

        # 查看异常
        elif oper_type == "online_preview_yichang":
            obj = models.Task.objects.get(id=o_id)
            status_choices = models.WendaLink.status_choices

            wendalink_objs = obj.wendalink_set.filter(status__gt=2)

            return render(request, "wenda/my_task/my_task_modal_online_preview_yichang.html", locals())

        # 备注 pub
        elif oper_type == 'beizhu_pub_marker':
            objs = models.Task.objects.filter(is_delete=False).filter(id=o_id)
            pub_remark= objs[0].publish_remark
            print('pub_remark - - -> ',pub_remark )
            return render(request,'wenda/my_task/my_task_modal_beizhu_pub_marker.html',locals())

        # 备注 obj
        elif oper_type == 'beizhu_obj_marker':
            objs =  models.Task.objects.filter(is_delete=False).filter(id=o_id)
            obj_remark = objs[0].remark
            print('-obj_remark- -- > ',obj_remark)
            return render(request, 'wenda/my_task/my_task_modal_beizhu_obj_marker.html', locals())