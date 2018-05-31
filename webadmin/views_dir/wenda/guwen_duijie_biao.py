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
from django.db.models import Count,Sum
import os
import time
from wenda_celery_project import tasks
import datetime


# 顾问对接
@pub.is_login
def guwen_duijie(request):
    role_names = models.Role.objects.values_list("id", "name")
    status_choices = models.UserProfile.status_choices
    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = [ "id", "market__xiaoshou", "bianji", "kehu_username__username", "shiji_daozhang", "fugai_count",
                       "jifeishijian_start", "jifeishijian_stop"]
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
                if field in ["status"]:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)
                elif field == "role_names":
                    print(request.GET[field])
                    q.add(Q(**{"role_id": request.GET[field]}), Q.AND)
                else:
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        user_profile_objs = models.YingXiaoGuWen_DuiJie.objects.select_related("market","kehu_username").filter(kehu_username__is_delete=False).filter(
            q).order_by(order_column)

        print('user = = => ',user_profile_objs)

        result_data = {
            "recordsTotal": user_profile_objs.count(),
            "data": []
        }

        for index, obj in enumerate(user_profile_objs[start: (start + length)], start=1):
            bianji = obj.bianji.username
            xiaoshou = obj.market.username
            daozhang = obj.shiji_daozhang
            kehu_name = obj.kehu_username.username
            fugai = obj.fugai_count
            user_id = obj.kehu_username_id
            kaishi_jifei = obj.jifeishijian_start.strftime('%Y-%m-%d')
            tingbiao = obj.jifeishijian_stop.strftime('%Y-%m-%d')

            print('asdhjksankljf ',bianji , xiaoshou, daozhang, kehu_name, fugai,kaishi_jifei,tingbiao)
            oper = ''
            oper += "<a href='beizhu_botton/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>备注</a>".format(
                user_id=user_id)


            result_data["data"].append(
                [index,user_id, xiaoshou, bianji, kehu_name, daozhang, fugai,kaishi_jifei,tingbiao, oper ,1])

        return HttpResponse(json.dumps(result_data))
    if "_pjax" in request.GET:
        return render(request, 'wenda/guwen_Docking_table/guwen_duijie_biao_pjax.html', locals())
    return render(request, 'wenda/guwen_Docking_table/guwen_duijie_biao.html', locals())


@pub.is_login
def guwen_duijie_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    role_id = request.session.get("role_id")
    response = pub.BaseResponse()

    if request.method == "POST":
        # 添加
        if oper_type == "create":
            data_temp = {}
            q = Q()
            yonghuming_id = request.POST.get('yonghuming')
            xiaoshou_id = request.POST.get('xiaoshou')
            bianji_id = request.POST.get('bianji')
            daozhang = request.POST.get('daozhang')
            fugailiang = request.POST.get('fugailiang')
            start_time = request.POST.get('start_time')
            stop_time = request.POST.get('stop_time')
            print('--',yonghuming_id,xiaoshou_id,bianji_id,daozhang,fugailiang,start_time,stop_time)
            q.add(Q(xiaoshou_id=xiaoshou_id)|Q(id=yonghuming_id),Q.AND)
            objs =  models.UserProfile.objects.filter(q)
            if objs:
                obj = models.YingXiaoGuWen_DuiJie.objects.filter(kehu_username_id=yonghuming_id)
                if obj:
                    obj.update(
                        kehu_username_id=yonghuming_id,  # 客户名
                        market_id=xiaoshou_id,  # 销售
                        shiji_daozhang=daozhang,  # 实际到账
                        fugai_count=fugailiang,  # 覆盖总数
                        jifeishijian_start=start_time,  # 计费开始
                        jifeishijian_stop=stop_time,  # 结束计费
                        bianji_id=bianji_id  # 编辑
                    )
                else:
                    models.YingXiaoGuWen_DuiJie.objects.create(
                        market_id=xiaoshou_id,              # 销售
                        kehu_username_id=yonghuming_id,       # 客户名
                        shiji_daozhang=daozhang,        # 实际到账
                        fugai_count=fugailiang,         # 覆盖总数
                        jifeishijian_start=start_time,  # 计费开始
                        jifeishijian_stop=stop_time,    # 结束计费
                        bianji_id=bianji_id             # 编辑
                    )
            # else:
            #     response.message = "没有该用户"
            response.message = "添加成功"
        # 备注
        elif oper_type =='beizhuy_oper':
            panduan_xinwenda = request.POST.get('panduan_xinwenda')
            xuanchuan = request.POST.get('xuanchuanyaoqiu')
            shangwutong = request.POST.get('shangwutong')
            wendageshu = request.POST.get('wendageshu')
            obj = models.YingXiaoGuWen_DuiJie.objects.filter(kehu_username_id=o_id)
            if obj:
                if panduan_xinwenda and wendageshu:
                    obj.update(
                        shangwutong=shangwutong,
                        xuanchuanyaoqiu=xuanchuan,
                        wenda_geshu=wendageshu,
                        xinwenda=True,
                    )
                else:
                    obj.update(
                        shangwutong=shangwutong,
                        xuanchuanyaoqiu=xuanchuan,
                        xinwenda=False,
                    )

                response.message = '备注成功'
            else:
                response.message = '用户错误    '




        # 删除
        elif oper_type == "delete":
            obj = models.KeywordsTopSet.objects.get(id=o_id)
            obj.is_delete = True
            obj.save()

            response.status = True
            response.message = "删除成功"

        # 覆盖报表所有功能 修改计费 删除链接....
        elif oper_type == 'quanbushezhi':
            data_objs = models.UserProfile.objects.filter(
                id=o_id)
            print('requeat -----> ',request.POST)
            print('data_objs - -- - - -- - > ',data_objs)
            # zhanshibianji = request.POST.get('zhanshibianji')
            fasongbaobiao = request.POST.get('fasongbaobiao')
            chongchafugai = request.POST.get('chongchafugai')
            delete_lianjie = request.POST.get('delete_lianjie')
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
                today_date = datetime.datetime.now().strftime("%Y-%m-%d")
                models.KeywordsCover.objects.filter(keywords__client_user_id=o_id, create_date__gte=today_date).delete()
                models.KeywordsTopSet.objects.filter(client_user_id=o_id).update(update_select_cover_date=None)
                models.UserprofileKeywordsCover.objects.filter(client_user_id=o_id, create_date__gte=today_date).delete()

            # 删除链接
            if delete_lianjie:
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

        # 查询覆盖量
        elif oper_type == 'chaxunfugai':
            startfugai = request.POST.get('startfugai')
            stopfugai = request.POST.get('stopfugai')
            client_id = request.POST.get('client_id')
            print( '开始时间--结束时间 --  - ->',startfugai,stopfugai)
            print('id -- -- -> ',client_id)


            if startfugai and stopfugai:

                objs = models.UserprofileKeywordsCover.objects.filter(
                    client_user_id=client_id,
                    create_date__gte=startfugai,
                    create_date__lt=stopfugai
                ).values('cover_num')
                # print('objs -->', objs)
                data_list = []
                data_obj = 0
                for obj in objs:
                    print(obj)
                    for k,v in obj.items():
                        data_list.append(v)
                print(data_list)
                for data in data_list:
                    data_obj += int(data)
                print('data - - - - >',data_obj)
                response.code = 200
                response.message = '查询成功'
                response.data = data_obj
            return JsonResponse(response.__dict__)

        # 重新生成覆盖报表
        elif oper_type == 'rebuild':
            date_obj = datetime.datetime.now()
            date = date_obj.strftime("%Y-%m-%d")
            objs = models.UserprofileKeywordsCover.objects.filter(
                create_date=date,
            )
            objs.delete()
            response.code = 200
            response.message = '生成成功'
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

        pass
        # # 外层添加
        if oper_type == "create":
            client_objs = models.UserProfile.objects.filter(is_delete=False, role_id=5)
            return render(request, 'wenda/guwen_Docking_table/guwen_outer_create.html', locals())

        # 备注按钮
        elif oper_type == 'beizhu_botton':
            return render(request, 'wenda/guwen_Docking_table/guwen_beizhu_button.html', locals())

        elif oper_type == 'update':



            return render(request,'',locals())













        #
        # # 删除
        # elif oper_type == "delete":
        #     obj = models.KeywordsTopSet.objects.get(id=o_id)
        #     return render(request, 'wenda/keywords_top_set/keywords_top_set_modal_delete.html', locals())
        #
        # # 客户首页覆盖
        # elif oper_type == "client_cover":
        #     objs = models.KeywordsTopInfo.objects.values('keyword__client_user', 'keyword__client_user__username',
        #         'page_type').annotate(cover=Count("keyword__client_user")).all()
        #
        #     data = {}
        #     for obj in objs:
        #         client_user_id = obj["keyword__client_user"]
        #         username = obj["keyword__client_user__username"]
        #         page_type = obj["page_type"]
        #         cover = obj["cover"]
        #
        #         if client_user_id in data:
        #             data[client_user_id][page_type] = cover
        #             if page_type == 1:
        #                 data[client_user_id]["total"] = cover + data[client_user_id][3]
        #             else:
        #                 data[client_user_id]["total"] = cover + data[client_user_id][1]
        #         else:
        #             # 查询该用户添加了多少关键词数量
        #             keywords_top_set_objs = models.KeywordsTopSet.objects.filter(client_user_id=client_user_id)
        #             keywords_num = keywords_top_set_objs.count()
        #             no_select_keywords_num = keywords_top_set_objs.filter(status=1).count()
        #
        #             if keywords_top_set_objs.filter(status=1):
        #                 keywords_status = "查询中"
        #             else:
        #                 keywords_status = "已查询"
        #
        #             keywords_top_page_cover_excel_path = keywords_top_set_objs[
        #                 0].client_user.keywords_top_page_cover_excel_path
        #             keywords_top_page_cover_yingxiao_excel_path = keywords_top_set_objs[
        #                 0].client_user.keywords_top_page_cover_yingxiao_excel_path
        #
        #             data[client_user_id] = {
        #                 page_type: cover,
        #                 "username": username,
        #                 "keywords_num": "{keywords_num} / {no_select_keywords_num}".format(keywords_num=keywords_num,
        #                     no_select_keywords_num=no_select_keywords_num),
        #                 "keywords_status": keywords_status,
        #                 "keywords_top_page_cover_excel_path": keywords_top_page_cover_excel_path,
        #                 "keywords_top_page_cover_yingxiao_excel_path": keywords_top_page_cover_yingxiao_excel_path
        #             }
        #
        #     return render(request, 'wenda/keywords_top_set/keywords_top_set_modal_client_cover.html', locals())
        #
        # # 报表下载
        # elif oper_type == "download":
        #     client_data = models.KeywordsCover.objects.values(
        #         'keywords__client_user__username',
        #         'keywords__client_user_id'
        #     ).annotate(Count("keywords"))
        #     print(client_data)
        #     return render(request, "wenda/cover_reports/cover_reports_modal_download.html", locals())
        #
        # # 查看客户每日覆盖明细
        # elif oper_type == "show_click_info":
        #
        #     data_objs = models.UserprofileKeywordsCover.objects.filter(
        #         client_user_id=o_id
        #     )
        #     # data_objs = models.KeywordsCover.objects.select_related(
        #     #     "keywords__client_user",
        #     #     "keywords"
        #     # ).filter(keywords__client_user_id=o_id).values("create_date").annotate(count=Count('id'))
        #     temp_data = {}
        #     for obj in data_objs:
        #         print(' = = = == = = = >    ',obj)
        #         date_format = obj.create_date.strftime("%Y-%m-%d")
        #         temp_data[date_format] = {
        #             "cover_num": obj.cover_num,
        #             "url_num": obj.url_num,
        #             "statement_path": obj.statement_path
        #         }
        #     if role_id in [5, 12]:  # 客户角色和销售角色
        #         result_data = """
        #             <table class="table table-bordered text-nowrap padding-left-50 margin-bottom-0" >
        #                 <tr><td>编号</td><td>日期</td><td>覆盖数</td><td>下载报表</td></tr>
        #                 {tr_html}
        #             </table>
        #         """
        #     else:
        #         result_data = """
        #             <table class="table table-bordered text-nowrap padding-left-50 margin-bottom-0" >
        #                 <tr><td>编号</td><td>日期</td><td>覆盖数</td><td>链接数</td><td>下载报表</td></tr>
        #                 {tr_html}
        #             </table>
        #         """
        #
        #     tr_html = ""
        #     for index, date in enumerate(sorted(temp_data.keys(), reverse=True), start=1):
        #
        #         # 销售角色只能下载属于自己客户的报表
        #         file_path = temp_data[date]["statement_path"]
        #         print('file_path - -- - - - - -> ',file_path)
        #         print('temp_data -- - —— -> ',temp_data)
        #         # 超级管理员 管理员 营销顾问看对应的报表
        #         if role_id in [1, 4, 7]:
        #             temp = temp_data[date]["statement_path"].split('/')
        #             print(temp[:-1], 'yingxiaoguwen_' + temp[-1])
        #
        #             file_name = 'yingxiaoguwen_' + temp[-1]
        #             file_path = '/'.join(temp[:-1]) + '/' + file_name
        #             # print(file_path)
        #
        #         statement_path = "<a href='/{file_path}' download='{download}'>下载报表</a>".format(
        #             file_path=file_path,
        #             download=temp_data[date]["statement_path"].split("/")[-1]
        #         )
        #
        #         if role_id == 12 and data_objs[0].client_user.xiaoshou_id != user_id and user_id != 133:
        #             statement_path = ''
        #
        #         if role_id in [5, 12]:
        #             tr_html += """
        #                 <tr><td>{index}</td><td>{date}</td><td>{count}</td><td>{statement_path}</td></tr>
        #             """.format(
        #                 index=index,
        #                 date=date,
        #                 count=temp_data[date]["cover_num"],
        #                 statement_path=statement_path
        #             )
        #         else:
        #             tr_html += """
        #                 <tr><td>{index}</td><td>{date}</td><td>{count}</td><td>{url_num}</td><td>{statement_path}</td></tr>
        #             """.format(
        #                 index=index,
        #                 date=date,
        #                 count=temp_data[date]["cover_num"],
        #                 url_num=temp_data[date]["url_num"],
        #                 statement_path=statement_path
        #             )
        #
        #     result_data = result_data.format(tr_html=tr_html)
        #     return HttpResponse(result_data)
        #
        # # 展示编辑内容
        # elif oper_type == 'task_edit_show':
        #     data_objs = models.UserProfile.objects.filter(
        #         id=o_id
        #     )
        #     if data_objs:
        #         data_objs[0].task_edit_show = not data_objs[0].task_edit_show
        #         data_objs[0].save()
        #
        #     return redirect(reverse("cover_reports"))
        #
        # # 重查报表
        # elif oper_type == "chongcha":
        #     today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        #     models.KeywordsCover.objects.filter(keywords__client_user_id=o_id, create_date__gte=today_date).delete()
        #     models.KeywordsTopSet.objects.filter(client_user_id=o_id).update(update_select_cover_date=None)
        #     models.UserprofileKeywordsCover.objects.filter(client_user_id=o_id, create_date__gte=today_date).delete()
        #
        #     return redirect(reverse("cover_reports"))
        #
        # # 删除链接
        # elif oper_type == 'shanchulianjie':
        #     objs = models.UserProfile.objects.filter(id=o_id)
        #     user = objs[0]
        #     return render(request, 'wenda/cover_reports/client_reports_modal_shanchulianjie.html', locals())
        #     # return redirect(reverse("cover_reports"))
        #
        # # 修改计费日期
        # elif oper_type == 'xiugaijifeiriqi':
        #     o_id = o_id
        #     return render(request, 'wenda/cover_reports/client_reports_modal_xiugaijifeiriqi.html', locals())
        #
        # # 查讯覆盖量
        # elif oper_type == 'chaxunfugai':
        #     client_data = models.ClientCoveringData.objects.filter(client_user__is_delete=False).values(
        #         'client_user__username',
        #         'client_user_id'
        #     ).annotate(Count("id"))
        #     return render(request,'wenda/cover_reports/client_reports__modal_select_fugai_liang.html',locals())
        #
        # # 重新生成覆盖报表
        # elif oper_type == 'rebuild':
        #     return render(request,'wenda/cover_reports/cover_chongxin_shengcheng_baobiao.html',locals())