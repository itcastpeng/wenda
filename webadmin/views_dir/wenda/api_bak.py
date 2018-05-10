#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from bson.objectid import ObjectId

from django.views.decorators.csrf import csrf_exempt

import datetime
import random


# 登录
@csrf_exempt
def login(request):
    if request.method == "POST":

        response = pub.ApiResponse()

        username = request.POST.get("username")
        password = request.POST.get("password")

        user_profile_obj = models.UserProfile.objects.filter(username=username, password=pub.str_encrypt(password), is_delete=False)

        if user_profile_obj:

            token = user_profile_obj[0].token
            if not token:
                token = str(ObjectId())
                user_profile_obj.update(token=token)

            response.status = True
            response.message = "登录成功!"

            response.data = {
                "token": token
            }
        else:
            response.status = False
            response.message = "登录失败, 用户名或密码错误!"

        return JsonResponse(response.__dict__)


@csrf_exempt
def get_wenda_task(request):

    response = pub.BaseResponse()

    if request.method == "POST":
        print(request.POST)

        token = request.POST.get("token")
        user_objs = models.UserProfile.objects.filter(token=token, token__isnull=False, is_delete=False)
        if user_objs:

            task_id = request.POST.get("task_id")
            status = request.POST.get("status")
            current_url = request.POST.get("current_url")
            cookies = request.POST.get("cookies")
            phone = request.POST.get("phone")
            ipaddr = request.POST.get("ipaddr")

            if current_url == "http://zhidao.baidu.com/new?word=&ie=GBK":
                response.status = False
                response.message = "任务发布异常"

            if response.status:
                wenda_robot_task_objs = models.WendaRobotTask.objects.filter(id=task_id)
                if wenda_robot_task_objs:
                    wenda_robot_task_obj = wenda_robot_task_objs[0]

                    if status == "1":     # 新发布问答
                        wenda_robot_task_obj.status = 2
                        wenda_robot_task_obj.wenda_url = current_url

                    elif status == "2":   # 回复问答
                        wenda_robot_task_obj.status = 5

                    elif status == "20":    # 回复异常
                        wenda_robot_task_obj.status = 20

                    elif status == "22":  # 回复异常
                        wenda_robot_task_obj.status = 22

                    elif status == "30":  # 标题过长
                        wenda_robot_task_obj.status = 30

                    elif status == "40":  # 链接失效
                        wenda_robot_task_obj.status = 40

                    else:   # status == 3  # 采纳问答
                        wenda_robot_task_obj.status = 6

                    wenda_robot_task_obj.update_date = datetime.datetime.now()
                    wenda_robot_task_obj.save()
                    models.RobotAccountLog.objects.create(
                        wenda_robot_task=wenda_robot_task_obj,
                        status=int(status),
                        phone_num=phone,
                        login_cookie=cookies,
                        ipaddr=ipaddr,
                    )

                    response.status = True
                    response.message = "提交成功"
                else:
                    response.status = False
                    response.message = "任务异常"
        else:
            response.status = False
            response.message = "token值错误"

    else:
        print(request.GET, request.POST)
        token = request.GET.get("token")
        status = request.GET.get("status")
        task_id = request.GET.get("task_id")

        user_objs = models.UserProfile.objects.filter(token=token, token__isnull=False, is_delete=False)
        if user_objs:

            # 只能获取10分钟内未操作的任务
            up_hours_time = datetime.datetime.now() - datetime.timedelta(minutes=10)

            if task_id and status == "5":   # 查询是否到采纳时间

                # 先查询任务状态是否正常
                wenda_robot_task_obj = models.WendaRobotTask.objects.get(id=task_id)
                if wenda_robot_task_obj.status not in [2, 5]:
                    response.status = True
                    response.error = "任务状态异常,请开始下一个任务"
                    return JsonResponse(response.__dict__)

                else:
                    if wenda_robot_task_obj.update_date < up_hours_time:

                        if wenda_robot_task_obj.status == 2:  # 如果状态不为 2, 5  等待回复和等待采纳, 则有异常
                            wenda_robot_task_obj = None

                        elif wenda_robot_task_obj.status == 5:
                            pass

                    else:   # 如果时间没有到,则设置任务为空
                        wenda_robot_task_obj = None

            else:
                wenda_robot_task_obj = None

                # 获取未完成的任务
                wenda_robot_task_objs = models.WendaRobotTask.objects.filter(status=status, update_date__isnull=True)
                # wenda_robot_task_obj = models.WendaRobotTask.objects.filter(status=2)
                if not wenda_robot_task_objs:
                    wenda_robot_task_objs = models.WendaRobotTask.objects.filter(status=status, update_date__lt=up_hours_time)
                    print('-' * 10, wenda_robot_task_objs)

                # 判断是否有任务
                if wenda_robot_task_objs:
                    wenda_robot_task_obj = wenda_robot_task_objs[0]

            print(wenda_robot_task_obj)
            if wenda_robot_task_obj:

                response.status = True

                release_platform = [i[0] for i in wenda_robot_task_obj.release_platform_choices if i[0] == wenda_robot_task_obj.release_platform][0]

                response.data = {
                    "task_id": wenda_robot_task_obj.id,
                    "release_platform": release_platform,
                    "status": wenda_robot_task_obj.status,
                }

                if wenda_robot_task_obj.status == 1:    # 发布新问答
                    response.data["title"] = wenda_robot_task_obj.title

                elif wenda_robot_task_obj.status == 2:  # 回复问答
                    response.data["url"] = wenda_robot_task_obj.wenda_url
                    response.data["content"] = wenda_robot_task_obj.content

                elif wenda_robot_task_obj.status == 5:   # 采纳

                    response.data["url"] = wenda_robot_task_obj.wenda_url
                    response.data["content"] = wenda_robot_task_obj.content

                else:
                    response.status = False
                    response.data = None
                    response.message = "操作异常"

                    return JsonResponse(response.__dict__)

                wenda_robot_task_obj.update_date = datetime.datetime.now()

                wenda_robot_task_obj.save()

            else:
                response.message = "task is null!"

        else:
            response.status = False
            response.message = "token值错误"

    return JsonResponse(response.__dict__)


@csrf_exempt
def check_ipaddr(request):
    response = pub.BaseResponse()

    if request.method == "GET":
        token = request.GET.get("token")

        user_objs = models.UserProfile.objects.filter(token=token, token__isnull=False, is_delete=False)
        if user_objs:
            ipaddr = request.GET.get("ipaddr")

            up_hours_time = datetime.datetime.now() - datetime.timedelta(days=1)
            robot_account_log_obj = models.RobotAccountLog.objects.filter(ipaddr=ipaddr, create_date__lt=up_hours_time)

            if robot_account_log_obj:
                response.status = False
                response.message = "该ip不能使用"

            else:
                response.status = True
                response.message = "该ip可以使用"

    else:
        response.status = False
        response.message = "请求异常"

    return JsonResponse(response.__dict__)


@csrf_exempt
def check_wenda_link(request):
    response = pub.BaseResponse()

    token = request.GET.get("token")
    user_objs = models.UserProfile.objects.filter(token=token, token__isnull=False, is_delete=False)
    if user_objs:
        if request.method == "GET":
            objs = models.WendaLink.objects.filter(status=1)
            if objs:
                response.data = {
                    'tid': objs.last().id,
                    'url': objs.last().url
                }
                response.status = True

            else:
                response.status = False
                response.message = "无任务"
        else:
            status = request.POST.get('status')
            tid = request.POST.get('tid')

            obj = models.WendaLink.objects.get(id=tid)
            obj.status = status
            obj.check_date = datetime.datetime.now()
            obj.save()

            response.status = True
            response.message = "提交成功"

    else:
        response.status = False
        response.message = "请求异常"

    return JsonResponse(response.__dict__)

