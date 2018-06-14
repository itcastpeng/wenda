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
from webadmin.forms import  guwen_duijie_biao
import datetime


# 顾问对接
@pub.is_login
def guwen_duijie(request):
    status_choices = models.UserProfile.status_choices
    client_data = models.UserProfile.objects.filter(is_delete=False, role_id=5).values('username', 'id')
    xiaoshou_data = models.UserProfile.objects.filter(is_delete=False,role_id=12).values('username','id')
    bianji_data =  models.UserProfile.objects.filter(is_delete=False,role_id=13).values('username','id')

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))
        # print('length ---- start',start ,length)
        client_user = request.GET.get('client_user')
        bianji_user = request.GET.get('bianji_user')
        xiaoshou_user = request.GET.get('xiaoshou_user')
        print('=======================================> ',
            client_user ,
            # 'xiaoshou:',
            xiaoshou_user,
            # 'guwen',
            bianji_user)

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

        user_profile_objs = ''

        if client_user or bianji_user or xiaoshou_user:
            if client_user:
                print('client_- > ',client_user)
                user_profile_objs = models.YingXiaoGuWen_DuiJie.objects.filter(kehu_username_id=client_user)
            elif bianji_user:
                user_profile_objs = models.YingXiaoGuWen_DuiJie.objects.filter(guwen_duijie_bianji=bianji_user)
            else:
                user_profile_objs = models.YingXiaoGuWen_DuiJie.objects.filter(marketid=xiaoshou_user)

        else:
            user_profile_objs = models.YingXiaoGuWen_DuiJie.objects.select_related("market").filter(kehu_username__is_delete=False).filter(
                q).order_by(order_column)

        result_data = {'data':[]}

        for index, obj in enumerate(user_profile_objs[start: (start + length)], start=1):
            q.add(Q(id=obj.kehu_username_id) | Q(id=obj.market_id),Q.AND)
            # bianji_obj = models.YingXiaoGuWen_DuiJie.objects.all()
            bianji_obj = obj.guwen_duijie_bianji.all().values('username')



            xiaoshou_obj = models.UserProfile.objects.filter(id=obj.market_id)
            bianji = ''
            xiaoshou = ''
            if bianji_obj:
                # print('bianji_obj - - >', bianji_obj)

                bianji = ",".join([i['username'] for i in bianji_obj])

            user_id = obj.id
            daozhang = obj.shiji_daozhang
            if obj.market:
                xiaoshou = obj.market
            kehu_name = obj.kehu_username.username
            index = index
            tingbiao = ''
            kaishi_jifei = ''
            daokuan_time = ''
            if obj.jifeishijian_stop:
                tingbiao = obj.jifeishijian_stop.strftime('%Y-%m-%d')
            if obj.jifeishijian_start:
                kaishi_jifei = obj.jifeishijian_start.strftime('%Y-%m-%d')
            if  obj.daokuan_time:
                daokuan_time = obj.daokuan_time.strftime('%Y-%m-%d')
            fugai_count = obj.fugai_count

            if obj.jifeishijian_start and obj.jifeishijian_stop and obj.jifeishijian_stop<datetime.date.today():
                kehu_name = '<span style="color: red">{username}</span>'.format(username=kehu_name)

            # print('xiaoshou --- - >',xiaoshou)
            # print('-------> ',user_id,tingbiao,kaishi_jifei,daozhang,kehu_name,user_id,index,daokuan_time,fugai_count,xiaoshou)

            oper = ''
            oper += "<a href='beizhu_botton/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>备注</a>".format(
                user_id=user_id)
            oper += "----<a href='outer_update/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>修改</a>".format(user_id=user_id)
            oper += "----<a href='outer_delete/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>删除</a>".format(user_id=user_id)
            oper += "----<a href = 'inner_create/{user_id}/'data-toggle='modal' data-target='#exampleFormModal'> 添加 </a>".format(user_id=user_id)
            result_data['data'].append({
                'oper':oper,
                'tingbiao':tingbiao,
                'kaishi_jifei':kaishi_jifei,
                'daozhang':daozhang,
                'bianji':bianji,
                'xiaoshou':str(xiaoshou),
                'kehu_name':kehu_name,
                'user_id':user_id,
                'index':index,
                'daokuan_time':daokuan_time,
                'fugai_count':fugai_count
            })

        return HttpResponse(json.dumps(result_data))
    if "_pjax" in request.GET:
        return render(request, 'wenda/guwen_Docking_table/guwen_duijie_biao_pjax.html', locals())
    return render(request, 'wenda/guwen_Docking_table/guwen_duijie_biao.html', locals())


@pub.is_login
def guwen_duijie_oper(request, oper_type, o_id):
    role_id = request.session.get("role_id")
    response = pub.BaseResponse()
    print('user',o_id)
    if request.method == "POST":
        # 外层添加
        if oper_type == "outer_create":
            print('request_post  -> ',request.POST)
            yonghuming_id = request.POST.get('yonghuming')
            bianjis = request.POST.getlist('bianji')
            bianji_list = []
            for bianji in bianjis:
                bianji_list.append(int(bianji))
            forms_obj = guwen_duijie_biao.OuterAddForm(request.POST)
            print('request_post = => ',request.POST)
            if forms_obj.is_valid():
                objs =  models.YingXiaoGuWen_DuiJie.objects.filter(kehu_username_id=yonghuming_id)
                if objs:
                    response.status = False
                    response.message = '添加失败,该用户已存在'
                else:
                    print('forms_obj.cleaned_data = ==  > ',forms_obj.cleaned_data)

                    yingxiaoguwen_obj = models.YingXiaoGuWen_DuiJie.objects.create(
                        market_id=forms_obj.cleaned_data['xiaoshou'],              # 销售
                        kehu_username_id=yonghuming_id,       # 客户名
                        shiji_daozhang=forms_obj.cleaned_data['daozhang'],              # 实际到账
                        fugai_count=forms_obj.cleaned_data['fugailiang'],               # 覆盖总数
                        jifeishijian_start=forms_obj.cleaned_data['start_time'],  # 计费开始
                        jifeishijian_stop=forms_obj.cleaned_data['stop_time'],    # 结束计费
                        # bianji_id=forms_obj.cleaned_data['bianji'],            # 编辑
                        daokuan_time=forms_obj.cleaned_data['daokuan_time']       # 到款日期
                    )
                    # for bianji in bianji_list:
                    #     print('ianji - - - > ',bianji)
                    yingxiaoguwen_obj.guwen_duijie_bianji = bianji_list

                    response.status = True
                    response.message = "添加成功"
            else:
                print(forms_obj.errors)
                response.status = False
                response.message = '参数验证失败'

        # 备注
        elif oper_type =='beizhuy_oper':
            panduan_xinwenda = request.POST.get('panduan_xinwenda')
            xuanchuan = request.POST.get('xuanchuanyaoqiu')
            shangwutong = request.POST.get('shangwutong')
            wendageshu = request.POST.get('wendageshu')
            obj = models.YingXiaoGuWen_DuiJie.objects.filter(id=o_id)
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
                response.status = True
                response.message = '备注成功'
            else:
                response.status = False
                response.message = '用户错误'

        # 外层修改
        elif oper_type == 'outer_update':
            # daokuan_time =''
            # start_time =''
            # stop_time =''
            # if request.POST.get('daokuan_riqi'):
            #     daokuan_time = request.POST.get('daokuan_riqi')
            #     print('=============>',daokuan_time)
            # if request.POST.get('start_time'):
            #     start_time = request.POST.get('start_time')
            #     print('=============>',start_time)
            # if request.POST.get('stop_time'):
            #     stop_time = request.POST.get('stop_time')
            #     print('=============>',stop_time)
            print('request-----> ',request.POST)
            forms_obj = guwen_duijie_biao.OuterUpdateForm(request.POST)
            if forms_obj.is_valid():
                print('forms_obj.cleaned_data -->', forms_obj.cleaned_data)
                obj = models.YingXiaoGuWen_DuiJie.objects.filter(id=o_id)
                bianjis = request.POST.getlist('bianji_outer_update')
                print('bianjis -- -  >',bianjis)
                bianji_list = []
                for bianji in bianjis:
                    bianji_list.append(int(bianji))
                if obj:
                    obj_update = obj.update(
                    market_id=forms_obj.cleaned_data['xiaoshou_outer_update'],   # 销售
                    shiji_daozhang=forms_obj.cleaned_data['daozhang'],           # 实际到账
                    fugai_count=forms_obj.cleaned_data['fugailiang'],            # 覆盖总数
                    # bianji_id=forms_obj.cleaned_data['bianji_outer_update'],     # 编辑
                    )
                    if forms_obj.cleaned_data['daokuan_riqi']:
                       obj.update(daokuan_time=forms_obj.cleaned_data['daokuan_riqi'])    # 到款日期
                    if forms_obj.cleaned_data['stop_datatime']:
                        obj.update(jifeishijian_stop=forms_obj.cleaned_data['stop_datatime'])   # 结束计费
                    if  forms_obj.cleaned_data['start_datatime']:
                        obj.update(jifeishijian_start=forms_obj.cleaned_data['start_datatime'])       # 计费开始
                    print('bianji_list - -- >',bianji_list)
                    if bianji_list:
                        obj[0].guwen_duijie_bianji=bianji_list

                        response.status = True
                        response.message = '修改成功'
            else:
                print('cuowu --',forms_obj.errors)
                response.status = False
                response.message = 'form验证失败'

        # 外层删除
        elif oper_type == 'outer_delete':
            obj = models.YingXiaoGuWen_DuiJie.objects.get(id=o_id)
            if obj:
                obj.delete()
                response.status = True
                response.message = '删除成功'
            else:
                response.status = False
                response.message = '删除失败'

        # 内层添加
        elif oper_type == 'inner_create':
            print('内层添加')
            obj = models.YingXiaoGuWen_DuiJie.objects.get(id=o_id)
            print('obj --- > ',obj )
            daozhang = request.POST.get('daozhang')
            fugailiang = request.POST.get('fugailiang')
            start_time = request.POST.get('start_time')
            stop_time = request.POST.get('stop_time')
            panduan_xinwenda = request.POST.get('panduan_xinwenda')
            if panduan_xinwenda :
                panduan_xinwenda = True
            else:
                panduan_xinwenda = False
            data_temp = {}
            forms_obj = guwen_duijie_biao.InnerCreateForm(request.POST)
            if forms_obj.is_valid():
                data_temp = {
                    "shiji_daozhang":daozhang,
                    "fugai_count":fugailiang,
                    "jifeishijian_start":start_time,
                    "jifeishijian_stop":stop_time,
                    "xinwenda":panduan_xinwenda,
                    "guishu":obj
                }
                models.YingXiaoGuWen_NeiBiao.objects.create(**data_temp)
                response.status = True
                response.message = '添加成功'
            else:
                response.status = False
                response.message = 'form验证失败'

        # 内层修改
        elif oper_type == 'inner_update':
            obj = models.YingXiaoGuWen_NeiBiao.objects.get(id=o_id)
            if obj:
                daozhang = request.POST.get('daozhang')
                fugailiang = request.POST.get('fugailiang')
                start_time = request.POST.get('start_time')
                stop_time = request.POST.get('stop_time')
                panduan_xinwenda = request.POST.get('panduan_xinwenda')
                if panduan_xinwenda:
                    panduan_xinwenda = True
                else:
                    panduan_xinwenda = False
                print(panduan_xinwenda)
                data_temp = {
                'daozhang' : daozhang,
                'fugailiang' : fugailiang ,
                'start_time' : start_time ,
                'stop_time' : stop_time,
                'panduan_xinwenda' : panduan_xinwenda ,
                }
                # print('到这了=======')
                forms_obj = guwen_duijie_biao.InnerCreateForm(data_temp)
                if forms_obj.is_valid():
                    print('验证成功')
                    cleant = forms_obj.cleaned_data
                    obj.shiji_daozhang = cleant['daozhang']
                    obj.jifeishijian_start = cleant['start_time']
                    obj.jifeishijian_stop = cleant['stop_time']
                    obj.fugai_count =  cleant['fugailiang']
                    obj.xinwenda =  cleant['panduan_xinwenda']
                    obj.save()
                    # print('obj - -- > ',obj.xinwenda)
                    response.status = True
                    response.message = '修改成功'
                else:
                    response.status = False
                    response.message = 'form验证失败'
            else:
                response.status = False
                response.message = '修改失败'

        # 内层删除
        elif oper_type == 'inner_delete':
            print('内层删除')
            obj = models.YingXiaoGuWen_NeiBiao.objects.get(id=o_id)
            if obj:
                obj.delete()

                response.status = True
                response.message = '删除成功'
            else:
                response.status = False
                response.message = '删除失败'

        return JsonResponse(response.__dict__)

    else:
        # 外层添加
        if oper_type == "outer_create":
            client_objs = models.UserProfile.objects.filter(is_delete=False, role_id=5)
            xiaoshous = models.UserProfile.objects.filter(is_delete=False,role_id=12)
            bianjis = models.UserProfile.objects.filter(is_delete=False,role_id=13)
            return render(request, 'wenda/guwen_Docking_table/guwen_duijie_outer/guwen_outer_create.html', locals())

        # 备注按钮
        elif oper_type == 'beizhu_botton':
            objs = models.YingXiaoGuWen_DuiJie.objects.filter(id=o_id).values('shangwutong','fugai_count','xuanchuanyaoqiu','wenda_geshu','xinwenda')
            shangwutong = objs[0]['shangwutong']
            fugailiang = objs[0]['fugai_count']
            xinwenda = objs[0]['xinwenda']
            wenda_geshu = objs[0]['wenda_geshu']
            xuanchuanyaoqiu = objs[0]['xuanchuanyaoqiu']
            if wenda_geshu is None:
                wenda_geshu = ''
            if shangwutong is None:
                shangwutong = ''
            if xuanchuanyaoqiu is None:
                xuanchuanyaoqiu = ''
            print('---------->',shangwutong,fugailiang,xuanchuanyaoqiu,wenda_geshu,xinwenda)
            return render(request, 'wenda/guwen_Docking_table/guwen_duijie_outer/guwen_beizhu_button.html', locals())

        # 外层修改
        elif oper_type == 'outer_update':
            objs = models.YingXiaoGuWen_DuiJie.objects.filter(id=o_id)
            if objs:
                bianji_list  = []
                print('进入 -- - - -= == = == =')
                bianji_panduan=''
                bianji_panduan = objs[0].guwen_duijie_bianji.all()
                if bianji_panduan:
                    bianji_panduan = bianji_panduan.values('username','id')
                    for bianji in bianji_panduan:
                        bianji_name = bianji['username']
                        bianji_id = bianji['id']
                        bianji_list.append({
                            'username':bianji_name,
                            'o_id':bianji_id
                        })
                xiaoshou_id = ''
                xiaoshouming = ''
                if objs[0].market_id:
                    xiaoshou_id = int(objs[0].market_id)
                if objs[0].market:
                    xiaoshouming = objs[0].market
                daozhang = ''
                if objs[0].shiji_daozhang:
                    daozhang = objs[0].shiji_daozhang
                fugai = ''
                if objs[0].fugai_count:
                    fugai = objs[0].fugai_count
                kaishi_time = ''
                jieshu_time = ''
                daokuan_time = ''
                if objs[0].jifeishijian_start:
                    kaishi_time = objs[0].jifeishijian_start.strftime('%Y-%m-%d')
                if objs[0].jifeishijian_stop:
                    jieshu_time = objs[0].jifeishijian_stop.strftime('%Y-%m-%d')
                if objs[0].daokuan_time:
                    daokuan_time = objs[0].daokuan_time.strftime('%Y-%m-%d')
                xiaoshous = models.UserProfile.objects.filter(role_id=12)
                bianjis = models.UserProfile.objects.filter(role_id=13)
                print('bianji_list --  >',bianji_list)
                print('locals() = = == = >',locals())
            return render(request, 'wenda/guwen_Docking_table/guwen_duijie_outer/guwen_outer_update.html',locals())

        # 外层删除
        elif oper_type == 'outer_delete':
            obj = models.YingXiaoGuWen_DuiJie.objects.filter(id=o_id)
            username = obj[0].kehu_username.username
            print('o_id = ==  == => 1',o_id)
            return render(request, 'wenda/guwen_Docking_table/guwen_duijie_outer/guwen_outer_delete.html',locals())

        # 点开详情
        elif oper_type == 'outer_xiangqing':
            objs = models.YingXiaoGuWen_NeiBiao.objects.filter(guishu=o_id)
            tr_html = ''
            result_data = """
                             <table class="table table-bordered text-nowrap padding-left-50 margin-bottom-0" >
                                 <tr><td>编号</td><td style="display:none;">ID</td><td>实际到账</td><td>覆盖总数</td><td>计费时间</td><td>停表时间</td><td>是否操作新问答</td><td>操作</td></tr>
                                 {tr_html}
                             </table>
                         """
            for index,obj in enumerate(objs):
                inner_id = obj.id
                jifeistart = obj.jifeishijian_start
                tingbiao = obj.jifeishijian_stop
                fugai = obj.fugai_count
                daozhang = obj.shiji_daozhang
                panduan_xinwenda = obj.xinwenda
                if panduan_xinwenda == True:
                    panduan_xinwenda = '是'
                else:
                    panduan_xinwenda = '否'
                tr_html += """
                           <tr>
                           <td>{index}</td>
                           <td>{daozhang}</td>
                           <td>{fugai}</td>
                           <td>{jifeistart}</td>
                           <td>{tingbiao}</td>
                           <td>{panduan_xinwenda}</td>
                           <td style="display:none">{inner_id}</td>
                           <td>
                           <a href="inner_update/{o_id}/"  data-toggle='modal' data-target='#exampleFormModal'>修改</a>
                           ----<a href="inner_delete/{o_id}/"  data-toggle='modal' data-target='#exampleFormModal'>删除</a></td>
                           </tr>                                   
                            """.format(index=index,inner_id=inner_id,fugai=fugai,daozhang=daozhang,
                            jifeistart=jifeistart,tingbiao=tingbiao,panduan_xinwenda=panduan_xinwenda,o_id=obj.id)


            result_data = result_data.format(tr_html=tr_html)
            return HttpResponse(result_data)

        # 内层添加
        elif oper_type == 'inner_create':
            return render(request,'wenda/guwen_Docking_table/guwen_duijie_inner/guwen_duijie_inner_create.html',locals())

        # 内层修改
        elif oper_type == 'inner_update':
            obj = models.YingXiaoGuWen_NeiBiao.objects.get(id=o_id)
            daozhang = obj.shiji_daozhang
            fugai = obj.fugai_count
            jifei_start = obj.jifeishijian_start.strftime('%Y-%m-%d')
            jifei_stop = obj.jifeishijian_stop.strftime('%Y-%m-%d')
            panduan_xinwenda = obj.xinwenda
            return render(request, 'wenda/guwen_Docking_table/guwen_duijie_inner/guwen_inner_update.html', locals())

        # 内层删除
        elif oper_type == 'inner_delete':
            obj = models.YingXiaoGuWen_NeiBiao.objects.get(id=o_id)
            username = obj.guishu.kehu_username
            return render(request, 'wenda/guwen_Docking_table/guwen_duijie_inner/guwen_inner_delete.html', locals())



