#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

import json

from django.db.models import Q

from webadmin.views_dir.wenda.message import AddMessage

import xlrd
import os
import datetime

import time
from wenda_celery_project import tasks

from webadmin.forms.task_list import OldWendaCreateForm
from webadmin.modules.WeChat import WeChatPublicSendMsg
from urllib.parse import unquote


def send_gongzhonghao_msg(openid, value="您有新的问答任务等待编写,请前往问答后台 - 我的任务-编辑 功能中查看"):
    post_data = {
        "touser": openid,
        "template_id": "ksNf6WiqO5JEqd3bY6SUqJvWeL2-kEDqukQC4VeYVvw",
        "data": {
            "first": {
                "value": value,
                "color": "#173177"
            },
            "keyword1": {
                "value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                # "color": "#173177"
            },
            "keyword2": {
                "value": "诸葛问答",
            },
        }
    }
    # tasks.send_msg_gongzhonghao.delay(post_data)
    # print(openid)
    # print(post_data)
    # wechat_data_path = os.path.abspath('webadmin/modules/wechat_data.json')
    # print(wechat_data_path)
    # we_chat_public_send_msg_obj = WeChatPublicSendMsg(wechat_data_path)
    # we_chat_public_send_msg_obj.sendTempMsg(post_data)


# 任务大厅
@pub.is_login
def task_list(request):
    user_id = request.session["user_id"]
    role_id = models.UserProfile.objects.get(id=user_id).role_id

    release_platform_choices = models.Task.release_platform_choices
    type_choices = models.Task.type_choices
    status_choices = models.Task.status_choices

    # 问答客户角色的所有用户
    if role_id in [1, 4]:  # 管理员和超级管理员看到所有的
        wendaClientUserObjs = models.UserProfile.objects.filter(is_delete=False, status=1, role_id=5).values('id',
                                                                                                             'username')
    elif role_id in [6, 8]:  # 问答编辑和问答渠道

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
        print('user_id - - -- - -> ',user_id)
        # wendaClientUserObjs = models.UserProfile.objects.filter(is_delete=False, status=1, role_id=5, guwen_id=user_id).values('id', 'username')
        wendaClientUserObjs = models.UserProfile.objects.filter(is_delete=False, status=1, role_id=5).values('id', 'username')

    elif role_id == 12:     # 销售
        wendaClientUserObjs = models.UserProfile.objects.filter(is_delete=False, status=1, role_id=5, xiaoshou_id=user_id).values('id', 'username')

    # 可以看到选择用户的下拉框功能的角色id   超级管理员、管理员、问答编辑、营销顾问、问答渠道
    show_select_user_role_ids = [1, 4, 7]

    if "type" in request.GET and request.GET["type"] == "ajax_json":

        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = [
            "id", "name", "release_platform", "wenda_type", "num", "status", "task_demand_excel",
            "task_result_excel", "publish_task_result_excel", "yichang", "create_date", "update_date",
            "complete_date", "remark", "oper", "release_user_id", "release_user__xiaoshou_id", "publish_user_id"
        ]
        # column_list = ["id", "name", "release_platform", "wenda_type", "status", "num", "task_excel", "create_date", "oper"]

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
                if field == "create_date":
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

                else:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)



        # 管理员能看到所有
        if role_id <= 4:
            task_objs = models.Task.objects.filter(is_delete=False, release_user__is_delete=False).filter(q).order_by(order_column).exclude(status=11)

        elif role_id == 12:     # 销售角色
            task_objs = models.Task.objects.filter(is_delete=False).filter(release_user__xiaoshou_id=user_id).filter(q).order_by(order_column).exclude(status=11)

        else:   # 营销顾问角色
            # release_user__oper_user_id=user_id   用于判断该任务对应的客户是否是当前营销顾问角色的用户创建的
            # task_objs = models.Task.objects.filter(is_delete=False).filter(release_user__guwen_id=user_id).filter(q).order_by(order_column).exclude(status=11)
            task_objs = models.Task.objects.filter(is_delete=False).filter(q).order_by(order_column).exclude(status=11)

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
            task_demand_excel = "<a href='/{task_demand_file_path}' download='{task_demand_file_path_name}'>下载</a> / <a href='/my_task/online_preview_task_demand/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>在线预览</a> ".format(
                task_demand_file_path=obj.task_demand_file_path,
                task_demand_file_path_name=obj.task_demand_file_path.split('/')[-1],
                obj_id=obj.id
            )

            # 写问答结果表格
            task_result_excel = ""
            if obj.task_result_file_path:
                task_result_excel = "<a href='/{task_result_file_path}' download='{task_result_file_path_name}'>下载</a> / <a href='/my_task/online_preview_task_result/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>在线预览</a>".format(
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

                publish_task_result_excel += "<a href='/my_task/online_preview_publish_task_result/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>在线预览</a>".format(
                    obj_id=obj.id
                )

            # # 发问答结果表格
            # publish_task_result_excel = ""
            # if obj.publish_task_result_file_path:
            #     publish_task_result_excel = "<a href='/{task_result_file_path}' download='{task_result_file_path_name}'>下载</a> / <a href='/my_task/online_preview_publish_task_result/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>在线预览</a>".format(
            #         task_result_file_path=obj.publish_task_result_file_path,
            #         task_result_file_path_name=obj.publish_task_result_file_path.split('/')[-1],
            #         obj_id=obj.id
            #     )

            # 报表内容
            baobiao = ""

            # 异常
            if obj.is_yichang:

                baobiao += "<a href='online_preview_yichang/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>异常({num})</a>".format(
                    obj_id=obj.id,
                    num=obj.wendalink_set.filter(status__gt=2).count()
                )

            if obj.status in [7, 10]:
                if baobiao:
                    baobiao += " / "
                baobiao += "<a href='online_preview_zhengchang/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>正常({num})</a>".format(
                    obj_id=obj.id,
                    num=obj.wendalink_set.filter(status=2).count()
                )

            oper = ""
            # 编辑角色
            if role_id == 6:
                oper += """
                    <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="hospital_info/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-search" aria-hidden="true"></i>医院信息</a>
                    """.format(obj_id=obj.id)
                    # <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="qiangdan/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-gavel" aria-hidden="true"></i>抢单</a>
            # 营销顾问 角色
            elif role_id == 7:

                if obj.status in [1, 5]:
                    oper += """
                        <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="paidan/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-plane" aria-hidden="true"></i>派单</a>
                    """.format(obj_id=obj.id)

            oper += """
                <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="task_detail/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-search" aria-hidden="true"></i>任务进展</a>
                <a class="btn btn-round btn-sm bg-info" aria-hidden="true" href="hospital_info/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-search" aria-hidden="true"></i>医院信息</a>
            """.format(obj_id=obj.id)

            if obj.status not in [1, 10, 11] and role_id == 7:  # 新发布、已完结和撤销状态的任务不显示
                oper += """
                        <a class="btn btn-round btn-sm bg-info" aria-hidden="true" href="update_fabu_shuliang/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-search" aria-hidden="true"></i>修改发布</a>
                 """.format(obj_id=obj.id)
                oper += """
                    <a class="btn btn-round btn-sm bg-danger" aria-hidden="true" href="revocation/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon wb-trash" aria-hidden="true"></i>撤销</a>
                """.format(obj_id=obj.id)

            remark = """
             <a class=" aria-hidden="true" href="beizhu_botton/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">备注</a>
            """.format(obj_id=obj.id)
            # if 6 > obj.status > 1:
            #     remark = obj.remark
            # else:
            #     remark = obj.publish_remark

            obj_data = [
                index, obj.name, release_platform, wenda_type, obj.num, status, task_demand_excel, task_result_excel,
                publish_task_result_excel, baobiao, create_date, update_date, complete_date, oper ,remark
            ]

            result_data["data"].append(obj_data)

        return HttpResponse(json.dumps(result_data))

    sale_userp_data = models.UserProfile.objects.filter(role_id=12).values_list("id", "username")

    oper_user_objs = models.UserProfile.objects.filter(role_id__in=[8, 10], is_delete=False)

    print(role_id)
    if "_pjax" in request.GET:
        return render(request, 'wenda/task_list/task_list_pjax.html', locals())
    return render(request, 'wenda/task_list/task_list.html', locals())


@pub.is_login
def task_list_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    role_id = request.session["role_id"]
    response = pub.BaseResponse()

    if request.method == "POST":
        if o_id != '0':
            task_obj = models.Task.objects.get(id=o_id)
        else:
            task_obj = None

        # # 编辑抢单
        # if oper_type == "qiangdan":
        #
        #     response.status = True
        #     response.message = "抢单成功"
        #
        #     task_obj.receive_user_id = user_id
        #     task_obj.status = 2
        #     task_obj.save()
        #
        #     message = "您的任务 [{task_name}] 已被编辑接单".format(task_name=task_obj.name, bianji_name=task_obj.receive_user.username)
        #     AddMessage(request, task_obj.release_user.id, message)

        # 派单员派单
        if oper_type == "paidan":

            bianji_id = request.POST["user_id"]
            task_type = request.POST.get("task_type")
            remark = request.POST.get("remark")

            if not bianji_id:
                response.status = False
                response.message = "请选择接单编辑"
            else:
                if task_obj.status == 1 and task_type == "1":    # 第一次派单 并且是写问答
                    task_obj.receive_user_id = bianji_id
                    task_obj.status = 2
                    task_obj.remark = remark

                    bj_name = task_obj.receive_user.username
                    bj_id = task_obj.receive_user.id

                    # 在任务首次被分配后进行扣费操作
                    kouFei(task_obj)

                    # 如果编写任务分配的用户是小明,则将该任务在 编辑内容管理 里面创建一份
                    if bj_id == 8:
                        models.EditContentManagement.objects.create(
                            task=task_obj,
                            client_user=task_obj.release_user,
                            create_user_id=user_id,
                            reference_file_path="/" + task_obj.task_demand_file_path,
                            status=1,
                            number=task_obj.num,
                            remark=remark,
                        )

                else:   # 发问答
                    if task_type == "2":
                        # 在任务首次被分配后进行扣费操作
                        kouFei(task_obj)

                    task_obj.publish_user_id = bianji_id
                    task_obj.status = 6
                    task_obj.publish_remark = remark

                    bj_name = task_obj.publish_user.username
                    bj_id = task_obj.publish_user.id

                message1 = "您的任务 {task_name} 已经被平台派单员 [{paidan_name}] 指定编辑进行完成".format(
                    task_name=task_obj.name,
                    paidan_name=models.UserProfile.objects.get(id=user_id).username,
                    bianji_name=bj_name
                )

                message2 = "平台派单员 [{paidan_name}] 分配给您新的任务 [{task_name}] , 请注意查看".format(
                    paidan_name=models.UserProfile.objects.get(id=user_id).username,
                    task_name=task_obj.name,
                )

                AddMessage(request, task_obj.release_user.id, message1)
                AddMessage(request, bj_id, message2)

                task_obj.update_date = datetime.datetime.now()
                task_obj.save()

                response.status = True
                response.message = "任务指派成功"

                # user_profile_obj = models.UserProfile.objects.get(id=task_obj.release_user.id)

                # 分配任务日志
                models.TaskProcessLog.objects.create(
                    task=task_obj,
                    status=2,
                    oper_user_id=user_id,
                    remark="任务分配给: %s" % bj_name
                )

        # 将异常告知发稿人员
        elif oper_type == "online_preview_yichang":

            obj = models.Task.objects.get(id=o_id)

            message = "客户 [{username}] 对任务 [{task_name}]  提出异议,请查看".format(
                task_name=obj.name,
                username=obj.release_user.username
            )
            AddMessage(request, obj.publish_user.id, message)

            response.status = True
            response.message = "通知成功"

        # 撤销
        elif oper_type == "revocation":
            remark = request.POST.get('remark')

            if not remark:
                response.status = False
                response.message = "备注不能为空"
            else:
                obj = models.Task.objects.get(id=o_id)
                obj.status = 11

                models.TaskProcessLog.objects.create(
                    task=obj,
                    status=7,
                    remark=remark,
                    oper_user_id=user_id
                )

                global_settings_obj = models.GlobalSettings.objects.all().first()

                price = 0
                if obj.wenda_type == 1:
                    price = global_settings_obj.new_wenda_money
                else:
                    price = global_settings_obj.old_wenda_money

                moeny = price * obj.num
                user_profile_obj = models.UserProfile.objects.get(id=obj.release_user.id)
                user_profile_obj.balance += moeny

                models.BalanceDetail.objects.create(
                    user_id=obj.release_user.id,
                    account_type=5,
                    money=moeny,
                    oper_user_id=user_id,
                    remark=remark
                )

                message = "您的任务 [{task_name}] 被撤销, 该任务所扣问答币已经退还,请查看".format(
                    task_name=obj.name,
                )
                AddMessage(request, obj.release_user.id, message)

                obj.update_date = datetime.datetime.now()
                obj.save()
                user_profile_obj.save()

                # 判断是否在编辑内容管理中有数据,如果有,修改为撤销状态
                edit_task_management_obj = models.EditContentManagement.objects.filter(task=obj).update(
                    status=10
                )

                # 如果机器人任务中存在任务,则删除掉
                models.WendaRobotTask.objects.filter(task=obj).delete()
                response.status = True
                response.message = "撤销成功"

        # 创建老问答(霸屏王)
        elif oper_type == "create":
            print(request.POST)
            bianji_id = request.POST.get("bianji_id")   # 编辑id
            client_id = request.POST.get("client_id")   # 用户id
            num = request.POST.get("num")
            remark = request.POST.get("remark")
            addMap = request.POST.get("addMap", False)
            is_test = request.POST.get("is_test", False)
            is_shangwutong = request.POST.get('is_shangwutong',False)
            if remark:
                remark = unquote(remark)
            release_platform = 1        # 发布平台   百度知道
            wenda_type = 2              # 问答类型   老问答

            task_excel_obj = request.FILES.get('task_excel')  # 提交的excel 对象

            form_obj = OldWendaCreateForm(data={
                "client_id": client_id,
                "bianji_id": bianji_id,
                "num": num,
                "task_excel_obj": task_excel_obj,
            })
            if form_obj.is_valid():
                user_profile_obj = models.UserProfile.objects.get(id=form_obj.cleaned_data['client_id'])
                # 扣费
                global_settings_obj = models.GlobalSettings.objects.all()[0]
                money = int(num) * global_settings_obj.old_wenda_money

                if user_profile_obj.balance >= money:  # 表示钱够
                    if addMap:
                        addMap = True
                        if user_profile_obj.map_match_keywords and user_profile_obj.map_search_keywords:
                            response.status = True
                        else:
                            response.status = False
                            response.message = "该用户未填写地图搜索关键词和地图匹配关键词"

                    if response.status:
                        hospital_information_objs = models.HospitalInformation.objects.select_related("department").filter(user_id=client_id)
                        if hospital_information_objs:
                            hospital_information_obj = hospital_information_objs[0]
                        else:
                            response.status = False
                            response.message = "该用户未填写医院信息"


                    if response.status:
                        task_count = models.Task.objects.filter(release_user_id=client_id).count() + 1

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

                        file_name = task_excel_obj.name
                        extension_name = file_name.split(".")[-1]

                        file_save_name = ".".join([task_name, extension_name])
                        file_save_path = "/".join(["statics", "task_excel", "demand", file_save_name])
                        print(file_save_path)

                        file_contents = bytes()
                        for chunk in task_excel_obj.chunks():
                            file_contents += chunk

                        with open(file_save_path, "wb") as f:
                            f.write(file_contents)

                        # 添加任务
                        if is_shangwutong:
                            is_shangwutong = True

                            models.KeywordsTopSet.objects.update(is_shangwutong=False)



                        if is_test:
                            is_test = True

                        # 做出判断插入数据
                        task_obj = models.Task.objects.create(
                            release_user_id=form_obj.cleaned_data['client_id'],
                            name=task_name,
                            release_platform=release_platform,
                            wenda_type=wenda_type,
                            num=form_obj.cleaned_data["num"],
                            task_demand_file_path=file_save_path,
                            update_date=datetime.datetime.now(),
                            status=2,
                            receive_user_id=8,
                            remark=remark,
                            add_map=addMap,
                            is_test=is_test,
                            is_shangwutong=is_shangwutong
                        )

                        # 扣费
                        user_profile_obj.balance -= money
                        user_profile_obj.save()
                        # 进行扣费记录操作
                        kouFei(task_obj)

                        # 添加任务日志
                        models.TaskProcessLog.objects.create(
                            task=task_obj,
                            status=1,
                            oper_user_id=user_id
                        )

                        bj_name = task_obj.receive_user.username
                        bj_id = task_obj.receive_user.id

                        # 将该任务在 编辑内容管理 里面创建一份
                        edit_content_management_obj = models.EditContentManagement.objects.create(
                            task=task_obj,
                            client_user=task_obj.release_user,
                            create_user_id=user_id,
                            reference_file_path="/" + task_obj.task_demand_file_path,
                            status=2,
                            number=num,
                            remark=remark,
                        )

                        models.EditTaskManagement.objects.create(
                            task=edit_content_management_obj,
                            edit_user_id=form_obj.cleaned_data["bianji_id"],
                            number=form_obj.cleaned_data["num"],
                            status=1,
                        )

                        # 添加任务日志
                        models.TaskProcessLog.objects.create(
                            task=task_obj,
                            status=2,
                            oper_user_id=user_id,
                            remark="分配任务给: 小明"
                        )

                        # 发送微信消息
                        user_obj = models.UserProfile.objects.get(id=form_obj.cleaned_data["bianji_id"])
                        openid = user_obj.openid
                        if not openid:  # 如果没有填写微信id 则告知 zhangcong
                            value = "编辑 " + user_obj.username + " 未关联公众号,请辅助帮忙关注"
                            send_gongzhonghao_msg('o7Xw_0bdwjqmqSsXBVGfZiYMy0pQ')
                        else:
                            send_gongzhonghao_msg(openid)

                        response.status = True
                        response.message = "添加成功"
                else:
                    response.status = False
                    response.message = "当前用户余额不足!"
            else:
                response.status = False
                for i in ["client_id", "bianji_id", "num", "task_excel_obj"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break

        # 修改发布数量
        elif oper_type == "update_fabu_shuliang":
            num = request.POST.get('num')
            name = request.POST.get('name')
            if num.isdigit() :
                obj = models.Task.objects.get(id=o_id)
                if obj:
                    obj.num=num
                    models.EditTaskManagement.objects.select_related('task','task').filter(task__task_id=obj.id).update(number=num)
                    # obj.editcontentmanagement_set.edittaskmanagement_set.number = num
                    obj.save()
                    response.status = True
                    response.message = '修改成功'
            else:
                response.status = False
                response.message = '请输入数字'

        # 备注按钮
        elif oper_type == 'beizhu_botton':
            xuanchuanyaoqiu = request.POST.get('xuanchuanyaoqiu')
            if xuanchuanyaoqiu:
                print(xuanchuanyaoqiu)
                obj = models.Task.objects.filter(id=o_id)
                if obj:
                    obj.update(
                        remark = xuanchuanyaoqiu
                    )
                    response.status = True
                    response.message='修改成功'
                else:
                    obj.create(
                        remark = xuanchuanyaoqiu
                    )
                    response.status = True
                    response.message = '创建成功'
        return JsonResponse(response.__dict__)

    else:
        # 医院信息
        if oper_type == "hospital_info":
            user_obj = models.Task.objects.get(id=o_id).release_user
            hospital_information_obj = models.HospitalInformation.objects.select_related('department').get(user=user_obj)

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

        # 抢单
        elif oper_type == "qiangdan":
            task_obj = models.Task.objects.get(id=o_id)
            return render(request, 'wenda/task_list/task_list_modal_qiangdan.html', locals())

        # 派单
        elif oper_type == "paidan":
            task_obj = models.Task.objects.get(id=o_id)
            return render(request, 'wenda/task_list/task_list_modal_paidan.html', locals())

        # 获取编辑列表
        elif oper_type == "get_bianji_data":

            task_obj = models.Task.objects.get(id=o_id)

            if task_obj.status == 1:
                user_profile_objs = models.UserProfile.objects.select_related("role").filter(role_id__in=[6, 8, 9, 10], is_delete=False)
            else:
                user_profile_objs = models.UserProfile.objects.select_related("role").filter(role_id__in=[6, 8, 9, 10], is_delete=False)

            return_html = []

            for obj in user_profile_objs:

                if task_obj.receive_user and task_obj.receive_user.id == obj.id:
                    text = "%s (%s)【编写问答】" % (obj.username, obj.role.name)
                    selected = True
                else:
                    text = "%s (%s)" % (obj.username, obj.role.name)
                    selected = False
                temp_html = {
                    "text": text,
                    "id": obj.id,
                    "state": {"selected": selected}
                }
                return_html.append(temp_html)
            return HttpResponse(json.dumps(return_html))

        # 任务进展
        elif oper_type == "task_detail":
            task_process_log_objs = models.TaskProcessLog.objects.select_related('oper_user').filter(task_id=o_id).order_by("-create_date")

            print(role_id)
            return render(request, "wenda/my_task/my_task_modal_task_detail.html", locals())

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
                    line_data.append(value)

                table_data.append(line_data)
            print(table_data)
            return render(request, "wenda/my_task/my_task_modal_online_preview.html", locals())

        # 展示异常
        elif oper_type == "online_preview_yichang":
            obj = models.Task.objects.get(id=o_id)

            file_name_path = os.path.join(os.getcwd(), obj.publish_task_result_file_path)
            book = xlrd.open_workbook(file_name_path)
            sh = book.sheet_by_index(0)
            table_data = {}
            for row in range(2, sh.nrows):
                line_data = []
                for col in range(sh.ncols):
                    value = sh.cell_value(rowx=row, colx=col)

                    ctype = sh.cell(row, col).ctype  # 表格的数据类型
                    if ctype == 2 and int(str(value).split(".")[1]) == 0:
                        value = int(value)
                    line_data.append(value)

                url = sh.cell_value(rowx=row, colx=0)
                table_data[url] = line_data

            wendalink_objs = obj.wendalink_set.filter(status__gt=2)

            result_data = []
            for obj in wendalink_objs:
                result_data.append(
                    {
                        "status": obj.get_status_display(),
                        "title": table_data[obj.url][1],
                        "content": table_data[obj.url][2],
                        "url": obj.url,
                        "update": obj.update_date.strftime("%y-%m-%d %H:%M:%S")
                    }
                )
            return render(request, "wenda/task_list/task_list_modal_online_preview_yichang.html", locals())

        # 展示正常
        elif oper_type == "online_preview_zhengchang":
            obj = models.Task.objects.get(id=o_id)
            status_choices = models.WendaLink.status_choices

            wendalink_objs = obj.wendalink_set.filter(status=2)

            return render(request, "wenda/task_list/task_list_modal_online_preview_zhengchang.html", locals())

        # 撤销
        elif oper_type == "revocation":
            # obj = models.Task.objects.get(id=o_id)
            # obj.status = 11
            #
            # models.TaskProcessLog.objects.create(
            #     task=obj,
            #     status=7,
            #     remark="",
            #     oper_user_id=user_id
            # )

            obj = models.Task.objects.get(id=o_id)
            return render(request, "wenda/my_task/my_task_modal_revocation.html", locals())

        # 生成异常报表
        elif oper_type == "yichang_baobiao":

            # 相对路径
            file_name = str(int(time.time() * 1000)) + ".xlsx"
            file_path = '/'.join(["statics", "upload_files", file_name])

            # 绝对路径
            file_save_path = os.path.join(os.getcwd(), file_path)

            tasks.generate_error_excel.delay(o_id, file_save_path)

            while True:
                if os.path.exists(file_save_path):
                    break

            response.status = True
            response.message = "数据报表下载成功"
            response.file_path = "/" + file_path
            response.file_name = file_name

            return JsonResponse(response.__dict__)

        # 创建老问答(霸屏王)
        elif oper_type == "create":

            bianji_role_id_list = [13, 14]  # 13 是内部编辑  14是外部编辑
            user_bianji_data = models.UserProfile.objects.filter(role_id__in=bianji_role_id_list, is_delete=False).values('id', 'username')
            user_client_data = models.UserProfile.objects.filter(role_id=5, is_delete=False).values('id', 'username')
            return render(request, "wenda/task_list/task_list_modal_create.html", locals())

        # 修改发布数量
        elif oper_type =="update_fabu_shuliang":
            objs = models.Task.objects.filter(id=o_id).values('num','name','id')
            num = objs[0]['num']
            o_id = o_id
            name = objs[0]['name']
            return render(request,'wenda/my_task/my_task_model_update_fabu_shuliang.html',locals())

        # 备注按钮
        elif oper_type == 'beizhu_botton':
            objs = models.Task.objects.filter(id=o_id)
            remark = objs[0].remark
            return render(request, 'wenda/my_task/my_task_modal_beizhu.html', locals())

# 对客户扣费记录明细
def kouFei(task_obj):
    num = int(task_obj.num)
    global_settings_obj = models.GlobalSettings.objects.all()[0]
    # print('task--> ',type(num) ,global_settings_obj.new_wenda_money, global_settings_obj.old_wenda_money)

    if task_obj.wenda_type == 1:  # 新问答
        money = num * global_settings_obj.new_wenda_money
        remark = "新增新问答{num}条".format(num=num)

    else:  # 老问答
        money = num * global_settings_obj.old_wenda_money
        remark = "新增老问答{num}条".format(num=num)
    print('money - - -  - - > ',money)
    # 记录消费明细
    models.BalanceDetail.objects.create(
        user=task_obj.release_user,
        account_type=2,
        money=money,
        oper_user=task_obj.release_user,
        remark=remark
    )
