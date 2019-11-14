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
import datetime


# 顾问对接
@pub.is_login
def my_client(request):
    client_data = models.UserProfile.objects.filter(is_delete=False, role_id=5).values('username', 'id')
    role_id = request.session.get("role_id")
    obj_user_id = request.session.get("user_id")
    qiyong_status = models.UserProfile.status_choices
    xinlaowenda_status = models.UserProfile.xinlaowenda_status_choices
    print('qiyong_status ========= >', qiyong_status)
    print('role_id ====== user_id =========>',role_id , obj_user_id )
    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))
        # print('request -- >',request.GET)
        # 排序
        column_list = ['client_user','qiyong_status','xinlaowenda_status']

        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]
        # print('column_list - -- -- >',order_column,type(order_column))
        # print('order[0] - - >',request.GET.get('order[0][column]'))
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column
        # print('order = = > ',order)
        # print('order_column = = > ',order_column)
        q = Q()
        for index, field in enumerate(column_list):
            # print('field = =  >',field)
            if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                if field =='client_user':
                    q.add(Q(**{'id': request.GET[field]}), Q.AND)
                elif field == 'qiyong_status':
                    q.add(Q(**{'status':request.GET[field]}) ,Q.AND)
                elif field == 'xinlaowenda_status':
                    print(request.GET[field])
                    q.add(Q(**{'xinlaowenda_status':request.GET[field]}) ,Q.AND)
                else:   
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        user_profile_objs = ''
        print('q ====q====q====q=====q=== q>',q)
        result_data = {'data':[]}
        clinet_date_objs = ''
        delete_client = ''

        if role_id in [1,7]:
            # print('进入 超级管理员0----role_id-->',role_id)
            clinet_date_objs = models.UserProfile.objects.filter(q).filter(role_id=5,is_delete=False)
            # clinet_date_objs = models.UserProfile.objects
            # delete_client = "<a href='client_delete/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>删除</a>".format(user_id=user_id)
        else:
            clinet_date_objs = models.UserProfile.objects.filter(q).filter(xiaoshou_id=obj_user_id).filter(role_id=5,is_delete=False)
        result_data = {
            "recordsFiltered": clinet_date_objs.count(),
            "recordsTotal": clinet_date_objs.count(),
            "data": []
            }
        # print('==========》 ',clinet_date_objs)
        for index, obj in enumerate(clinet_date_objs[start: (start + length)], start=1):
            user_id = obj.id

            # oper += "<a href='outer_update/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>修改</a>".format(user_id=user_id)
            rizhi = "<a href = 'look_log/{user_id}/'data-toggle='modal' data-target='#exampleFormModal'> 查看日志 </a>".format(user_id=user_id)
            beizhu = "<a href='marker_client/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>备注</a>".format(user_id=user_id)
            partner = "<a href='partner/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>合伙人</a>".format(user_id=user_id)
            result_data['data'].append({
                # 'delete_client':delete_client,
                'kaishi_jifei':rizhi,
                'kehu_name':obj.username,
                'user_id':obj.id,
                'index':index,
                'beizhu':beizhu,
                'partner':partner,
            })
        return HttpResponse(json.dumps(result_data))
    if "_pjax" in request.GET:
        return render(request, 'wenda/my_client/my_client_user_pjax.html', locals())
    return render(request, 'wenda/my_client/my_client_user.html', locals())


@pub.is_login
def my_client_oper(request, oper_type, o_id):
    role_id = request.session.get("role_id")
    response = pub.BaseResponse()
    obj_user_id = request.session.get("user_id")
    client_user_objs = models.UserProfile.objects.filter(is_delete=False)
    user_objs = client_user_objs.filter(id=obj_user_id)
    client_user = client_user_objs.filter(id=o_id)
    user_name = user_objs[0].username
    client_user = client_user[0].username
    now_date_time = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    if request.method == "POST":

        # 备注
        if oper_type =='marker_client':
            remark = request.POST.get('remark')
            print('备注 ========== 》' ,remark)
            if remark:
                objs = models.My_Client_User.objects.filter(client_user_name_id=o_id)
                if objs:
                    if objs[0].remark_beizhu:
                        client_log = "{user_name}修改了{client_user}的备注!".format(
                            user_name=user_name,client_user=client_user)
                        log_objs = models.My_Client_User_Log.objects.create(
                            client_log=client_log,
                            update_time=now_date_time,
                            guishu_user_id=o_id,
                            shijian_xinxi_yuan=objs[0].remark_beizhu
                        )

                        objs.update(remark_beizhu=remark)
                        log_objs.shijian_xinxi_xian=remark
                        log_objs.save()

                        response.status = True
                        response.message = '修改备注成功!'
                    else:
                        client_log = "{user_name}创建了{client_user}的备注!".format(
                            user_name=user_name, client_user=client_user)
                        client_log_objs = models.My_Client_User_Log.objects.create(
                            client_log=client_log,
                            update_time=now_date_time,
                            guishu_user_id=o_id,
                            shijian_xinxi_yuan = '无'
                        )

                        objs.create(remark_beizhu=remark,
                         client_user_name_id=o_id)
                        client_log_objs.shijian_xinxi_xian = remark
                        client_log_objs.save()
                    response.status = True
                    response.message = '创建备注成功!'
                # 库里没有数据 创建
                else:
                    print('=====else ==========')
                    client_log = "{user_name}创建了{client_user}的备注!".format(
                        user_name=user_name, client_user=client_user)
                    client_log_objs = models.My_Client_User_Log.objects.create(
                        client_log=client_log,
                        update_time=now_date_time,
                        guishu_user_id=o_id,
                        shijian_xinxi_yuan='无'
                    )

                    objs.create(client_user_name_id=o_id,
                        remark_beizhu=remark)
                    client_log_objs.shijian_xinxi_xian = remark
                    client_log_objs.save()

                    response.status = True
                    response.message = '备注成功'
            else:
                print(user_name ,client_user)
                client_log = "{user_name}操作{client_user}的备注失败!".format(
                    user_name=user_name, client_user=client_user)

                models.My_Client_User_Log.objects.create(
                    client_log=client_log,
                    update_time=now_date_time,
                    guishu_user_id=o_id,
                    shijian_xinxi_yuan='备注失败',
                    shijian_xinxi_xian='备注失败'
                )
                response.status = False
                response.message = '请输入备注!'

        # 合伙人
        elif oper_type == 'partner_info':
            print('request.POST========================> ', request.POST)
            partner = request.POST.get('partner')
            objs = models.record_partner_info.objects.filter(user_id=o_id)
            now_date = datetime.datetime.today()
            flag = True
            if objs:
                objs = objs.filter(create_date=now_date)
                if objs:
                    flag = False
                    objs.update(partner_info=partner)
                    response.status = True
                    response.message = '修改合伙人信息成功!'

            if flag:

                models.record_partner_info.objects.create(
                    user_id=o_id,
                    data=partner
                )
                response.status = False
                response.message = '请输入合伙人信息'

        return JsonResponse(response.__dict__)

    else:

        # 备注
        if oper_type == 'marker_client':
            print('o_id ============== >',o_id)
            objs = models.My_Client_User.objects.filter(client_user_name_id=o_id)
            if objs:
                remark = objs[0].remark_beizhu
            return render(request, 'wenda/my_client/my_client_marker_beizhu.html', locals())

        # 合伙人
        elif oper_type == 'partner':
            objs = models.record_partner_info.objects.filter(user_id=o_id).order_by('-create_date')
            if objs:
                partner_info = objs[0].partner_info
            return render(request, 'wenda/my_client/my_client_marker_partner.html', locals())

        # 查看日志
        elif oper_type == 'look_log':
            # client_log = "{user_name}--查看了{client_user}的日志!".format(
            #     user_name=user_name,client_user=client_user)
            # models.My_Client_User_Log.objects.create(
            #     client_log=client_log,
            #     update_time=now_date_time,
            #     guishu_user_id=o_id
            # )
            objs = models.My_Client_User_Log.objects.filter(guishu_user=o_id).order_by('-update_time')[0:10]
            result_data = ''
            tr_html = ''
            result_data = """
                   <table class="table table-bordered text-nowrap padding-left-50 margin-bottom-0" >
                        <tr>
                        <td>ID</td>
                        <td>编号</td>
                        <td>日期</td>
                        <td>事件</td>
                        <td>日志归属用户</td>
                        <td>查看事件信息</td>
                       {tr_html}
                   </table>
               """
            for index, obj in enumerate(objs):
                date_time = obj.update_time
                event = obj.client_log
                guishu = obj.guishu_user
                ID = obj.id
                data = ID
                update_time = obj.update_time
                chakan_shijian = "<a href='chakan_shijian_xinxi/{user_id}/?data={data}' id='chakan_shijian' data-toggle='modal' data-target='#exampleFormModal'>查看</a>".format(user_id=guishu.id,data=data)
                tr_html += """
                     <tr>
                     <td>{ID}</td>
                     <td>{index}</td>
                     <td  class='date_time'>{datetime}</td>
                     <td>{event}</td>
                     <td>{guishu}</td>
                     <td>{chakan_shijian}</td>
                     </tr>                                   
                      """.format(datetime=date_time,event=event,
                    guishu=guishu,index=index+1,chakan_shijian=chakan_shijian,ID=ID)
            result_data = result_data.format(tr_html=tr_html)
            return HttpResponse(result_data)

        elif oper_type == 'chakan_shijian_xinxi':
            data = request.GET.get('data')
            print('data ---------- >',data)
            objs = models.My_Client_User_Log.objects.filter(guishu_user_id=o_id,id=data)
            if objs:
                xianshuju = objs[0].shijian_xinxi_xian
                yuanshuju = objs[0].shijian_xinxi_yuan
            return render(request, 'wenda/my_client/my_client_chakan_shijian_xinxi.html', locals()  )
