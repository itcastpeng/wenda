#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms.task_list import TaskListCreateForm, TaskListUpdateForm
import json

from django.db.models import F
from django.db.models import Q
from django.db.models import Sum


# 任务管理
@pub.is_login
def bianxiebaobiao(request):
    user_id = request.session["user_id"]


    if "type" in request.GET and request.GET["type"] == "ajax_json":

        # ##### 排序加搜索 ##### ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
        column_list = ['id', 'xiangmu', 'oper_user_id', 'create_date', 'edit_count','oper']

        q = Q()
        for index, field in enumerate(column_list):
            if field in request.GET and request.GET[field]:     # 如果该字段存在并且不为空
                q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        task_list_objs = models.BianXieBaoBiao.objects.filter(q)

        # ##### 排序加搜索 ##### ↑↑↑↑↑↑↑↑↑↑↑

        result_data = {
            "recordsFiltered": task_list_objs.count(),
            "option": []
        }

        # user_data = models.UserProfile.objects.filter(is_delete=False, role_id__in=[6, 7]).values_list('username')
        user_data = models.UserProfile.objects.filter(is_delete=False).values_list('username')
        user_data = [i[0] for i in user_data]

        xiangmu_data = ["总数据"]
        xiangmu_data.extend([i[1] for i in models.BianXieBaoBiao.xiangmu_choices])
        series_data = []
        objs = models.BianXieBaoBiao.objects.filter(create_date__lte='2018-5-12').values('xiangmu','oper_user__username').annotate(Sum('edit_count'))
        temp_dict = {}
        for obj in objs:
            username = obj['oper_user__username']
            xiangmu = obj['xiangmu']
            count = obj['edit_count__sum']
            if username not in temp_dict:
                temp_dict[username] = [0] * 7
            # 项目为索引 哪个项目就是第几个元素
            temp_dict[username][xiangmu] = count

        for k,v in temp_dict.items():
            v[0] = sum(v)
            series_data.append({
                    'data': v,
                    'type': 'line',
                    'smooth': True,
                    'name': k
            })



        print('进入的数据----->',series_data)
        option = {
            'xAxis': {
                'type': 'category',
                'data': xiangmu_data
            },
            'yAxis': {
                'type': 'value'
            },

            'title': {
                'title': '编辑编写量统计图'
            },
            'tooltip': {
                'trigger': 'axis'
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '3%',
                'containLabel': True
            },

            'legend': {
                # 'data': ['赵欣鹏','张聪' , '赵欣鹏1', '直接访问', '搜索引擎']
                'data': user_data
            },
            'series': series_data,

        }

        result_data['option'] = option

        # for index, obj in enumerate(task_list_objs[start: (start + length)], start=1):
        #
        #     if obj.create_at:
        #         create_date = obj.create_at.strftime("%Y-%m-%d %H:%M:%S")
        #     else:
        #         create_date = ""
        #
        #     if obj.update_at:
        #         update_at = obj.update_at.strftime("%Y-%m-%d %H:%M:%S")
        #     else:
        #         update_at = ""
        #
        #     status = ""
        #     for i in status_choices:
        #         if i[0] == obj.status:
        #             status = i[1]
        #             break
        #
        #     search_engine = ""
        #     for i in search_engine_choices:
        #         if i[0] == obj.search_engine:
        #             search_engine = i[1]
        #             break
        #
        #     # 排名变化
        #     ranking_change = ""
        #
        #     # 成功点击数
        #     success_click_numbers = ""
        #
        #     oper = ""
        #
        #     if obj.status == 1:     # 当前状态显示在线
        #         oper += """<a class="btn btn-round btn-sm bg-warning" aria-hidden="true" href="offline/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-cloud-download" aria-hidden="true"></i>下线</a>"""
        #
        #     else:   # 当前状态显示离线
        #         oper += """<a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="online/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-cloud-upload" aria-hidden="true"></i>上线</a>"""
        #
        #     oper += """
        #         <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="update/{obj_id}/" data-toggle="modal" data-target="#modal-width-700"><i class="icon fa-pencil-square-o"></i>修改</a>
        #         <a class="btn btn-round btn-sm bg-danger" aria-hidden="true" href="delete/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="fa fa-trash-o fa-fw"></i>删除</a>
        #     """
        #
        #     if user_obj.role.id in admin_role_list:
        #         oper += """<a class="btn btn-round btn-sm bg-info" aria-hidden="true" href="update/{obj_id}/" data-toggle="modal" data-target="#modal-width-700"><i class="icon fa-search" aria-hidden="true"></i>详情</a>"""
        #
        #     oper=oper.format(obj_id=obj.id)
        #
        #     # 管理员看到的字段和普通员工看到的字段不一样
        #     if user_obj.role.id in admin_role_list:
        #         table_data = [index, obj.keywords, obj.url, search_engine, obj.first_ranking, obj.now_ranking, ranking_change, obj.day_click_number, success_click_numbers, create_date, update_at, status, oper]
        #     else:
        #         table_data = [index, obj.keywords, obj.url, search_engine, obj.first_ranking, obj.now_ranking, ranking_change, create_date, status, oper]
        #     result_data["data"].append(table_data)

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, '../../wenda/templates/wenda/bianxiebaobiao/bianxiebaobiao_pjax.html', locals())
    return render(request, '../../wenda/templates/wenda/bianxiebaobiao/bianxiebaobiao.html', locals())


@pub.is_login
def bianxiebaobiao_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":
        # 添加
        if oper_type == "create":

            response.status = True
            response.message = "添加成功"

            form_obj = TaskListCreateForm(request.POST)

            if form_obj.is_valid():
                form_obj.cleaned_data["user_id"] = user_id
                models.Task.objects.create(**form_obj.cleaned_data)

            else:
                response.status = False
                for i in ["keywords", "url", "day_click_number", "search_engine", "click_strategy_id"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break

        # 批量添加
        elif oper_type == "batch_create":
            response.status = True
            response.message = "添加成功"
            print(request.POST)

            keywords = request.POST["keywords"]
            url = request.POST["url"]

            if len(keywords.strip().split()) != len(url.strip().split()):
                response.status = False
                response.message = "关键词数量和网址数量不一致!"

            else:
                keywords_list = keywords.strip().split()
                url_list = url.strip().split()

                task_objs = []
                for index in range(len(keywords_list)):
                    keywords = keywords_list[index].strip()
                    url = url_list[index].strip()

                    form_obj = TaskListCreateForm({"keywords": keywords, "url": url})

                    if form_obj.is_valid():
                        task_objs.append(models.Task(user_id=user_id, keywords=keywords, url=url))
                    else:
                        response.status = False

                        for i in ["keywords", "url"]:
                            if i in form_obj.errors:
                                response.message = "第{index}行发生错误: {message}".format(index=index+1, message=form_obj.errors[i])
                                break

                        if not response.status:
                            break

                if response.status:
                    models.Task.objects.bulk_create(task_objs)

        # 修改
        elif oper_type == "update":
            response.status = True
            response.message = "添加成功"
            user_obj = models.UserProfile.objects.select_related('role').get(id=user_id)

            # 1 4 表示是管理员权限
            if user_obj.role.id in [1, 4]:

                form_obj = TaskListUpdateForm(request.POST)
            else:
                form_obj = TaskListCreateForm(request.POST)

            if form_obj.is_valid():
                models.Task.objects.filter(id=o_id).update(**form_obj.cleaned_data)

            else:
                response.status = False
                for i in ["keywords", "url", "day_click_number", "search_engine", "click_strategy_id"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break
        # 删除用户
        elif oper_type == "delete":
            models.Task.objects.get(id=o_id).delete()
            response.status = True
            response.message = "删除成功"

        # 充值
        elif oper_type == "recharge":
            balance = request.POST.get("balance")

            if not balance or not balance.isdigit():
                response.status = False
                response.message = "充值金额有误"

            models.UserProfile.objects.filter(id=o_id).update(balance=F("balance") + int(balance))

            models.BalanceDetail.objects.create(
                user_id=o_id,
                type=1,
                money=balance,
                oper_user_id=user_id
            )

            response.status = True
            response.message = "充值成功"

        # 下线
        elif oper_type == "offline":
            models.Task.objects.filter(id=o_id).update(status=2)
            response.status = True
            response.message = "下线成功"

        # 上线
        elif oper_type == "online":
            models.Task.objects.filter(id=o_id).update(status=1)
            response.status = True
            response.message = "上线成功"

        return JsonResponse(response.__dict__)

    else:
        roles_dict = models.Role.objects.all().values("id", "name")

        # 添加
        if oper_type == "create":

            return render(request, 'paimingbao/task_list/task_list_modal_create.html', locals())

        # 批量添加
        if oper_type == "batch_create":

            return render(request, 'paimingbao/task_list/task_list_modal_batch_create.html', locals())

        # 修改
        elif oper_type == "update":

            # 修改的时候区分管理员用户和普通用户
            user_obj = models.UserProfile.objects.select_related('role').get(id=user_id)
            admin_role_list = [1, 4]

            task_list_obj = models.Task.objects.select_related("click_strategy").get(id=o_id)
            search_engine_choices = models.Task.search_engine_choices
            click_strategy_objs = models.ClickStrategy.objects.filter(user_id__in=[user_id, 1])  # 获取系统默认策略和自定义策略

            return render(request, 'paimingbao/task_list/task_list_modal_update.html', locals())

        # 删除
        elif oper_type == "delete":
            task_list_obj = models.Task.objects.get(id=o_id)
            return render(request, 'paimingbao/task_list/task_list_modal_delete.html', locals())

        # 下线
        elif oper_type == "offline":
            task_list_obj = models.Task.objects.get(id=o_id)
            return render(request, 'paimingbao/task_list/task_list_modal_offline.html', locals())

        # 上线
        elif oper_type == "online":
            task_list_obj = models.Task.objects.get(id=o_id)
            return render(request, 'paimingbao/task_list/task_list_modal_online.html', locals())


  # objs = models.BianXieBaoBiao.objects.select_related('oper_user').filter(create_date__lte='2018-05-11').values('xiangmu', 'oper_user__username').annotate(Sum('edit_count'))
  #
  #
  #       temp_dict = {}
  #       for obj in objs:
  #           # obj['xiangmu'] = models.BianXieBaoBiao.xiangmu_choices[obj['xiangmu'] - 1][1]
  #           # print(obj)
  #           username = obj['oper_user__username']
  #           edit_count = obj['edit_count__sum']
  #           xiangmu = obj['xiangmu']
  #
  #           if username not in temp_dict:
  #               temp_dict[username] = [0] * 7
  #
  #           temp_dict[username][xiangmu] = edit_count
  #           # print('temp_dict -->', temp_dict)
  #
  #       series_data = []
  #       for k, v in temp_dict.items():
  #           v[0] = sum(v)
  #           series_data.append({
  #               'data': v,
  #               'type': 'line',
  #               'smooth': True,
  #               'name': k
  #           })