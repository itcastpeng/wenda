#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse, redirect, HttpResponsePermanentRedirect
from webadmin.views_dir import pub
import redis
from webadmin import models
from django.http import JsonResponse

from bson.objectid import ObjectId

from django.views.decorators.csrf import csrf_exempt

import datetime
import random
from django.db.models import Q
from django.db.models import Count
import re
import json
from wenda_celery_project import tasks

from webadmin.modules.WeChat import WeChatPublicSendMsg
import base64
from webadmin.modules import RedisOper

redis_host = 'redis_host'


# 登录
@csrf_exempt
def login(request):
    if request.method == "POST":

        response = pub.ApiResponse()

        username = request.POST.get("username")
        password = request.POST.get("password")

        user_profile_obj = models.UserProfile.objects.filter(username=username, password=pub.str_encrypt(password),
                                                             is_delete=False)

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


# 发送企业微信消息
def send_msg(wenda_robot_task_obj, yuanyin):
    # 如果发布内容违规,则将判断该内容是否是由编辑写的
    edit_objs = models.EditPublickTaskManagement.objects.select_related('task__edit_user').filter(
        run_task=wenda_robot_task_obj
    )
    if edit_objs:
        edit_obj = edit_objs[0]
        edit_obj.status = 2
        edit_obj.save()

        models.EditTaskLog.objects.create(
            edit_public_task_management=edit_obj,
            title=edit_obj.title,
            content=edit_obj.content,
            remark=yuanyin
        )

        # 给对应编辑发送消息
        # weixin_id = edit_obj.task.edit_user.weixin_id
        # if weixin_id:
        #     now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     description = """
        #         通知时间: {now_datetime}\n\n
        #         问题: {title}\n\n
        #         答案: {content}\n\n
        #         异常原因: {yuanyin}
        #                 """.format(
        #         now_datetime=now_datetime,
        #         title=edit_obj.title,
        #         content=edit_obj.content,
        #         yuanyin=yuanyin
        #     )
        #     user_id_str = edit_obj.task.edit_user.weixin_id
        #     url = "http://wenda.zhugeyingxiao.com/edit_error_content/{t_id}/".format(t_id=edit_obj.id)
        #     tasks.send_msg.delay(user_id_str, description, w_type="card", url=url)
        #
        # else:
        #     now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     text = "通知时间: {now_datetime} \n通知平台:诸葛问答\n用户 {username} 未设置微信id".format(
        #         now_datetime=now_datetime,
        #         username=edit_obj.task.edit_user.username
        #     )
        #     tasks.send_msg.delay("zhangcong", text)


# 发送微信公众号消息
def send_msg_gongzhonghao(wenda_robot_task_obj, yuanyin):
    # 如果发布内容违规,则将判断该内容是否是由编辑写的
    edit_objs = models.EditPublickTaskManagement.objects.select_related('task__edit_user').filter(
        run_task=wenda_robot_task_obj
    )
    if edit_objs:
        edit_obj = edit_objs[0]
        # edit_obj.status = 2
        # edit_obj.save()
        edit_objs.update(status=2)

        models.EditTaskLog.objects.create(
            edit_public_task_management=edit_obj,
            title=edit_obj.title,
            content=edit_obj.content,
            remark=yuanyin
        )

        # now_datetime = datetime.datetime.now()
        # flag = False
        # if 20 > now_datetime.hour > 8:
        #     flag = True
        #
        # # 只在 8-20点之间通知,其余时间不通知
        # if not flag:
        #     return
        #
        # # 给对应编辑发送消息
        # openid = edit_obj.task.edit_user.openid
        # if openid:
        #     now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     url = "http://wenda.zhugeyingxiao.com/edit_error_content/{t_id}/".format(t_id=edit_obj.id)
        #     post_data = {
        #         "touser": openid,
        #         "template_id": "REblvLGT0dVxwzyrp28mBaXKF6XnHhP2_b7hXjUyI2A",
        #         "url": url,
        #         "data": {
        #             "first": {
        #                 "value": "问答任务异常！",
        #                 "color": "#173177"
        #             },
        #             "keyword2": {
        #                 "value": now_datetime,
        #                 "color": "#173177"
        #             },
        #             "remark": {
        #                 "value": "问题:{title}\n\n答案:{content}\n\n异常原因:{yuanyin}".format(
        #                     title=edit_obj.title,
        #                     content=edit_obj.content,
        #                     yuanyin=yuanyin
        #                 ),
        #                 "color": "#173177"
        #             }
        #         }
        #     }
        #
        #     tasks.send_msg_gongzhonghao.delay(post_data)
        #
        # else:
        #     now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #     text = "通知时间: {now_datetime} \n通知平台:诸葛问答\n用户 {username} 未设置微信id".format(
        #         now_datetime=now_datetime,
        #         username=edit_obj.task.edit_user.username
        #     )
        #     tasks.send_msg.delay("zhangcong", text)


# 任务完成
def task_ok(wenda_robot_task_obj):
    wenda_robot_task_obj.status = 6
    edit_obj = models.EditPublickTaskManagement.objects.filter(
        run_task_id=wenda_robot_task_obj.id
    )
    if edit_obj:
        edit_obj.update(
            status=3,
            update_date=datetime.datetime.now()
        )


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
            area = request.POST.get("area")
            img_src = request.POST.get("img_src")     # 回复内容发布图片获取到的图片url

            if current_url == "http://zhidao.baidu.com/new?word=&ie=GBK":
                response.status = False
                response.message = "任务发布异常"

            if response.status:
                wenda_robot_task_objs = models.WendaRobotTask.objects.filter(id=task_id)
                if wenda_robot_task_objs:
                    wenda_robot_task_obj = wenda_robot_task_objs[0]

                    if status == "1":  # 新发布问答
                        wenda_robot_task_obj.status = 2

                        if not current_url.endswith(".html"):
                            current_url = \
                            re.findall(".*html", "https://zhidao.baidu.com/question/1612479735.html&fr=none")[0]

                        wenda_robot_task_obj.wenda_url = current_url
                        if wenda_robot_task_obj.task.id == 356:
                            wenda_robot_task_obj.next_date = datetime.datetime.now() + datetime.timedelta(days=2)
                        else:
                            wenda_robot_task_obj.next_date = datetime.datetime.now() + datetime.timedelta(
                                # minutes=random.randint(60 * 3, 60 * 5))
                                minutes=random.randint(60 * 1, 60 * 2))

                    elif status == "2":  # 回复问答
                        if wenda_robot_task_obj.wenda_type == 2:  # 老问答

                            # 如果当前任务为已完成状态,不做任何处理
                            if wenda_robot_task_obj.status != 6:
                                if img_src: # 如果回复内容存在图片，则保存图片
                                    wenda_robot_task_obj.img_src = img_src

                                task_ok(wenda_robot_task_obj)
                                obj = models.TongjiKeywords.objects.filter(run_task=wenda_robot_task_obj)

                                # 存在,则更新, 不存在新增
                                if not obj:
                                    models.TongjiKeywords.objects.create(
                                        task=wenda_robot_task_obj.task,
                                        title=wenda_robot_task_obj.title,
                                        content=wenda_robot_task_obj.content,
                                        url=wenda_robot_task_obj.wenda_url,
                                        run_task=wenda_robot_task_obj,
                                        img_src=img_src
                                    )

                                else:
                                    obj[0].content = wenda_robot_task_obj.content
                                    obj[0].save()

                        elif not wenda_robot_task_obj.task:  # 养账号问答
                            wenda_robot_task_obj.status = 6

                        else:  # 新问答
                            wenda_robot_task_obj.status = 5
                            wenda_robot_task_obj.next_date = datetime.datetime.now() + datetime.timedelta(
                                minutes=random.randint(60 * 5, 60 * 6))

                    elif status == "20":  # 回复内容异常
                        wenda_robot_task_obj.status = 20
                        send_msg(wenda_robot_task_obj, "回复内容异常")
                        send_msg_gongzhonghao(wenda_robot_task_obj, "回复内容异常")

                    elif status == "22":  # 发布内容异常
                        wenda_robot_task_obj.status = 22
                        send_msg(wenda_robot_task_obj, "发布内容异常")
                        send_msg_gongzhonghao(wenda_robot_task_obj, "发布内容异常")

                    elif status == "30":  # 标题过长
                        wenda_robot_task_obj.status = 30
                        send_msg(wenda_robot_task_obj, "标题过长")
                        send_msg_gongzhonghao(wenda_robot_task_obj, "标题过长")
                    #
                    elif status == "40":  # 链接失效

                        # 如果是老问答,直接将状态修改为已完成
                        if wenda_robot_task_obj.wenda_type == 2:
                            wenda_robot_task_obj.status = 6
                        else:
                            wenda_robot_task_obj.status = 40
                            # send_msg(wenda_robot_task_obj, "链接失效")
                            # send_msg_gongzhonghao(wenda_robot_task_obj, "链接失效")

                    elif status == "50":  # 未找到采纳答案
                        # 未找到采纳答案重新发布
                        wenda_robot_task_obj.status = 2

                    elif status == "60":  # 发布账号异常
                        # 发布账号异常,重新发布
                        wenda_robot_task_obj.status = 1

                    elif status == "70":  # 链接异常,操作老问答未找到链接
                        # 链接异常,操作老问答未找到链接
                        wenda_robot_task_obj.status = 70

                    else:  # status == 5  # 采纳问答
                        task_ok(wenda_robot_task_obj)
                        xinlaowenda_status = wenda_robot_task_obj.task.release_user.xinlaowenda_status
                        if xinlaowenda_status == 2:
                            obj = models.TongjiKeywords.objects.filter(run_task=wenda_robot_task_obj)
                            # 存在,则更新, 不存在新增
                            if not obj:
                                models.TongjiKeywords.objects.create(
                                    task=wenda_robot_task_obj.task,
                                    title=wenda_robot_task_obj.title,
                                    content=wenda_robot_task_obj.content,
                                    url=wenda_robot_task_obj.wenda_url,
                                    run_task=wenda_robot_task_obj
                                )

                            else:
                                obj[0].content = wenda_robot_task_obj.content
                                obj[0].save()

                    wenda_robot_task_obj.update_date = datetime.datetime.now()
                    wenda_robot_task_obj.save()
                    models.RobotAccountLog.objects.create(
                        wenda_robot_task=wenda_robot_task_obj,
                        status=int(status),
                        phone_num=phone,
                        login_cookie=cookies,
                        ipaddr=ipaddr,
                        area=area
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
        area = request.GET.get("area")
        is_test = request.GET.get("is_test", False)
        new_wenda = request.GET.get("new_wenda")

        user_objs = models.UserProfile.objects.filter(token=token, token__isnull=False, is_delete=False)
        if user_objs:
            status_list = [5, 2, 1]  # 5表示采纳,2表示回复,1表示发布

            # 获取测试任务
            if is_test:
                print("获取测试任务")
                wenda_robot_task_objs = models.WendaRobotTask.objects.select_related('task__release_user').filter(
                    # next_date__lt=datetime.datetime.now(),
                    task__is_test=True,
                    status__in=status_list
                ).order_by('?')[:5]
            else:
                print("获取新问答")
                wenda_robot_task_objs = None
                if new_wenda:
                    wenda_robot_task_objs = models.WendaRobotTask.objects.select_related('task__release_user').filter(
                        status__in=status_list,
                        next_date__lt=datetime.datetime.now(),
                        wenda_type__in=[1, 10],
                        task__is_test=False
                    ).exclude(
                        task__release_user_id=235
                    ).order_by('-status')
                    print('wenda_robot_task_objs -->', wenda_robot_task_objs)

                if not wenda_robot_task_objs:
                    # 优先处理老问答优先的问题
                    wenda_robot_task_objs = models.WendaRobotTask.objects.select_related('task__release_user').filter(
                        status__in=status_list,
                        next_date__lt=datetime.datetime.now(),
                        wenda_type=2,
                        task__release_user__laowenda_youxian=True,
                        task__is_test=False
                    ).order_by('?')
                    print('wenda_robot_task_objs -->', wenda_robot_task_objs)

                # 如果没有老问答优先处理的任务,则处理新问答
                if not wenda_robot_task_objs:
                    print("没有老问答优先的任务")
                    # 新问答 不包括养账号任务
                    wenda_robot_task_objs = models.WendaRobotTask.objects.select_related("task__release_user").filter(
                        status__in=status_list,
                        next_date__lt=datetime.datetime.now(),
                        wenda_type__in=[1, 10],  # 新问答或新问答补发
                    ).exclude(task__release_user_id=235).order_by('oper_num')[:500]
                    print('wenda_robot_task_objs 新问答 不包括养账号任务 -->', wenda_robot_task_objs)

                flag = False
                for obj in wenda_robot_task_objs:
                    if obj.status == 5:
                        robot_account_log_obj = obj.robotaccountlog_set.filter(status=1).last()
                        if robot_account_log_obj.area != area:
                            continue
                    flag = True
                    break
                print('flag -->', flag)

                # 如果正式新问答没有任务则操作养账号任务
                if not wenda_robot_task_objs or not flag:
                    wenda_robot_task_objs = models.WendaRobotTask.objects.select_related("task__release_user").filter(
                        status__in=status_list,
                        next_date__lt=datetime.datetime.now(),
                        wenda_type__in=[1, 10],  # 新问答或新问答补发
                    ).order_by('-status')[:500]

                    print('wenda_robot_task_objs 养账号任务 -->', wenda_robot_task_objs)

                # 如果没有新问答, 则处理老问答
                if not wenda_robot_task_objs:
                    print("没有老问答优先任务或新问答任务")
                    wenda_robot_task_objs = models.WendaRobotTask.objects.select_related("task__release_user").filter(
                        status__in=status_list,
                        next_date__lt=datetime.datetime.now(),
                        wenda_type=2,
                        task__is_test=False
                    ).order_by('?')[:5]

            wenda_robot_task_obj = None
            print(wenda_robot_task_objs)
            for obj in wenda_robot_task_objs:
                if obj.status == 5:
                    robot_account_log_obj = obj.robotaccountlog_set.filter(status=1).last()
                    if robot_account_log_obj.area != area:
                        continue
                print(obj)
                wenda_robot_task_obj = obj
                break

            # 如果没有新闻单则处理老问答
            if not wenda_robot_task_obj:
                print("-->没有老问答优先任务或新问答任务")
                wenda_robot_task_objs = models.WendaRobotTask.objects.select_related("task__release_user").filter(
                    status__in=status_list,
                    next_date__lt=datetime.datetime.now(),
                    wenda_type=2,
                    task__is_test=False
                ).order_by('?')[:5]
                if wenda_robot_task_objs:
                    wenda_robot_task_obj = wenda_robot_task_objs[0]
                else:
                    print("无任务")

            if wenda_robot_task_obj:
                print('-->', wenda_robot_task_obj, wenda_robot_task_obj.status)

                response.status = True

                release_platform = [i[0] for i in wenda_robot_task_obj.release_platform_choices if
                                    i[0] == wenda_robot_task_obj.release_platform][0]

                response.data = {
                    "task_id": wenda_robot_task_obj.id,
                    "release_platform": release_platform,
                    "status": wenda_robot_task_obj.status,
                    "wenda_type": wenda_robot_task_obj.wenda_type,
                }

                # 没有任务ID的属于养账号的任务,发布任务的id 为 235 的也是养账号任务
                if not wenda_robot_task_obj.task or wenda_robot_task_obj.task.release_user.id == 235:
                    response.data["yangzhanghao"] = True
                else:
                    response.data["yangzhanghao"] = False

                if wenda_robot_task_obj.status == 1:  # 发布新问答
                    response.data["title"] = wenda_robot_task_obj.title

                elif wenda_robot_task_obj.status == 2:  # 回复问答
                    response.data["url"] = wenda_robot_task_obj.wenda_url
                    response.data["title"] = wenda_robot_task_obj.title
                    response.data["content"] = wenda_robot_task_obj.content
                    response.data["img_content"] = wenda_robot_task_obj.img_content
                    response.data["wenda_type"] = wenda_robot_task_obj.wenda_type

                    if wenda_robot_task_obj.task_id:  # 如果没有task_id 则是测试任务
                        response.data[
                            "shangwutong_url"] = "http://wenda.zhugeyingxiao.com/api/tiaozhuan/?id={uid}".format(
                            uid=wenda_robot_task_obj.task.release_user.id
                        )

                    if wenda_robot_task_obj.wenda_type == 2:  # 老问答
                        keywords_top_info_objs = models.KeywordsTopInfo.objects.select_related('keyword').filter(
                            url=wenda_robot_task_obj.wenda_url)
                        search_keywords_list = set()
                        for keywords_top_info_obj in keywords_top_info_objs:
                            search_keywords_list.add(keywords_top_info_obj.keyword.keyword)
                        response.data["search_keywords"] = list(search_keywords_list)

                        wenda_robot_task_obj.oper_num = models.RobotAccountLog.objects.filter(
                            wenda_robot_task=wenda_robot_task_obj).count()

                    if wenda_robot_task_obj.add_map == 1:
                        response.data["map"] = {
                            "map_search_keywords": wenda_robot_task_obj.task.release_user.map_search_keywords,
                            "map_match_keywords": wenda_robot_task_obj.task.release_user.map_match_keywords,
                            "move_map_coordinate": wenda_robot_task_obj.task.release_user.move_map_coordinate,
                        }

                elif wenda_robot_task_obj.status == 5:  # 采纳
                    response.data["title"] = wenda_robot_task_obj.title
                    response.data["url"] = wenda_robot_task_obj.wenda_url
                    response.data["content"] = wenda_robot_task_obj.content

                    phone_num = wenda_robot_task_obj.robotaccountlog_set.filter(status=1).last().phone_num
                    response.data["phone_num"] = phone_num

                else:
                    response.status = False
                    response.data = None
                    response.message = "操作异常"

                    return JsonResponse(response.__dict__)

                wenda_robot_task_obj.update_date = datetime.datetime.now()
                wenda_robot_task_obj.next_date = datetime.datetime.now() + datetime.timedelta(minutes=20)

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
            # ipaddr = request.GET.get("ipaddr")
            # ipaddr_list = RedisOper.read_from_cache('api_check_ipaddr_ip_list')
            # if ipaddr in ipaddr_list:
            #
            #     # up_hours_time = datetime.datetime.now() - datetime.timedelta(hours=6)
            #     # robot_account_log_obj = models.RobotAccountLog.objects.filter(ipaddr=ipaddr, create_date__lt=up_hours_time)
            #     #
            #     # if robot_account_log_obj:
            #     response.status = False
            #     response.message = "该ip不能使用"
            #
            # else:
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
            objs = models.WendaLink.objects.filter(status=1, check_date__lt=datetime.datetime.now())
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

            obj = models.WendaLink.objects.select_related('task').get(id=tid)
            obj.status = status
            obj.update_date = datetime.datetime.now()
            obj.save()

            if obj.status == '2':
                wenda_objs = obj.task.wendarobottask_set.filter(wenda_url=obj.url)
                if wenda_objs:
                    print('wenda_objs -  -> ', wenda_objs)
                    wenda_obj = wenda_objs[0]
                    models.TongjiKeywords.objects.create(
                        title=wenda_obj.title,
                        content=wenda_obj.content,
                        url=wenda_obj.wenda_url,
                        task_id=obj.task.id
                    )

            response.status = True
            response.message = "提交成功"

    else:
        response.status = False
        response.message = "请求异常"

    return JsonResponse(response.__dict__)


@csrf_exempt
def set_keywords_rank(request):
    response = pub.BaseResponse()

    token = request.GET.get("token")
    select_type = request.GET.get("select_type")
    user_objs = models.UserProfile.objects.filter(token=token, token__isnull=False, is_delete=False)
    if user_objs:
        if request.method == "GET":
            filter_datetime = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y-%m-%d"), '%Y-%m-%d')

            q = Q()
            if select_type:
                # q.add(Q(Q(z_update_date__isnull=True) | Q(z_update_date__lt=filter_datetime))
                q = Q(Q(z_update_date__isnull=True) | Q(z_update_date__lt=filter_datetime))
                # q.add(Q(task__wenda_type__in=[1,10]),Q.AND())
            else:
                q = Q(Q(update_date__isnull=True) | Q(update_date__lt=filter_datetime))
            # q.add(Q(task__wenda_type__in=[1, 10]), Q.AND)
            # print('q -- > ',q)
            objs = models.SearchKeywordsRank.objects.select_related('task').filter(q).order_by('?')
            if objs:  # 有任务
                obj = objs[0]
                response.status = True
                response.data = {
                    "task_id": obj.id,
                    "client_user_id": obj.client_user.id,
                    "keywords": obj.keywords,
                }

                if select_type:
                    obj.z_update_date = datetime.datetime.now()
                else:
                    obj.update_date = datetime.datetime.now()
                obj.save()

            else:  # 无任务
                response.status = True
                response.message = "当前无任务"

        else:  # POST

            url = request.POST.get("url")
            task_type = request.POST.get("task_type")
            client_user_id = request.POST.get("client_user_id")
            task_id = request.POST.get("task_id")
            rank = request.POST.get("rank")
            search_url = request.POST.get("search_url")

            task_objs = models.Task.objects.filter(
                release_user_id=client_user_id,
                is_delete=False,
                wenda_type__in=[1,10]
            ).exclude(status=11)

            number = re.search("\d+", url).group()  # 过滤出url中的数字
            print(number)

            flag = False
            for obj in task_objs:
                wendalink_objs = obj.wendalink_set.filter(url__contains=number)  # 在数据库中所属url中的数字,看是否能匹配到
                if wendalink_objs:  # 表示匹配到了

                    # datetime.datetime.strftime("%y-%m-%d %H:%M:%S")
                    date = datetime.datetime.now().strftime("%Y-%m-%d")

                    if select_type:
                        search_keywords_rank_log_objs = models.SearchKeywordsRankLog.objects.filter(
                            keywords_id=task_id,
                            create_date=date,
                            task_type=task_type,
                            data_type=2,
                        )
                        if search_keywords_rank_log_objs:
                            search_keywords_rank_log_obj = search_keywords_rank_log_objs[0]
                            before_rank = search_keywords_rank_log_obj.rank
                            search_keywords_rank_log_obj.rank = ", ".join([before_rank, rank])
                            search_keywords_rank_log_obj.save()
                        else:
                            models.SearchKeywordsRankLog.objects.create(
                                keywords_id=task_id,
                                rank=rank,
                                task_type=task_type,
                                search_url=search_url,
                                data_type=2,
                            )
                    else:
                        search_keywords_rank_log_objs = models.SearchKeywordsRankLog.objects.filter(
                            keywords_id=task_id,
                            create_date=date,
                            task_type=task_type,
                            data_type=1,
                        )
                        if search_keywords_rank_log_objs:
                            search_keywords_rank_log_obj = search_keywords_rank_log_objs[0]
                            before_rank = search_keywords_rank_log_obj.rank
                            search_keywords_rank_log_obj.rank = ", ".join([before_rank, rank])
                            search_keywords_rank_log_obj.save()
                        else:
                            models.SearchKeywordsRankLog.objects.create(
                                keywords_id=task_id,
                                rank=rank,
                                task_type=task_type,
                                search_url=search_url
                            )

                    flag = True
                    break

            response.status = True
            response.data = flag
            response.message = "提交成功"

    else:
        response.status = False
        response.message = "token值错误"

    return JsonResponse(response.__dict__)


def check_follow_wechat(request):
    response = pub.BaseResponse()
    user_id = request.GET.get("user_id")
    obj = models.UserProfile.objects.select_related('role').get(id=user_id)
    if obj.openid:
        response.status = True
        response.message = "关注成功"

        webchat_obj = WeChatPublicSendMsg()
        webchat_obj.batch_tagging(obj.openid, obj.role.tag_id)
    else:
        response.status = False

    return JsonResponse(response.__dict__)


def sendMsg(request):
    response = pub.BaseResponse()

    webchat_obj = WeChatPublicSendMsg()

    data = request.GET.get("data")
    touser = request.GET.get("touser")
    url = request.GET.get("url")

    print(dict(request.GET))
    print(data)
    # data = {
    #     "first": {
    #         "value": "问答养账号有新的任务需要处理！",
    #         "color": "#173177"
    #     },
    #     "keyword1": {
    #         "value": datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"),
    #     },
    #     # "keyword2": {
    #     #     "value": datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"),
    #     #     "color": "#173177"
    #     # },
    # }

    post_data = {
        # "touser": "o7Xw_0YmQrxqcYsRhFR2y7yQPBMU",
        "touser": touser,
        "template_id": "ksNf6WiqO5JEqd3bY6SUqJvWeL2-kEDqukQC4VeYVvw",
        "data": json.loads(data),
        "url": url,
    }

    webchat_obj.sendTempMsg(post_data=post_data)

    response.status = True
    response.message = "发送成功"

    return JsonResponse(response.__dict__)


# 查询关键词在百度首页知道的条数
@csrf_exempt
def keywords_top_set(request):
    response = pub.BaseResponse()

    if request.method == "POST":
        # post_data = {
        #     "url": "",
        #     "task_type": 1,  # 1 pc-网页   2 pc-知道  3 wap-网页
        #     "client_user_id": client_user_id,
        #     "task_id": task_id,
        #     "rank": rank_num,
        #     "search_url": search_url,
        #     "title": "",
        #     "is_caina": False,
        #     "huifu_num": 0
        # }
        url = request.POST.get("url").split("?")[0]
        task_type = request.POST.get("task_type")
        client_user_id = request.POST.get("client_user_id")
        task_id = request.POST.get("task_id")
        search_url = request.POST.get("search_url")
        is_caina = request.POST.get("is_caina")
        huifu_num = request.POST.get("huifu_num")
        rank = request.POST.get("rank")
        title = request.POST.get("title")

        keywords_top_set_obj = models.KeywordsTopSet.objects.get(id=task_id)
        models.KeywordsTopInfo.objects.create(
            keyword=keywords_top_set_obj,
            title=title,
            url=url,
            page_type=task_type,
            rank=rank,
            is_caina=is_caina,
            huifu_num=huifu_num
        )
        cover_num = models.KeywordsTopInfo.objects.filter(keyword=keywords_top_set_obj).count()
        keywords_top_set_obj.top_page_cover = cover_num
        keywords_top_set_obj.status = 2
        keywords_top_set_obj.save()

    else:
        objs = models.KeywordsTopSet.objects.filter(status=1, is_delete=False, client_user_id=193)
        if not objs:
            objs = models.KeywordsTopSet.objects.filter(status=1, is_delete=False)
        if objs:
            obj = objs[0]
            obj.status = 3
            obj.save()
            response.status = True
            response.data = {
                "keywords": obj.keyword,
                "client_user_id": obj.client_user_id,
                "task_id": obj.id
            }

        else:
            response.status = False
            response.message = "当前无任务"

    return JsonResponse(response.__dict__)


@csrf_exempt
def keywords_top_set_oper(request, oper_type):
    response = pub.BaseResponse()

    if request.method == "POST":
        if oper_type == "update":
            """
            post_data = {
                "url": "",
                "task_type": 1,         # 1 pc-网页  3 wap-网页
                "kid": kid,             # 搜索词id
                "keyword": keyword,     # 搜索词
                "rank": rank_num,
                "client_user_id": client_user_id,       # 客户id
            }
            """

            """
                {
                    "huifu_num": 2,
                    "title": "\u80f8\u6da8\u662f\u600e\u4e48\u56de\u4e8b",
                    "task_type": 1,
                    "keyword": "\u80f8\u6da8",
                    "kid": 2189,
                    "url": "https://zhidao.baidu.com/question/1610207357483962387.html",
                    "is_caina": false,
                    "rank": 6,
                    "client_user_id": 25
                }
            """
            print(request.POST)
            url = request.POST.get("url")
            client_user_id = request.POST.get("client_user_id")
            is_pause = int(request.POST.get("is_pause"))
            obj = models.TongjiKeywords.objects.filter(
                task__release_user_id=client_user_id,
                url=url,
            )
            # print(obj.count())
            #
            # print(obj, client_user_id, type(client_user_id), url)
            if obj:
                obj[0].is_update = True
                obj[0].update_date = datetime.datetime.now()

                if not obj[0].run_task:  # 没有该值表示是渠道做的
                    obj[0].delete()
                    response.status = True
                    response.message = "修改成功 - 渠道操作"
                else:
                    robot_task_obj = models.WendaRobotTask.objects.select_related('task').get(id=obj[0].run_task.id)
                    print('robot_task_obj -->', robot_task_obj.id)
                    edit_pulick_task_objs = models.EditPublickTaskManagement.objects.filter(run_task=robot_task_obj)
                    # print('edit_pulick_task_obj -->', edit_pulick_task_obj)
                    if edit_pulick_task_objs:
                        edit_pulick_task_obj = edit_pulick_task_objs[0]
                        if not is_pause:  # is_pause = False 任务没有关闭,需要打回
                            robot_task_obj.status = 20
                            robot_task_obj.next_date = datetime.datetime.now() + datetime.timedelta(minutes=10)

                            edit_pulick_task_obj.update_date = datetime.datetime.now()
                            if edit_pulick_task_obj.status < 3:
                                print("已经打回")
                            else:
                                if robot_task_obj.task.status <= 7:
                                    edit_pulick_task_obj.status = 2
                                    edit_pulick_task_obj.is_select_cover_back = True

                                    models.EditTaskLog.objects.create(
                                        edit_public_task_management=edit_pulick_task_obj,
                                        title=edit_pulick_task_obj.title,
                                        content=edit_pulick_task_obj.content,
                                        remark="查询覆盖无匹配答案"
                                    )
                        else:  # 任务被关闭  is_pause = True
                            robot_task_obj.status = 6
                            robot_task_obj.next_date = datetime.datetime.now() + datetime.timedelta(minutes=10)
                            edit_pulick_task_obj.status = 3
                            edit_pulick_task_obj.is_select_cover_back = True
                            edit_pulick_task_obj.update_date = datetime.datetime.now()

                            if not obj[0].is_pause:  # 如果该任务当前状态为未暂停状态
                                models.EditTaskLog.objects.create(
                                    edit_public_task_management=edit_pulick_task_obj,
                                    title=edit_pulick_task_obj.title,
                                    content=edit_pulick_task_obj.content,
                                    remark="查询覆盖答案被删除,问答被关闭"
                                )
                        edit_pulick_task_obj.save()
                    obj[0].save()
                    robot_task_obj.save()

                    response.status = True
                    response.message = "修改成功"

    else:
        response.status = False
        response.message = "请求异常"

    return JsonResponse(response.__dict__)


# 查看3天未联系的客户信息
def tongji_kehu_shiyong(request):
    data = RedisOper.read_from_cache("tongji_kehu_shiyong")
    data_list = data.strip().split("\n")
    return render(request, 'api/tongji_kehu_shiyong.html', locals())


# 查询关键词覆盖(覆盖模式)
@csrf_exempt
def keywords_cover(request):
    response = pub.BaseResponse()

    if request.method == "POST":
        """
        {
            'client_user_id': 25,
            'task_type': 1,
            'url': 'https://zhidao.baidu.com/question/578414474.html',
            'kid': 2087,
            'rank': 10,
            'keyword': '胸部变大的好方法'
        }
        """
        kid = request.POST.get("kid")
        page_type = request.POST.get("task_type")
        rank = request.POST.get("rank")
        url = request.POST.get("url")
        is_zhedie = request.POST.get("is_zhedie", False)
        zhidao_hehuoren = request.POST.get("zhidao_hehuoren", False)
        xiongzhanghao = request.POST.get("xiongzhanghao", False)

        keywords_cover_obj = models.KeywordsCover.objects.filter(
            keywords_id=kid,
            page_type=page_type,
            url=url,
            create_date__gte=datetime.datetime.now().strftime("%Y-%m-%d")
        )

        if not keywords_cover_obj:
            if zhidao_hehuoren or xiongzhanghao:     # 知道合伙人排名
                rank_type = 1
                if zhidao_hehuoren:
                    rank_type = 2
                if xiongzhanghao:
                    rank_type = 2
                models.KeywordsCover.objects.create(
                    keywords_id=kid,
                    page_type=page_type,
                    rank=rank,
                    url=url,
                    is_zhedie=is_zhedie,
                    rank_type=rank_type
                )

            else:
                keywords_top_set_objs = models.KeywordsTopSet.objects.filter(id=kid)
                keywords_top_set_objs.update(
                    update_select_cover_date=datetime.datetime.now()
                )
                wenda_robot_task_objs = models.WendaRobotTask.objects.filter(
                    task__release_user_id=keywords_top_set_objs[0].client_user.id,
                    wenda_url=url
                )

                models.EditPublickTaskManagement.objects.filter(run_task_id=wenda_robot_task_objs[0].id).update(status=3)

                if wenda_robot_task_objs[0].add_map == 1:
                    task_type = 2
                else:
                    task_type = 1

                models.KeywordsCover.objects.create(
                    keywords_id=kid,
                    page_type=page_type,
                    rank=rank,
                    url=url,
                    task_type=task_type,
                    is_zhedie=is_zhedie
                )

        response.status = True
        response.message = "添加成功"

    else:
        now_date = datetime.datetime.now().strftime("%Y-%m-%d")
        area = request.GET.get('area')
        print('area -=-=>', area)
        print("--->1: ", datetime.datetime.now())
        rc = redis.StrictRedis(host=redis_host, port=6379,db=8, decode_responses=True)
        # 建立连接

        flag = True
        while True:
            redis_data = rc.rpop('data')
            redis_len = rc.llen('data')
            print('redis_len --->', redis_len, type(redis_len), redis_data, type(redis_data))
            if redis_len < 500 and not rc.get('huancunguanjianci_time'):
                rc.set('huancunguanjianci_time', 1)
                rc.expire('huancunguanjianci_time', 120)
                tasks.huancunguanjianci.delay()

            if not redis_data:
                flag = False
                break
            else:
                redis_data = json.loads(redis_data)
                # {'keyword_id': 139344, 'keyword': '八大处腹壁整形', 'area': '广东阳江', 'client_user_id': 165}
                result_area = redis_data['area']
                if result_area == area:
                    rc.lpush('data', json.dumps(redis_data))
                    continue
                break

        if flag and area:
            updateData = {
                'update_select_cover_date': datetime.datetime.now(),
                'status': 3,
                'area': area,
            }

            # 当日查询次数
            search_count = models.KeywordsSearchLog.objects.filter(
                create_date__gt=now_date,
                keyword_id=redis_data['keyword_id']
            ).count()
            # if search_count < 2:   # 如果今日查询次数小于2次，则在查询一次
            #     del updateData['update_select_cover_date']

            keywords_top_set_objs = models.KeywordsTopSet.objects.select_related('client_user').filter(id=redis_data['keyword_id'])
            keywords_top_set_objs.update(**updateData)
            # KeywordsSearchLog
            models.KeywordsSearchLog.objects.create(
                keyword_id=redis_data['keyword_id'],
                area=area
            )

            print("--->4: ", datetime.datetime.now())

            xiongzhanghao_website = keywords_top_set_objs[0].client_user.xiongzhanghao_website
            zhidao_hehuoren_website = keywords_top_set_objs[0].client_user.zhidao_hehuoren_website
            data = {
                "kid": redis_data['keyword_id'],  # 关键词id
                "keyword": redis_data['keyword'],  # 关键词
                "client_user_id": redis_data['client_user_id'],  # 客户id
                "map_match_keywords": redis_data['map_match_keywords'],  # 地图匹配文字
                "xiongzhanghao_website": xiongzhanghao_website,  # 熊掌号主页地址
                "zhidao_hehuoren_website": zhidao_hehuoren_website,  # 知道合伙人主页地址
            }

            response.status = True
            response.data = data

        else:
            response.status = False
            response.message = "当前无任务"

    return JsonResponse(response.__dict__)

# 查询关键词覆盖(覆盖模式)  调试模式
@csrf_exempt
def keywords_cover_debug(request):
    response = pub.BaseResponse()

    if request.method == "POST":
        """
        {
            'client_user_id': 25,
            'task_type': 1,
            'url': 'https://zhidao.baidu.com/question/578414474.html',
            'kid': 2087,
            'rank': 10,
            'keyword': '胸部变大的好方法'
        }
        """
        kid = request.POST.get("kid")
        page_type = request.POST.get("task_type")
        rank = request.POST.get("rank")
        url = request.POST.get("url")
        is_zhedie = request.POST.get("is_zhedie", False)

        keywords_cover_obj = models.KeywordsCover.objects.filter(
            keywords_id=kid,
            page_type=page_type,
            url=url,
            create_date__gte=datetime.datetime.now().strftime("%Y-%m-%d")
        )

        if not keywords_cover_obj:
            keywords_top_set_objs = models.KeywordsTopSet.objects.filter(id=kid)
            keywords_top_set_objs.update(
                update_select_cover_date=datetime.datetime.now()
            )
            wenda_robot_task_objs = models.WendaRobotTask.objects.filter(
                task__release_user_id=keywords_top_set_objs[0].client_user.id,
                wenda_url=url
            )

            models.EditPublickTaskManagement.objects.filter(run_task_id=wenda_robot_task_objs[0].id).update(status=3)

            if wenda_robot_task_objs[0].add_map == 1:
                task_type = 2
            else:
                task_type = 1

            models.KeywordsCover.objects.create(
                keywords_id=kid,
                page_type=page_type,
                rank=rank,
                url=url,
                task_type=task_type,
                is_zhedie=is_zhedie
            )

        response.status = True
        response.message = "添加成功"

    else:
        keywords_objs = models.KeywordsTopSet.objects.select_related('client_user', 'client_user__role').filter(
            is_delete=False,
            client_user__status=1,
            client_user__role_id=15
        )
        keywords_obj = keywords_objs[0]

        xiongzhanghao_website = keywords_obj.client_user.xiongzhanghao_website
        zhidao_hehuoren_website = keywords_obj.client_user.zhidao_hehuoren_website
        data = {
            "kid": keywords_obj.id,  # 关键词id
            # "keyword": keywords_obj.keyword,  # 关键词
            "keyword": "沈阳白癜风",  # 关键词
            "client_user_id": keywords_obj.client_user_id,  # 客户id
            "map_match_keywords": keywords_obj.client_user.map_match_keywords,  # 地图匹配文字
            "xiongzhanghao_website": xiongzhanghao_website,  # 熊掌号主页地址
            "zhidao_hehuoren_website": zhidao_hehuoren_website,  # 知道合伙人主页地址
        }

        response.status = True
        response.data = data

    return JsonResponse(response.__dict__)


# 检查知道url 是我们自己操作的(覆盖模式)
@csrf_exempt
def check_zhidao_url(request):
    print('进入判断--------------')
    response = pub.BaseResponse()

    """
    post_data = {
                "url": "",
                "task_type": 1,  # 1 pc-网页  3 wap-网页
                "kid": kid,     # 搜索词id
                "rank": rank_num,
                "client_user_id": client_user_id,       # 客户id
            }
    """
    if request.method == "POST":
        print('request_POST===> ',request.POST)
        url = request.POST.get("url")
        client_user_id = request.POST.get("client_user_id")
        is_pause = int(request.POST.get("is_pause"))
        browse_times_text = request.POST.get('browse_times_text')
        print('---------> ',url, client_user_id, is_pause)
        tongji_keywords_objs = models.TongjiKeywords.objects.filter(
            task__release_user_id=client_user_id,
            url=url,
            # is_pause=False,         # 未暂停, 已发布,答案被删除,问答关闭,则会将该字段修改为True
        )
        print('tongji_keywords_objs=====> ',tongji_keywords_objs)
        # 如果统计表中存在,则表示操作过
        if tongji_keywords_objs:
            if is_pause:
                tongji_keywords_objs.update(is_pause=True)
            #     models.EditPublickTaskManagement.objects.filter(run_task_id=obj[0].run_task_id).update(status=3)
            #     models.WendaRobotTask.objects.filter(id=obj[0].run_task_id).update(status=6)
            # print('tongji_keywords_objs---> ',tongji_keywords_objs[0])
            response.status = True
            response.data = {
                "content": [i[0] for i in tongji_keywords_objs.values_list('content')]
            }
            # print('response----> ',response.data)

        else:
            """
            {
                'huifu_num': 5,
                'url': 'https://zhidao.baidu.com/question/1861100693274616587.html',
                'task_type': 1,
                'kid': 2046,
                'rank': 5,
                'client_user_id': 25,
                'keyword': '打针丰胸',
                'is_caina': True,
                'ask_title': "fdsafdsa"
                }
            """
            page_type = request.POST.get("task_type")
            keyword_id = request.POST.get("kid")
            title = request.POST.get("title")
            rank = request.POST.get("rank")
            is_caina = int(request.POST.get("is_caina"))
            huifu_num = request.POST.get("huifu_num")
            browse_times_text = 0
            if request.POST.get('browse_times_text'):
                browse_times_text = request.POST.get('browse_times_text')
            if not is_pause:  # 如果任务没有关闭
                print('--> is_pause false')
                keywords_top_info_objs = models.KeywordsTopInfo.objects.filter(
                    url=url,
                    page_type=request.POST.get("task_type"),
                    keyword_id=request.POST.get("kid"),
                )

                if not keywords_top_info_objs:
                    obj = models.KeywordsTopInfo.objects.create(
                        # initial_num=browse_times_text,
                        page_type=page_type,
                        keyword_id=keyword_id,
                        title=title,
                        url=url,
                        rank=rank,
                        is_caina=is_caina,
                        huifu_num=huifu_num,
                        update_date=datetime.datetime.now()
                    )
                    keywords_top_set_obj = models.KeywordsTopSet.objects.get(id=keyword_id)
                    cover_num = models.KeywordsTopInfo.objects.filter(keyword=keywords_top_set_obj).count()
                    keywords_top_set_obj.top_page_cover = cover_num
                    keywords_top_set_obj.status = 2
                    keywords_top_set_obj.save()

                # else:
                #     keywords_top_info_objs.update(update_date=datetime.datetime.now(),current_number=browse_times_text)

            response.status = True
            response.data = None  # data 为空,表示不是我们的数据

    else:
        response.status = False
        response.message = "请求异常"

    return JsonResponse(response.__dict__)


# 添加养账号问答题
@csrf_exempt
def add_zhidaohuida(request):
    response = pub.BaseResponse()

    title = request.POST.get("title")
    url = request.POST.get("url").split('?')[0]

    obj = models.ZhidaoWenda.objects.filter(
        url=url
    )

    if not obj:
        models.ZhidaoWenda.objects.create(
            title=title,
            url=url
        )

    response.status = True
    response.message = "添加成功"

    return JsonResponse(response.__dict__)


def tiaozhuan(request):
    uid = request.GET.get('id')
    user_objs = models.UserProfile.objects.filter(id=uid)
    if user_objs:
        user_obj = user_objs[0]
        if user_obj.shangwutong_url:
            return HttpResponsePermanentRedirect(user_obj.shangwutong_url)

    return redirect('/')


def current_oper_task(request):
    response = pub.BaseResponse()

    # 先判断是否有覆盖查询的任务
    select_keyword_cover_flag = False
    if not select_keyword_cover_flag:
        print('-----------------------=============1111111111111111=============----------------------')
        now_date = datetime.datetime.now().strftime("%Y-%m-%d")
        user_data = models.WendaRobotTask.objects.filter(
            wenda_type=2,
            status__gte=6
        ).values("task__release_user_id").annotate(Count("id"))
        user_list_id = [i["task__release_user_id"] for i in user_data]
        q = Q(
                Q(client_user_id__in=user_list_id) &
                Q(client_user__status=1) &
                Q(is_delete=False) & 
                Q(Q(update_select_cover_date__isnull=True) | Q(update_select_cover_date__lt=now_date))
        )
        keywords_objs = models.KeywordsTopSet.objects.select_related('client_user').filter(q).order_by('client_user')[
                        0:10]

        # 如果查询覆盖的词查完了，判断下是否有知道合伙人的任务
        if not keywords_objs:
            print('-----------------------=============22222222222222222222=============----------------------')
            keywords_objs = models.KeywordsTopSet.objects.select_related('client_user').filter(
                client_user__status=1,
                is_delete=False,
                client_user__role_id=15
            ).filter(Q(Q(update_select_cover_date__isnull=True) | Q(update_select_cover_date__lt=now_date)))


        # 如果查询覆盖的词查完,则查询指定关键词中未查询的词
        if not keywords_objs:
            print('-----------------------=============33333333333333333333333333333=============----------------------')
            q = Q(
                    Q(status=1) &
                    Q(is_delete=False) &
                    Q(client_user__status=1) &
                    # Q(client_user__role_id=5) &
                    Q(Q(update_select_cover_date__isnull=True) | Q(update_select_cover_date__lt=now_date))
            )
            keywords_objs = models.KeywordsTopSet.objects.select_related('client_user').filter(q).order_by(
                'client_user')[0:10]

        if keywords_objs:
            print('----------============5555555555555555555==============---->')
            select_keyword_cover_flag = True
            response.status = True
            response.data = {
                "task_id": 1
            }

    if not select_keyword_cover_flag:
        print('-----------------------=============444444444444444444444444444=============----------------------')
        wenda_robot_task_objs = models.WendaRobotTask.objects.filter(
            next_date__lt=datetime.datetime.now(),
        )
        if wenda_robot_task_objs.count() > 100:
            response.status = True
            response.data = {
                "task_id": 2
            }

    return JsonResponse(response.__dict__)


# 获取渠道操作商务通是否存活
@csrf_exempt
def qudao_shangwutong_cunhuo(request):
    response = pub.BaseResponse()
    if request.method == "POST":
        tid = request.POST.get('tid')
        status = request.POST.get('status')
        if status == '1':  # 1 表示存在, 0表示不存在
            t_status = 21
        else:
            t_status = 22

        models.EditPublickTaskManagement.objects.filter(id=tid).update(status=t_status,
                                                                       update_date=datetime.datetime.now())
    else:
        dtime = datetime.datetime.now() - datetime.timedelta(days=1)
        q = Q(Q(update_date__isnull=True) | Q(update_date__lt=dtime))
        edit_publick_task_management_objs = models.EditPublickTaskManagement.objects.filter(
            task__edit_user__role_id=14,
        ).filter(q).exclude(status=22)
        if edit_publick_task_management_objs:
            edit_publick_task_management_obj = edit_publick_task_management_objs[0]
            response.status = True
            response.data = {
                'tid': edit_publick_task_management_obj.id,
                'url': edit_publick_task_management_obj.url,
                'content': edit_publick_task_management_obj.content
            }
        else:
            response.status = True
            response.data = None

    return JsonResponse(response.__dict__)


# 查询用户到期信息微信推送
@csrf_exempt
def jifeidaoqitixing(request, oper_type, o_id):

    print('进入---------------> ')
    response = pub.BaseResponse()
    now_date = datetime.datetime.today().strftime('%Y-%m-%d')
    seventime = datetime.date.today() + datetime.timedelta(days=7)
    q = Q()
    q.add(Q(guwen__isnull=False) | Q(xiaoshou__isnull=False), Q.AND)
    q.add(Q(jifei_stop_date__lte=seventime) & Q(is_delete=False) & Q(status=1) & Q(jifei_start_date__isnull=False) & Q(
        jifei_stop_date__isnull=False) & Q(jifei_stop_date__gte=now_date), Q.AND)

    if request.GET.get('canshu'):
        print('进入 canshu 判断=-==========')
        # 判断出所有符合条件用户
        objs = models.UserProfile.objects.filter(q)
        data_temp = {}
        data_list_weixin = []
        if objs:
            data_list = []
            for obj in objs:
                # print('--整7天到期用户-------> ',obj.username,obj.jifei_stop_date)
                if obj.jifei_stop_date == seventime:
                    daoqi_days = obj.jifei_stop_date - datetime.date.today()
                    data_list.append({
                        'this_id': obj.id,
                        'username': obj.username,
                        'stop_time': obj.jifei_stop_date,
                        'guwen_openid': obj.guwen.openid,
                        'xiaoshou_openid': obj.xiaoshou.openid,
                        'daoqi_today': daoqi_days.days,
                        'xiaoshou_id': obj.xiaoshou_id,
                        'guwen_id': obj.guwen_id
                    })

                # print('今天到期--------> ',obj.username,obj.jifei_stop_date)
                elif obj.jifei_stop_date == datetime.date.today():
                    daoqi_days = obj.jifei_stop_date - datetime.date.today()
                    data_list.append({
                        'this_id': obj.id,
                        'username': obj.username,
                        'stop_time': obj.jifei_stop_date,
                        'guwen_openid': obj.guwen.openid,
                        'xiaoshou_openid': obj.xiaoshou.openid,
                        'daoqi_today': daoqi_days.days,
                        'xiaoshou_id': obj.xiaoshou_id,
                        'guwen_id': obj.guwen_id
                    })

                # print('到期时间-====》 ',obj.username,obj.jifei_stop_date,daoqi_days.days)
                else:
                    daoqi_days = obj.jifei_stop_date - datetime.date.today()
                    data_list.append({
                        'this_id': obj.id,
                        'username': obj.username,
                        'stop_time': obj.jifei_stop_date,
                        'guwen_openid': obj.guwen.openid,
                        'xiaoshou_openid': obj.xiaoshou.openid,
                        'daoqi_today': daoqi_days.days,
                        'xiaoshou_id': obj.xiaoshou_id,
                        'guwen_id': obj.guwen_id
                    })

            if data_list:
                for obj in data_list:
                    if obj['xiaoshou_openid']:
                    # if obj['xiaoshou_id']:
                        xiaoshou_id = obj['xiaoshou_id']
                        stop_time = obj['stop_time']
                        data_temp[xiaoshou_id] = {
                            'this_id': obj['this_id'],
                            'xiaoshou_openid': obj['xiaoshou_openid'],
                            'username': obj['username'],
                            'stop_time': stop_time.strftime('%Y-%m-%d'),
                            'daoqi_today':obj['daoqi_today']
                        }

                    if obj['guwen_openid']:
                    # if obj['guwen_id']:
                        guwen_id = obj['guwen_id']
                        this_id = obj['this_id']
                        stop_time = obj['stop_time']
                        data_temp[guwen_id] = {
                            'this_id': obj['this_id'],
                            'guwen_openid': obj['guwen_openid'],
                            'username': obj['username'],
                            'stop_time': stop_time.strftime('%Y-%m-%d'),
                            'daoqi_today': obj['daoqi_today']
                        }
                for p_id, data in data_temp.items():
                    data_list_weixin.append(data)

        response.data = data_list_weixin
        return JsonResponse(response.__dict__)

    else:
        print('else =============')
        objs = models.UserProfile.objects.filter(
            is_delete=False,
            id=o_id
        )
        api_data_list = []
        if objs:
            daoqi_days = objs[0].jifei_stop_date - datetime.date.today()
            for obj in objs:
                if daoqi_days == 0:
                    api_data_list.append({
                        'username': obj.username,
                        'text': '今天到期'})
                else:
                    api_data_list.append({
                        'username': obj.username,
                        'text': '{}天到期'.format(daoqi_days.days)})
    print('api_data_list= =========> ',api_data_list)
    if oper_type == 'json':
        response.code = 200
        response.data = api_data_list
        return JsonResponse(response.__dict__)
    else:
        return render(request, 'api/chaxun_kehu_daoqishijian.html', locals())


# 查询每日覆盖量微信推送
@csrf_exempt
def fugailiangtixing(request, oper_type, o_id):
    print('进入--->',o_id)
    now_date = datetime.datetime.now()
    response = pub.BaseResponse()
    q = Q()
    q.add(Q(client_user__is_delete=False) & Q(client_user__status=1) , Q.AND)
    q.add(Q(client_user__xiaoshou__isnull=False) | Q(client_user__guwen__isnull=False), Q.AND)
    q.add(Q(client_user_id=o_id), Q.AND)
    objs = models.UserprofileKeywordsCover.objects.select_related('client_user').filter(q).values(
        'create_date',
        'cover_num',
        'client_user__username',
    ).annotate(Count('id'))
    data_list = []
    for obj in objs:
        print('objs - - - - ',obj )
        client_name = obj['client_user__username']
        cover_num = obj['cover_num']
        create_date = obj['create_date'].strftime('%Y-%m-%d')
        data_list.append({
            'name': client_name,
            'count': cover_num,
            'create_date':create_date
        })
        print("data_list[0]['name'] --  >",data_list[0]['name'])
    objs.filter(create_date=now_date)
    now_name = objs[0]['client_user__username']
    now_count = objs[0]['cover_num']
    print('now_count,now_date -- - >',now_count,now_date)
    if oper_type == 'json':
        response.code = 200
        response.data = data_list
        return JsonResponse(response.__dict__)
    else:
        return render(request, 'api/chaxun_kehu_fugai.html', locals())


# 新问答完成的不打回到编辑
def xinwenda_wancheng_budahui(request):
    print('进入 ====================== 进入')
    objs = models.EditPublickTaskManagement.objects.filter(status=2).exclude(run_task__wenda_type=2)
    for obj in objs:
        print('obj ----- > ',obj.run_task.task.name )
        obj_statu = obj.run_task.task.status
        if obj_statu > 6 :
            obj.status = 3
            obj.run_task.status = 6
            obj.save()
    return HttpResponse('======')



# 关键词提取 每次取出一个 时间最小的
@csrf_exempt
def fifty_guanjianci_fabu(request):
    response = pub.BaseResponse()
    now_time = datetime.datetime.today()
    if request.method == "POST":
        keyword = request.POST.get('keyword')
        guanjianci_num = request.POST.get('guanjianci_num')
        guanjianci_id = request.POST.get('guanjianci_id')
        # print('关键词 - - -- - - -- > ',keyword)
        jieping_1 = request.POST.get('jieping_1')
        jieping_1 = base64.b64decode(jieping_1)
        open('statics/picture/' + keyword + '--1--' + '{guanjianci_num}.png'.format(guanjianci_num=guanjianci_num),'wb').write(jieping_1)
        jieping_2 = request.POST.get('jieping_2')
        jieping_2 = base64.b64decode(jieping_2)
        open('statics/picture/' + keyword + '--2--' + '{guanjianci_num}.png'.format(guanjianci_num=guanjianci_num),'wb').write(jieping_2)
        jieping_3 = request.POST.get('jieping_3')
        jieping_3 = base64.b64decode(jieping_3)
        open('statics/picture/' + keyword + '--3--' + '{guanjianci_num}.png'.format(guanjianci_num=guanjianci_num),'wb').write(jieping_3)
        picture_path_one =  '/' + 'statics/picture/' + keyword + '--1--' + '{guanjianci_num}.png'.format(guanjianci_num=guanjianci_num)
        picture_path_two =  '/' + 'statics/picture/' + keyword + '--2--' + '{guanjianci_num}.png'.format(guanjianci_num=guanjianci_num)
        picture_path_three = '/' + 'statics/picture/' + keyword + '--3--' + '{guanjianci_num}.png'.format(guanjianci_num=guanjianci_num)

        # q = Q()
        # q.add(Q(picture_path=picture_path_one) | Q(picture_path=picture_path_two) | Q(picture_path=picture_path_three),Q.AND)
        # objs = models.Fifty_GetKeywordsJiePing.objects.filter(q)
        # if objs:
        #     pass
        # else:
        obj = models.Fifty_GuanJianCi.objects.get(guanjianci=keyword)
        obj.jieping_time = now_time
        obj.save()
        obj.have_not_capture=1
        obj.save()
        # obj.is_pandaun = True
        # obj.save()
        print('--------- 截屏入库 ----- 更改状态 --------- ')
        one_obj = models.Fifty_GetKeywordsJiePing(picture_path=picture_path_one, guanjianci_id=guanjianci_id)
        one_obj.save()
        two_obj = models.Fifty_GetKeywordsJiePing(picture_path=picture_path_two, guanjianci_id=guanjianci_id)
        two_obj.save()
        three_obj = models.Fifty_GetKeywordsJiePing(picture_path=picture_path_three, guanjianci_id=guanjianci_id)
        three_obj.save()

    # 取关键词
    else:
        canshu = request.GET.get('canshu')
        print('进入参数 -=------》 ',canshu)
        # 如果有参数 取 以取过无截屏的数据
        if canshu:
            objs = models.Fifty_GuanJianCi.objects.filter(
                create_time__lte=datetime.date.today(),
                jieping_time__isnull=True,
                have_not_capture=2
            ).order_by('create_time')
            if objs:
                user_id = objs[0].yonghu_user_id
                guanjianci = objs[0].guanjianci
                guanjianci_id = objs[0].id
                response.data = {
                    'guanjianci': guanjianci,
                    'user_id': user_id,
                    'guanjianci_id': guanjianci_id
                }
            response.status=False
        # 如果没参数 取没取过的数据
        else:
            print('进入 ------------ 取数据 GET')
            # 如果 没被截过屏 取出最小创建时间的关键词(优先)
            objs = models.Fifty_GuanJianCi.objects.filter(
                create_time__lte=datetime.date.today(),
                jieping_time__isnull=True,
                is_pandaun=False
            ).order_by('create_time')
            if objs:
                print('没有截屏')
                guanjianci = objs[0].guanjianci
                user_id = objs[0].yonghu_user_id
                guanjianci_id = objs[0].id
                data_obj = models.Fifty_GuanJianCi.objects.get(guanjianci=guanjianci)
                data_obj.is_pandaun=True
                data_obj.save()
                response.data = {
                    'guanjianci': guanjianci,
                    'user_id': user_id,
                    'guanjianci_id': guanjianci_id
                }
            else:
                print('已截屏')
                objs = models.Fifty_GuanJianCi.objects.filter(
                    jieping_time__lt=datetime.date.today(),
                    create_time__isnull=False,
                    is_pandaun=True
                ).order_by('jieping_time')
                if objs:
                    guanjianci = objs[0].guanjianci
                    user_id = objs[0].yonghu_user_id
                    guanjianci_id = objs[0].id
                    response.data = {
                        'guanjianci': guanjianci,
                        'user_id': user_id,
                        'guanjianci_id': guanjianci_id
                    }
                else:
                    response.status = False
    return JsonResponse(response.__dict__)


# 指定关键词-优化-协助调用查询数据库
@csrf_exempt
def keywords_select_models(request):
    print('-------------------------------------------------------------------')
    response = pub.BaseResponse()
    data_objs = models.KeywordsTopInfo.objects.filter(keyword__client_user__is_delete=False).values(
        'keyword__client_user',
        'keyword__client_user__username',
        'keyword__client_user__laowenda_youxian',
        'page_type',
    ).annotate(cover=Count("keyword__client_user")).order_by('-keyword__client_user__laowenda_youxian',
        '-keyword__client_user__create_date')

    user_id_list, user_data = [], {}
    for obj in data_objs:
        client_user_id = int(obj["keyword__client_user"])
        username = obj["keyword__client_user__username"]
        page_type = obj["page_type"]
        cover = obj["cover"]

        if client_user_id in user_id_list:
            user_data[client_user_id][page_type] = cover
        else:
            user_id_list.append(client_user_id)
            user_data[client_user_id] = {
                page_type: cover,
                "username": username,
                "user_id": client_user_id
            }
    for index, user_id in enumerate(user_id_list):
        client_user_id = user_data[user_id]["user_id"]
        username = user_data[user_id]["username"]
        pc_cover = 0
        wap_cover = 0
        if 1 in user_data[user_id]:
            pc_cover = user_data[user_id][1]
        if 3 in user_data[user_id]:
            wap_cover = user_data[user_id][3]
        total_cover = pc_cover + wap_cover

        keywords_top_set_objs = models.KeywordsTopSet.objects.select_related('client_user').filter(
        client_user_id=client_user_id, is_delete=False)
        keywords_num = keywords_top_set_objs.count()
        no_select_keywords_num = keywords_top_set_objs.filter(status=1).count()
        keywords_top_set_obj = keywords_top_set_objs[0]
        keywords_top_page_cover_excel_path = keywords_top_set_obj.client_user.keywords_top_page_cover_excel_path
        keywords_top_page_cover_yingxiao_excel_path = keywords_top_set_obj.client_user.keywords_top_page_cover_yingxiao_excel_path
        if no_select_keywords_num > 0:
            keywords_status = '1'
        else:
            keywords_status = '2'
        data_temp = {
            'username_id': client_user_id,
            'koywords_status': keywords_status,
            'keywords_num': keywords_num,
            'total_cover': total_cover,
            'pc_cover': pc_cover,
            'wap_cover': wap_cover,
            'no_select_keywords_num': no_select_keywords_num,
            'keywords_top_page_cover_excel_path': keywords_top_page_cover_excel_path,
            'keywords_top_page_cover_yingxiao_excel_path': keywords_top_page_cover_yingxiao_excel_path
        }

        user_obj = models.UserProfile.objects.filter(id=client_user_id)
        response.data = {
            'user_obj':user_obj[0].id
        }
        print('response.data --------------- > ',response.data)
        youhua_objs = models.KeyWords_YouHua.objects.filter(username_id=client_user_id)
        if youhua_objs:
            youhua_objs.update(**data_temp)
            response.status = True
            response.message = '完成缓存'
        else:
            youhua_objs.create(**data_temp)
            response.status = True
            response.message = '完成缓存'

    return JsonResponse(response.__dict__)

# 查询关键词覆盖(覆盖模式)优化 -- 供task查询数据库
@csrf_exempt
def keywords_cover_select_models(request):
    rc = redis.StrictRedis(host=redis_host, port=6379,db=8, decode_responses=True)
    if rc.llen('data') > 10000:
        return HttpResponse('数据已经大于一万条，不缓存数据了')

    now_date = datetime.datetime.now().strftime("%Y-%m-%d")
    # 判断含有老问答的客户优先查覆盖
    user_data = models.WendaRobotTask.objects.filter(
        wenda_type=2,
        status__gte=6
    ).values("task__release_user_id").annotate(Count("id"))
    user_list_id = [i["task__release_user_id"] for i in user_data]

    get_select_date = datetime.datetime.now() - datetime.timedelta(minutes=5)
    q = Q(
        Q(client_user_id__in=user_list_id) &
        Q(is_delete=False) &
        Q(client_user__status=1) &
        Q(Q(get_select_date__isnull=True) | Q(get_select_date__lt=get_select_date)) &
        Q(Q(update_select_cover_date__isnull=True) | Q(update_select_cover_date__lt=now_date))
    )

    # 先查询启用用户的关键词覆盖
    keywords_objs = models.KeywordsTopSet.objects.select_related('client_user').filter(q).filter(
        client_user__status=1
    ).order_by(
        '?'
    )[0:500]

    if not keywords_objs:   # 如果启用的查询完了，则查询知道合伙人的关键词
        keywords_objs = models.KeywordsTopSet.objects.select_related('client_user', 'client_user__role').filter(
            Q(is_delete=False) &
            Q(client_user__status=1) &
            Q(client_user__role_id=15) &
            Q(Q(get_select_date__isnull=True) | Q(get_select_date__lt=get_select_date)) &
            Q(Q(update_select_cover_date__isnull=True) | Q(update_select_cover_date__lt=now_date))
        ).order_by('?')[0:500]

    if not keywords_objs:  # 如果启用的查询完了，则查询未启用的用户的关键词覆盖
        keywords_objs = models.KeywordsTopSet.objects.select_related('client_user').filter(q).order_by(
            '?'
        )[0:500]

    # 如果查询覆盖的词查完,则查询指定关键词中未查询的词
    if not keywords_objs:
        q = Q(Q(status=1) & Q(is_delete=False) & Q(
            Q(update_select_cover_date__isnull=True) | Q(update_select_cover_date__lt=now_date)))
        keywords_objs = models.KeywordsTopSet.objects.select_related('client_user').filter(q).order_by(
            '?')[0:500]

    print('keywords_objs -->', keywords_objs)
    if keywords_objs:
        for keywords_obj in keywords_objs:
            keyword = keywords_obj.keyword
            client_user_id = keywords_obj.client_user_id
            keyword_id = keywords_obj.id
            area = keywords_obj.area
            map_match_keywords = keywords_obj.client_user.map_match_keywords
            redis_data_list = {
                'keyword': keyword,
                'client_user_id': client_user_id,
                'keyword_id': keyword_id,
                'area': area,
                'map_match_keywords': map_match_keywords
            }
            rc.lpush('data', json.dumps(redis_data_list))
            keywords_obj.get_select_date = datetime.datetime.now()
            keywords_obj.save()

    return HttpResponse('缓存数据到redis中')
