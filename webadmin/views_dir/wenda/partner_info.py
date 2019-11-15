
from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub
from webadmin import models
from django.http import JsonResponse
import json, datetime
from django.db.models import Q


# 合伙人信息
@pub.is_login
def partner_info(request):
    role_id = request.session.get("role_id")
    obj_user_id = request.session.get("user_id")

    # client_data = models.UserProfile.objects.filter(is_delete=False, role_id=15).values('username', 'id')
    # qiyong_status = models.UserProfile.status_choices
    # xinlaowenda_status = models.UserProfile.xinlaowenda_status_choices

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))
        # 排序
        column_list = ['client_user','qiyong_status','xinlaowenda_status']

        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column
        q = Q()
        # for index, field in enumerate(column_list):
        #     if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
        #         if field =='client_user':
        #             q.add(Q(**{'id': request.GET[field]}), Q.AND)
        #         elif field == 'qiyong_status':
        #             q.add(Q(**{'status':request.GET[field]}) ,Q.AND)
        #         elif field == 'xinlaowenda_status':
        #             print(request.GET[field])
        #             q.add(Q(**{'xinlaowenda_status':request.GET[field]}) ,Q.AND)
        #         else:
        #             q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        print('q ====q====q====q=====q=== q>',q)
        result_data = {'data':[]}
        user_profile_objs = ''
        clinet_date_objs = ''
        delete_client = ''

        clinet_date_objs = models.record_partner_info.objects.filter(q).filter(
            user_id=obj_user_id
        ).order_by(
            '-create_date'
        )

        result_data = {
            "recordsFiltered": clinet_date_objs.count(),
            "recordsTotal": clinet_date_objs.count(),
            "data": []
            }
        for index, obj in enumerate(clinet_date_objs[start: (start + length)], start=1):
            user_id = obj.id
            data = obj.data.split('|')
            liulanliang = data[0]
            guanfangdianhua = data[1]
            guanfangdianji = data[2]
            result_data['data'].append({
                'index':index,
                'id':obj.id,
                'liulanliang':liulanliang,
                'guanfangdianhua':guanfangdianhua,
                'guanfangdianji':guanfangdianji,
                'create_date':obj.create_date.strftime('%Y-%m-%d %H:%M:%S'),
            })


        return HttpResponse(json.dumps(result_data))
    if "_pjax" in request.GET:
        return render(request, 'wenda/partner/partner_info_pjax.html', locals())
    return render(request, 'wenda/partner/partner_info.html', locals())

