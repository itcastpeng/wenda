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
from django.db.models import Count
import datetime
import os ,time
from webadmin.modules import RedisOper

from wenda_celery_project import tasks


# 生成表格中显示的数据
def init_data(role_id=None, q=Q(), start=0, length=-1):
    print("3--> ", datetime.datetime.now())
    objs = models.KeyWords_YouHua.objects.filter(q).filter(username__is_delete=False)
    print('objs ========== >',objs)
    if objs:
        obj_count = objs.count()
        # print('obj_count ----------》',obj_count)
        result_data = {
            "recordsFiltered": obj_count,
            "recordsTotal": obj_count,
            "data": []
        }
        if objs:
            for index, obj in enumerate(objs[start: (start + (length - 1))], start=1):
                client_user_id = obj.username.id
                username = str(obj.username)
                pc_cover = obj.pc_cover
                wap_cover = obj.wap_cover
                total_cover = pc_cover + wap_cover
                keywords_num = obj.keywords_num
                keywords_status = obj.get_koywords_status_display()
                no_select_keywords_num = obj.no_select_keywords_num
                keywords_top_page_cover_excel_path = obj.keywords_top_page_cover_excel_path
                keywords_top_page_cover_yingxiao_excel_path = obj.keywords_top_page_cover_yingxiao_excel_path

                # keywords_top_set_objs = models.KeywordsTopSet.objects.select_related('client_user').filter(
                #     client_user_id=client_user_id, is_delete=False)
                # keywords_top_set_obj = keywords_top_set_objs[0]

                keywords_num_str = "{keywords_num} / {no_select_keywords_num}".format(
                    keywords_num=keywords_num,
                    no_select_keywords_num=no_select_keywords_num
                )

                baobiao_download = """<a class="shengchengbaobiao" uid="{client_user_id}" href="#">生成报表</a>""".format(
                    client_user_id=client_user_id)
                if keywords_top_page_cover_excel_path:
                    baobiao_download += """
                    /
                    <a download="/{keywords_top_page_cover_excel_path}" href="/{keywords_top_page_cover_excel_path}">普通</a>
                    /
                    <a download="/{keywords_top_page_cover_yingxiao_excel_path}" href="/{keywords_top_page_cover_yingxiao_excel_path}">营销</a>
                    """.format(
                        keywords_top_page_cover_excel_path=keywords_top_page_cover_excel_path,
                        keywords_top_page_cover_yingxiao_excel_path=keywords_top_page_cover_yingxiao_excel_path,
                    )

                oper = """
                    <a class="download_keyword" uid="{client_user_id}" href="#">关键词下载</a>
                    /
                    <a class="chongcha" uid="{client_user_id}" href="#">重查</a>
                    /
                    <a class="shanchuhuifuyichang" uid="{client_user_id}" href="#">删除回复异常</a>
                    
                """.format(client_user_id=client_user_id)

                if role_id and ("测试" in username or role_id == 1):
                    oper += """
                        / <a class="clearKeywords" uid="{client_user_id}" href="#">清空关键词</a>
                    """.format(client_user_id=client_user_id)

                # 如果该用户老问答没有优先,则显示优先处理的功能
                if not obj.username.laowenda_youxian:
                    oper += """
                        / <a class="laowendaYouxian" uid="{client_user_id}" href="#">老问答优先处理</a>
                    """.format(client_user_id=client_user_id)
                else:
                    username = '<span style="color: red">{username} (老问答优先)</span>'.format(username=username)

                    oper += """
                        / <a class="laowendaYouxianQuxiao" uid="{client_user_id}" href="#">取消优先处理</a>
                    """.format(client_user_id=client_user_id)
                result_data["data"].append(
                    [
                        index, username, keywords_status, keywords_num_str,
                        total_cover, pc_cover, wap_cover, baobiao_download, oper, client_user_id
                    ]
                )
    else:
        result_data = {

        }
    return result_data


# 指定首页关键词
@pub.is_login
def keywords_top_set(request):
    role_id = request.session.get("role_id")
    user_id = request.session.get("user_id")

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))
        client_user_id = request.GET.get('client_user_id')
        print('client_user_id ---------- > ',client_user_id)
        # 排序
        column_list = [
             "client_user_id","client_user_type"
            # "id","keyword", "top_page_cover",
            # "create_date", "oper_user_id", "oper",
        ]
        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column

        print("1--> ", datetime.datetime.now())
        q = Q()
        for index, field in enumerate(column_list):
            if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                if field == "client_user_type":
                    if request.GET.get(field) == "1":  # 正式用户
                        q.add(~Q(**{"username__username" + "__contains": "测试"}), Q.AND)
                    elif request.GET.get(field) == "2":  # 测试 用户
                        q.add(Q(**{"username__username" + "__contains": "测试"}), Q.AND)
                elif field == "client_user_id":
                    q.add(Q(**{"username_id": request.GET[field]}), Q.AND)
                else:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)
                # q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        if not request.GET.get("client_user_type"):
            q.add(~Q(**{"username__username" + "__contains": "测试"}), Q.AND)

        # print(q, q.children, len(q.children))
        # if len(q.children):
        #     result_data = init_data(role_id, q, start, length)
        # else:
        #     print("走 redis 缓存")
        #     # result_data = init_data(role_id)
        #     # RedisOper.write_to_cache("keywords_top_set-init-data", result_data)
        #
        #     result_data = RedisOper.read_from_cache("keywords_top_set-init-data")
        #     if not result_data:
        #         result_data = init_data(role_id)
        #         RedisOper.write_to_cache("keywords_top_set-init-data", result_data)
        #
        #     print(request.GET.get("client_user_type"))
        #     data = []
        #     index = 1
        #     for i in result_data["data"]:
        #         i[0] = index
        #         client_user_id = i.pop()
        #
        #         if "测试" in i[1] or role_id == 1:
        #             i[-2] += """
        #                 / <a class="clearKeywords" uid="{client_user_id}" href="#">清空关键词</a>
        #             """.format(client_user_id=client_user_id)
        #
        #         if request.GET.get("client_user_type") == "2":
        #             if "测试" in i[1]:
        #                 data.append(i)
        #                 index += 1
        #         else:
        #             if "测试" not in i[1]:
        #                 data.append(i)
        #                 index += 1
        #
        #     result_data["data"] = data[start: start + length]
        #     result_data["recordsFiltered"] = len(data)
        #     result_data["recordsTotal"] = len(data)

        result_data = init_data(role_id, q, start, length)
        # print('result_data---=-=-=-=-=-=-==-=-=-=-=-=-=-=-=> ',result_data)
        print("4--> ", datetime.datetime.now())
        return HttpResponse(json.dumps(result_data))

    status_choices = models.UserProfile.status_choices
    client_data = models.KeywordsTopInfo.objects.filter(keyword__client_user__is_delete=False).values(
        'keyword__client_user',
        'keyword__client_user__username',
    ).annotate(cover=Count("keyword__client_user"))
    # client_data = models.KeywordsTopSet.objects.values('client_user__username', 'client_user_id').annotate(Count("keyword")).filter(is_delete=False)

    if "_pjax" in request.GET:
        return render(request, 'wenda/keywords_top_set/keywords_top_set_pjax.html', locals())
    return render(request, 'wenda/keywords_top_set/keywords_top_set.html', locals())


@pub.is_login
def keywords_top_set_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    role_id = request.session.get("role_id")
    response = pub.BaseResponse()
    if request.method == "POST":
        # 添加
        if oper_type == "create":
            keyword = request.POST.get("keyword")
            client_user_id = request.POST.get("client_user_id", None)
            keywords_type = request.POST.get('keywords_type')

            print(client_user_id)

            if client_user_id == "":
                response.status = False
                response.message = "请选择用户"
            elif client_user_id is None:
                client_user_id = user_id

            if response.status and not keyword:
                response.status = False
                response.message = "请输入需要添加的关键词"

            if response.status:
                keyword_list = set(keyword.splitlines())
                print('keyword_list - - -> ',keyword_list)

                query = []
                repeat_num = 0
                for i in keyword_list:
                    if not i:  # 如果为空 则跳过
                        continue
                    objs = models.KeywordsTopSet.objects.filter(
                        client_user_id=client_user_id,
                        keyword=i,
                        is_delete=False
                    )
                    if not objs:
                        query.append(models.KeywordsTopSet(
                            keyword=i,
                            client_user_id=client_user_id,
                            oper_user_id=user_id,
                            keywords_type=keywords_type
                        ))
                    else:
                        obj = objs[0]
                        obj.keywords_type = keywords_type
                        obj.save()
                        repeat_num += 1

                models.KeywordsTopSet.objects.bulk_create(query)

                response.status = True
                response.message = "成功添加 {num} 个关键词".format(num=len(query))

        # 删除
        elif oper_type == "delete":
            obj = models.KeywordsTopSet.objects.get(id=o_id)
            obj.is_delete = True
            obj.save()

            response.status = True
            response.message = "删除成功"

        # 客户重查
        elif oper_type == "chongcha":
            models.KeywordsTopInfo.objects.filter(keyword__client_user_id=o_id).delete()
            models.KeywordsTopSet.objects.filter(client_user_id=o_id).update(status=1)
            user_obj = models.UserProfile.objects.get(id=o_id)
            user_obj.keywords_top_page_cover_excel_path = None
            user_obj.keywords_top_page_cover_yingxiao_excel_path = None
            user_obj.save()

            response.status = True
            response.message = "开始重查"

        # 删除回复异常任务
        elif oper_type == 'shanchuhuifuyichang':
            objs = models.WendaRobotTask.objects.select_related('task__release_user').filter(
                task__release_user_id=o_id,
                status=20,
                task__is_delete=False,
                wenda_type=2
            ).delete()

        # 清空关键词
        elif oper_type == "clearKeywords":
            print('o_id ========>',o_id)
            models.KeywordsTopSet.objects.filter(client_user_id=o_id).delete()
            obj = models.KeyWords_YouHua.objects.get(username_id=o_id)
            obj.keywords_num = 0
            obj.no_select_keywords_num = 0
            obj.save()
            response.status = True
            response.message = "关键词清空成功"

        # 老问答优先处理
        elif oper_type == "laowendaYouxian":
            # models.UserProfile.objects.all().update(laowenda_youxian=False)
            models.UserProfile.objects.filter(id=o_id).update(laowenda_youxian=True)

            response.status = True
            response.message = "设置成功"

        # 清除所有客户发布老问答优先
        elif oper_type == "clearLaowendaYouxian":
            models.UserProfile.objects.all().update(laowenda_youxian=False)
            response.status = True
            response.message = "清除所有客户发布老问答优先"

        elif oper_type == "laowendaYouxianQuxiao":
            models.UserProfile.objects.filter(id=o_id).update(laowenda_youxian=False)
            response.status = True
            response.message = "取消成功"

        elif oper_type == "shengchengbaobiao":
            print('o_id -->', o_id)
            tasks.keywords_top_page_cover_excel.delay(o_id)
            response.status = True
            response.message = "报表生成中,请稍后查看"

        # 下载关键词
        elif oper_type == 'download_keyword':
            if o_id:
                print('o_id - - -- > 下载',o_id)
                objs = models.KeywordsTopSet.objects.filter(
                    client_user_id=o_id,
                    is_delete=False,
                )
                data_list = []
                file_name = ''
                for obj in objs:
                    file_name = os.path.join("statics" +'/'+ "task_excel" +'/'+ "keywords_top_set"+'/'+ obj.client_user.username + ".xlsx")
                    keyword = obj.keyword
                    keywords_type = obj.get_keywords_type_display()
                    data_list.append({
                        'keyword': keyword,
                        'keywords_type': keywords_type
                    })

                response.status = True
                response.message = "导出成功"
                response.download_url =  file_name
                print('下载路径----> ',file_name)
                tasks.guanjianci_xiazai.delay(file_name, data_list)
        # RedisOper.write_to_cache("keywords_top_set-init-data", None)
        return JsonResponse(response.__dict__)

    else:
        # 添加
        if oper_type == "create":
            client_objs = models.UserProfile.objects.filter(is_delete=False, role_id=5)
            keywords_type_choices = models.KeywordsTopSet.keywords_type_choices
            return render(request, 'wenda/keywords_top_set/keywords_top_set_modal_create.html', locals())

        # 删除
        elif oper_type == "delete":
            obj = models.KeywordsTopSet.objects.get(id=o_id)
            return render(request, 'wenda/keywords_top_set/keywords_top_set_modal_delete.html', locals())

        # 客户首页覆盖
        elif oper_type == "client_cover":
            objs = models.KeywordsTopInfo.objects.filter(keyword__client_user__is_delete=False).values(
                'keyword__client_user',
                'keyword__client_user__username',
                'page_type'
            ).annotate(cover=Count("keyword__client_user"))
            # ).annotate(cover=Count("keyword__client_user")).all().order_by('create_date')
            # print(objs)

            data = {}
            for obj in objs:
                client_user_id = obj["keyword__client_user"]
                username = obj["keyword__client_user__username"]
                page_type = obj["page_type"]
                cover = obj["cover"]
                print(page_type, cover)
                # print(data)
                if client_user_id in data:
                    data[client_user_id][page_type] = cover
                    if page_type == 1:
                        data[client_user_id]["total"] = cover + data[client_user_id][3]
                    else:
                        data[client_user_id]["total"] = cover + data[client_user_id][1]
                else:
                    # 查询该用户添加了多少关键词数量
                    keywords_top_set_objs = models.KeywordsTopSet.objects.filter(client_user_id=client_user_id,
                        is_delete=False)
                    keywords_num = keywords_top_set_objs.count()
                    no_select_keywords_num = keywords_top_set_objs.filter(status=1).count()

                    if no_select_keywords_num > 0:
                        keywords_status = "查询中"
                    else:
                        keywords_status = "已查询"

                    keywords_top_page_cover_excel_path = keywords_top_set_objs[
                        0].client_user.keywords_top_page_cover_excel_path
                    keywords_top_page_cover_yingxiao_excel_path = keywords_top_set_objs[
                        0].client_user.keywords_top_page_cover_yingxiao_excel_path

                    pc_cover = 0
                    wap_cover = 0
                    if page_type == 1:  # PC 端
                        pc_cover += cover
                    else:
                        wap_cover += cover

                    data[client_user_id] = {
                        # 1: pc_cover,
                        # 3: wap_cover,
                        page_type: cover,
                        "username": username,
                        "keywords_num": "{keywords_num} / {no_select_keywords_num}".format(keywords_num=keywords_num,
                            no_select_keywords_num=no_select_keywords_num),
                        "keywords_status": keywords_status,
                        "keywords_top_page_cover_excel_path": keywords_top_page_cover_excel_path,
                        "keywords_top_page_cover_yingxiao_excel_path": keywords_top_page_cover_yingxiao_excel_path
                    }

            return render(request, 'wenda/keywords_top_set/keywords_top_set_modal_client_cover.html', locals())

        # 清除所有客户发布老问答优先
        elif oper_type == "clearLaowendaYouxian":
            print('请求到 GET -=---------------')
            return render(request,'wenda/keywords_top_set/keyword_top_set_modal_clearLaowendaYouxian.html',locals())
