#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com
from django.shortcuts import render, HttpResponse, redirect, reverse
from webadmin.views_dir import pub
from webadmin import models
from django.http import JsonResponse
from django.db import connection
from webadmin.forms import user
import json
from webadmin.forms.form_cover_update_jifei import jifeiupdateForm
from django.db.models import F
from django.db.models import Q
from webadmin.views_dir.wenda.message import AddMessage
from django.db.models import Count
import os
import time
from wenda_celery_project import tasks
import datetime


# 覆盖报表
@pub.is_login
def cover_reports(request):
    role_id = request.session.get("role_id")
    user_id = request.session.get("user_id")

    # print("role_id -->", role_id)
    # print("user_id -->", user_id)
    filter_dict = {}
    if role_id == 5:  # 客户角色只能看到自己的
        filter_dict["client_user"] = user_id
    # elif role_id == 12:  # 销售角色只能看到自己客户的
    #     filter_dict["keywords__client_user__xiaoshou_id"] = user_id

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        # print("1 -->", datetime.datetime.now())
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        """
        index, obj.keywords.client_user.username, keyword, obj.get_page_type_display(),
                    obj.rank, create_date, oper
        """
        # column_list = ["", "index", "id", "keywords__client_user", "keyword", "page_type", "rank", "create_date", "oper", "keywords__client_user_id"]
        column_list = [
            "index", "id", "client_user", "client_user__xiaoshou", "keywords_num", "keyword_no_select_count",
            "today_cover_num", "total_cover_num", "total_publish_num",'client_user__jifei_start_date' ,'client_user__jifei_stop_date',
            "oper", "client_user_id","client_user__xiaoshou_id", 'client_user__status',

        ]
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

        if 'client_user__status' not in request.GET:
            q.add(Q(**{'client_user__status': 1}), Q.AND)

        # print('q -->', q)

        # data_objs = models.KeywordsCover.objects.select_related(
        #     "keywords__client_user",
        #     "keywords"
        # ).filter(**filter_dict).filter(q).order_by(order_column)

        # print("2 -->", datetime.datetime.now())

        print(order_column)
        # 如果是销售角色，不是刘婷的账号，则将成都美尔贝隐藏起来
        data_objs = models.ClientCoveringData.objects.select_related(
            "client_user",
            "client_user__xiaoshou"
        ).filter(client_user__is_delete=False).filter(**filter_dict).filter(q).order_by(order_column)
        if role_id == 12:
            data_objs = data_objs.exclude(client_user__username__contains='YZ-')
            if user_id != 37:
                data_objs = data_objs.exclude(client_user_id=175)

        result_data = {
            "recordsFiltered": data_objs.count(),
            "recordsTotal": data_objs.count(),
            "data": [],
        }

        status_choices = models.UserProfile.status_choices

        # print("3 -->", datetime.datetime.now())
        for index, obj in enumerate(data_objs[start: (start + length)], start=1):

            # keywords_topset_obj = models.KeywordsTopSet.objects.filter(
            #     client_user_id=obj["keywords__client_user_id"],
            #     is_delete=False
            # )
            # keyword_count = keywords_topset_obj.count()   # 关键词总数
            #
            # now_date = datetime.datetime.now().strftime("%Y-%m-%d")
            #
            # # 当日覆盖数
            # today_cover = models.KeywordsCover.objects.filter(
            #     keywords__client_user_id=obj["keywords__client_user_id"],
            #     create_date__gte=now_date
            # ).count()
            #
            # # 总发布次数
            # total_oper_num = models.RobotAccountLog.objects.filter(
            #     wenda_robot_task__task__release_user_id=obj["keywords__client_user_id"],
            #     wenda_robot_task__wenda_type=2
            # ).count()
            #
            # q = Q(Q(update_select_cover_date__isnull=True) | Q(update_select_cover_date__lt=now_date))
            # keyword_select_count = keywords_topset_obj.filter(q).count()    # 未查询的关键词数
            #
            # if keyword_select_count > 0:
            #     keyword_count_str = "%s / %s" % (keyword_count, keyword_select_count)
            #     select_status = "查询中"
            # else:
            #     keyword_count_str = keyword_count
            #     select_status = "查询完成"

            # oper = ""
            # if role_id in [1, 4, 7]:
            #     if obj["keywords__client_user__task_edit_show"]:  # True 表示当前任务为编辑状态, False 为不编辑状态
            #         oper += "<a href='task_edit_show/{client_user_id}/'>不展示编辑内容</a>"
            #     else:
            #         oper += "<a href='task_edit_show/{client_user_id}/'>展示编辑内容</a>"
            #
            #     oper += " / "
            #     if obj["keywords__client_user__send_statement"]:  # True 表示当前任务发送报表, False 为不发送报表
            #         oper += "<a href='send_statement/{client_user_id}/'>暂停发送报表</a>"
            #     else:
            #         oper += "<a href='send_statement/{client_user_id}/'>开启发送报表</a>"
            #
            #     oper += " / <a href='chongcha/{client_user_id}/'>重查覆盖</a>"

            keyword_count = obj.keywords_num
            today_cover = obj.today_cover_num

            if obj.keyword_no_select_count > 0:
                keyword_count_str = "%s / %s" % (keyword_count, obj.keyword_no_select_count)
                select_status = "查询中"
            else:
                keyword_count_str = keyword_count
                select_status = "查询完成"
            total_oper_num = obj.total_publish_num

            oper = ""
            zhanshibianji = ''
            if role_id in [1, 4, 7]:
                if obj.client_user.task_edit_show:  # True 表示当前任务为编辑状态, False 为不编辑状态
                    zhanshibianji += "<a href='task_edit_show/{client_user_id}/'>不展示</a>".format(client_user_id=obj.client_user_id)
                else:
                    zhanshibianji += "<a href='task_edit_show/{client_user_id}/'>展示 </a>".format(client_user_id=obj.client_user_id)

                # oper += " / "
                # if obj.client_user.send_statement:  # True 表示当前任务发送报表, False 为不发送报表
                #     oper += "<a href='send_statement/{client_user_id}/'>暂停发送报表</a>"
                # else:
                #     oper += "<a href='send_statement/{client_user_id}/'>开启发送报表</a>"
                #
                # oper += " / <a href='chongcha/{client_user_id}/'>重查覆盖</a>"
                #
                # oper += " / <a href='shanchulianjie/{client_user_id}/' data-toggle='modal' data-target='#exampleFormModal'>删除不计覆盖链接</a>"
                oper += "<a href='quanbushezhi/{client_user_id}/' data-toggle='modal' data-target='#exampleFormModal'>设置</a>".format(client_user_id=obj.client_user_id)

            # oper = oper.format(client_user_id=obj.client_user_id)
            # zhanshibianji = zhanshibianji.format(client_user_id=obj.client_user_id)
            # xiugaijifeiriqi = " <a href='xiugaijifeiriqi/{client_user_id}/' data-toggle='modal' data-target='#exampleFormModal'>修改计费日期</a>".format(
            #     client_user_id=obj.client_user_id)
            username = obj.client_user.username
            jifei_start_date = ''
            jifei_stop_date = ''

            if role_id in [1,4,6,7]:
                if obj.client_user.jifei_start_date:
                    jifei_start_date = obj.client_user.jifei_start_date.strftime('%Y-%m-%d')
                if obj.client_user.jifei_stop_date:
                    jifei_stop_date = obj.client_user.jifei_stop_date.strftime('%Y-%m-%d')

                    now_date = datetime.datetime.now()


                    if obj.client_user.jifei_stop_date == datetime.date.today():
                        username += "<span style='color: red'> (今天到期)</span>"

                    elif obj.client_user.jifei_stop_date <datetime.date.today():
                        username += "<span style='color: red'> (已到期)</span>"
                    # 如果当前时间 大于等于 计费结束日期减去七天
                    else:
                        if now_date.strftime('%Y-%m-%d') >= (obj.client_user.jifei_stop_date - datetime.timedelta(days=7)).strftime('%Y-%m-%d'):
                            # 用结束日期减去当前日期 剩余天数
                            temp = obj.client_user.jifei_stop_date - datetime.date.today()
                            username += "<span style='color: #ff9900'> (还有{}天到期)</span>".format(temp.days)


            jifeishijian = jifei_start_date + '<br>' + jifei_stop_date
            result_data["data"].append(
                {
                    "index": index,
                    "id": obj.client_user_id,
                    "username": username,
                    "xiaoshou_username": obj.client_user.xiaoshou.username,
                    "cover_total": obj.total_cover_num,
                    "select_status": select_status,
                    "keyword_count": keyword_count_str,
                    "oper": oper,
                    "today_cover": today_cover,
                    "total_oper_num": total_oper_num,
                    'zhanshibianji':zhanshibianji,
                    'xiugaijifeiriqistop': jifeishijian,
                    # "xiugaijifeiriqi": xiugaijifeiriqi,
                    # 'xiugaijifeiriqistart': jifei_start_date,
                }
            )
            # print("4 -->", datetime.datetime.now())
        return HttpResponse(json.dumps(result_data))

    if role_id == 12:
        client_data = models.ClientCoveringData.objects.filter(client_user__is_delete=False).filter(**filter_dict).exclude(
            client_user__username__contains='YZ-'
        ).values(
            'client_user__username',
            'client_user_id'
        ).annotate(Count("id"))
    else:
        client_data = models.ClientCoveringData.objects.filter(client_user__is_delete=False).filter(**filter_dict).values(
            'client_user__username',
            'client_user_id'
        ).annotate(Count("id"))

    xiaoshou_data = models.ClientCoveringData.objects.filter(**filter_dict).values('client_user__xiaoshou__username',
        'client_user__xiaoshou_id').annotate(Count("id"))
    print("client_data -->", client_data)

    status_choices = models.UserProfile.status_choices

    if "_pjax" in request.GET:
        return render(request, 'wenda/cover_reports/cover_reports_pjax.html', locals())
    return render(request, 'wenda/cover_reports/cover_reports.html', locals())


@pub.is_login
def cover_reports_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    role_id = request.session.get("role_id")
    response = pub.BaseResponse()

    if request.method == "POST":
        # 添加
        if oper_type == "create":
            keyword = request.POST.get("keyword")
            client_user_id = request.POST.get("client_user_id", None)
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

                query = []
                repeat_num = 0
                for i in keyword_list:
                    if not i:  # 如果为空 则跳过
                        continue
                    obj = models.KeywordsTopSet.objects.filter(client_user_id=user_id, keyword=i, is_delete=False)
                    if not obj:
                        query.append(models.KeywordsTopSet(
                            keyword=i,
                            client_user_id=client_user_id,
                            oper_user_id=user_id,
                        ))
                    else:
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

        # 覆盖报表所有功能 修改计费 删除链接....
        elif oper_type == 'shezhi_oper':
            data_objs = models.UserProfile.objects.filter(
                id=o_id)
            print('requeat -----> ',request.POST)
            print('data_objs - -- - - -- - > ',data_objs)
            # zhanshibianji = request.POST.get('zhanshibianji')
            fasongbaobiao = request.POST.get('fasongbaobiao')
            chongchafugai = request.POST.get('chongchafugai')
            shanchufugai = request.POST.get('delete_lianjie')
            xiugaijifeiriqistart = request.POST.get('xiugaijifeiriqistart')
            xiugaijifeiriqistop = request.POST.get('xiugaijifeiriqistop')
            # 展示编辑
            # if zhanshibianji == 'on':
            #     print('进入展示编辑   ')
            #     data_objs.update(task_edit_show=True)

                # data_objs[0].save()
                # print('data_objs -- - -- > ',data_objs[0].task_edit_show)
            # else:
            #     print('展示编辑else')
            #     data_objs.update(task_edit_show=False)

            # 发送报表
            if fasongbaobiao == 'on':
                data_objs.update(send_statement=True)

            else:
                data_objs.update(send_statement=False)

            # 重查覆盖
            if chongchafugai == 'on':
                models.KeywordsTopInfo.objects.filter(keyword__client_user_id=o_id).delete()
                models.KeywordsTopSet.objects.filter(client_user_id=o_id).update(status=1)
                user_obj = models.UserProfile.objects.get(id=o_id)
                user_obj.keywords_top_page_cover_excel_path = None
                user_obj.keywords_top_page_cover_yingxiao_excel_path = None
                user_obj.save()

            # 删除链接
            if shanchufugai:
                delete_lianjie = request.POST.get('delete_lianjie')
                print('进入删除 - - -- > ', delete_lianjie)
                delete_lianjie_list = set(delete_lianjie.splitlines())
                print('delete_lianjie_list - - - - - - >', delete_lianjie_list)
                for delete_lianjie in delete_lianjie_list:
                    if not delete_lianjie:
                        continue
                    objs = models.TongjiKeywords.objects.filter(
                        url=delete_lianjie,
                        task__release_user_id=o_id,
                    )
                    print('objs - - -- -- -- - - 》',objs )
                    if objs:
                        objs.delete()


            # 修改计费日期
            if xiugaijifeiriqistart or xiugaijifeiriqistop:
                print(xiugaijifeiriqistart ,xiugaijifeiriqistop)
                forms_obj = jifeiupdateForm(request.POST)
                if forms_obj.is_valid():
                    time_objs = models.UserProfile.objects.filter(id=o_id).update(
                        jifei_start_date=xiugaijifeiriqistart,
                        jifei_stop_date=xiugaijifeiriqistop
                    )
                else:
                    response.status = False
                    response.message = '请填写正确日期'
            response.status = True
            response.message = "操作成功"

        # 下载报表

        if oper_type == "download":
            user_id = request.POST.get("user_id")
            if not user_id:
                response.status = False
                response.message = "请选择导出用户名称"
            else:
                file_name = os.path.join("statics", "upload_files", str(int(time.time() * 1000)) + ".xlsx")

                search_objs = models.KeywordsCover.objects.select_related(
                    'keywords', 'keywords__client_user'
                ).filter(keywords__client_user_id=user_id).order_by("-create_date")

                data_list = []
                for obj in search_objs:
                    data_list.append({
                        "username": obj.keywords.client_user.username,
                        "keywords": obj.keywords.keyword,
                        "page_type": obj.get_page_type_display(),
                        "rank": obj.rank,
                        "create_date": obj.create_date.strftime("%Y-%m-%d"),
                        "link": obj.url
                    })

                tasks.cover_reports_generate_excel.delay(file_name, data_list)
                tasks.userprofile_keywords_cover.delay()

                response.status = True
                response.message = "导出成功"
                response.download_url = "/" + file_name

        return JsonResponse(response.__dict__)

    else:
        # 添加
        if oper_type == "create":
            client_objs = models.UserProfile.objects.filter(is_delete=False, role_id=5)
            return render(request, 'wenda/keywords_top_set/keywords_top_set_modal_create.html', locals())

        # 删除
        elif oper_type == "delete":
            obj = models.KeywordsTopSet.objects.get(id=o_id)
            return render(request, 'wenda/keywords_top_set/keywords_top_set_modal_delete.html', locals())

        # 客户首页覆盖
        elif oper_type == "client_cover":
            objs = models.KeywordsTopInfo.objects.values('keyword__client_user', 'keyword__client_user__username',
                'page_type').annotate(cover=Count("keyword__client_user")).all()

            data = {}
            for obj in objs:
                client_user_id = obj["keyword__client_user"]
                username = obj["keyword__client_user__username"]
                page_type = obj["page_type"]
                cover = obj["cover"]

                if client_user_id in data:
                    data[client_user_id][page_type] = cover
                    if page_type == 1:
                        data[client_user_id]["total"] = cover + data[client_user_id][3]
                    else:
                        data[client_user_id]["total"] = cover + data[client_user_id][1]
                else:
                    # 查询该用户添加了多少关键词数量
                    keywords_top_set_objs = models.KeywordsTopSet.objects.filter(client_user_id=client_user_id)
                    keywords_num = keywords_top_set_objs.count()
                    no_select_keywords_num = keywords_top_set_objs.filter(status=1).count()

                    if keywords_top_set_objs.filter(status=1):
                        keywords_status = "查询中"
                    else:
                        keywords_status = "已查询"

                    keywords_top_page_cover_excel_path = keywords_top_set_objs[
                        0].client_user.keywords_top_page_cover_excel_path
                    keywords_top_page_cover_yingxiao_excel_path = keywords_top_set_objs[
                        0].client_user.keywords_top_page_cover_yingxiao_excel_path

                    data[client_user_id] = {
                        page_type: cover,
                        "username": username,
                        "keywords_num": "{keywords_num} / {no_select_keywords_num}".format(keywords_num=keywords_num,
                            no_select_keywords_num=no_select_keywords_num),
                        "keywords_status": keywords_status,
                        "keywords_top_page_cover_excel_path": keywords_top_page_cover_excel_path,
                        "keywords_top_page_cover_yingxiao_excel_path": keywords_top_page_cover_yingxiao_excel_path
                    }

            return render(request, 'wenda/keywords_top_set/keywords_top_set_modal_client_cover.html', locals())

        # 报表下载
        elif oper_type == "download":
            client_data = models.KeywordsCover.objects.values(
                'keywords__client_user__username',
                'keywords__client_user_id'
            ).annotate(Count("keywords"))
            print(client_data)
            return render(request, "wenda/cover_reports/cover_reports_modal_download.html", locals())

        # 查看客户每日覆盖明细
        elif oper_type == "show_click_info":

            data_objs = models.UserprofileKeywordsCover.objects.filter(
                client_user_id=o_id
            )
            # data_objs = models.KeywordsCover.objects.select_related(
            #     "keywords__client_user",
            #     "keywords"
            # ).filter(keywords__client_user_id=o_id).values("create_date").annotate(count=Count('id'))

            temp_data = {}
            for obj in data_objs:
                date_format = obj.create_date.strftime("%Y-%m-%d")
                temp_data[date_format] = {
                    "cover_num": obj.cover_num,
                    "url_num": obj.url_num,
                    "statement_path": obj.statement_path
                }
            if role_id in [5, 12]:  # 客户角色和销售角色
                result_data = """
                    <table class="table table-bordered text-nowrap padding-left-50 margin-bottom-0" >
                        <tr><td>编号</td><td>日期</td><td>覆盖数</td><td>下载报表</td></tr>
                        {tr_html}
                    </table>
                """
            else:
                result_data = """
                    <table class="table table-bordered text-nowrap padding-left-50 margin-bottom-0" >
                        <tr><td>编号</td><td>日期</td><td>覆盖数</td><td>链接数</td><td>下载报表</td></tr>
                        {tr_html}
                    </table>
                """

            tr_html = ""
            for index, date in enumerate(sorted(temp_data.keys(), reverse=True), start=1):

                # 销售角色只能下载属于自己客户的报表
                file_path = temp_data[date]["statement_path"]

                # 超级管理员 管理员 营销顾问看对应的报表
                if role_id in [1, 4, 7]:
                    temp = temp_data[date]["statement_path"].split('/')
                    print(temp[:-1], 'yingxiaoguwen_' + temp[-1])

                    file_name = 'yingxiaoguwen_' + temp[-1]
                    file_path = '/'.join(temp[:-1]) + '/' + file_name
                    print(file_path)

                statement_path = "<a href='/{file_path}' download='{download}'>下载报表</a>".format(
                    file_path=file_path,
                    download=temp_data[date]["statement_path"].split("/")[-1]
                )

                if role_id == 12 and data_objs[0].client_user.xiaoshou_id != user_id and user_id != 133:
                    statement_path = ''

                if role_id in [5, 12]:
                    tr_html += """
                        <tr><td>{index}</td><td>{date}</td><td>{count}</td><td>{statement_path}</td></tr>
                    """.format(
                        index=index,
                        date=date,
                        count=temp_data[date]["cover_num"],
                        statement_path=statement_path
                    )
                else:
                    tr_html += """
                        <tr><td>{index}</td><td>{date}</td><td>{count}</td><td>{url_num}</td><td>{statement_path}</td></tr>
                    """.format(
                        index=index,
                        date=date,
                        count=temp_data[date]["cover_num"],
                        url_num=temp_data[date]["url_num"],
                        statement_path=statement_path
                    )

            result_data = result_data.format(tr_html=tr_html)
            return HttpResponse(result_data)

            # 展示编辑内容
        elif oper_type == 'task_edit_show':
            data_objs = models.UserProfile.objects.filter(
                id=o_id
            )
            if data_objs:
                data_objs[0].task_edit_show = not data_objs[0].task_edit_show
                data_objs[0].save()

            return redirect(reverse("cover_reports"))

        elif oper_type == "chongcha":
            today_date = datetime.datetime.now().strftime("%Y-%m-%d")
            models.KeywordsCover.objects.filter(keywords__client_user_id=o_id, create_date__gte=today_date).delete()
            models.KeywordsTopSet.objects.filter(client_user_id=o_id).update(update_select_cover_date=None)
            models.UserprofileKeywordsCover.objects.filter(client_user_id=o_id, create_date__gte=today_date).delete()

            return redirect(reverse("cover_reports"))


        elif oper_type == 'shanchulianjie':
            objs = models.UserProfile.objects.filter(id=o_id)
            user = objs[0]
            return render(request, 'wenda/cover_reports/client_reports_modal_shanchulianjie.html', locals())
            # return redirect(reverse("cover_reports"))


        elif oper_type == 'xiugaijifeiriqi':
            o_id = o_id
            return render(request, 'wenda/cover_reports/client_reports_modal_xiugaijifeiriqi.html', locals())


        elif oper_type == 'quanbushezhi':
            o_id=o_id
            obj = models.UserProfile.objects.get(id=o_id)
            print('obj - ---  -> ',obj )
            start_time = ''
            stop_time = ''
            if obj.jifei_start_date:
                start_time = obj.jifei_start_date.strftime('%Y-%m-%d')
            if obj.jifei_stop_date:
                stop_time = obj.jifei_stop_date.strftime('%Y-%m-%d')

            return render(request,'wenda/cover_reports/client_reports_modal_shezhi.html',locals())