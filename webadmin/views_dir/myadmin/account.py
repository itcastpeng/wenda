#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse
from webadmin.templatetags.base_rights_management import ShowMessageCount
# from web.views_dir.pub import paging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def Custompager(baseurl, currentPage, totalpage):  # 基础页，当前页，总页数
    # 总页数<11
    # 0 -- totalpage
    # 总页数>11
    # 当前页大于5 currentPage-5 -- currentPage+5
    # currentPage+5是否超过总页数,超过总页数，end就是总页数
    # 当前页小于5 0 -- 11
    begin = 0
    end = 0
    if totalpage <= 11:
        begin = 0
        end = totalpage
    else:
        if currentPage > 5:
            begin = currentPage - 5
            end = currentPage + 5
            if end > totalpage:
                end = totalpage
        else:
            begin = 0
            end = 11
    pager_list = []
    if currentPage <= 1:
        first = '<li class="page-item first disabled"><a href="#" class="page-link">首页</a></li>'
    else:
        first = '<li class="page-item first"><a href="%s%d" class="page-link">首页</a></li>' % (baseurl, 1)
    pager_list.append(first)

    if currentPage <= 1:
        prev = '<li class="page-item prev disabled"><a href="#" class="page-link">上一页</a></li>'
    else:
        prev = '<li class="page-item prev"><a href="%s%d" class="page-link">上一页</a></li>' % (baseurl, currentPage - 1)
    pager_list.append(prev)

    for i in range(begin + 1, end + 1):
        if i == currentPage:
            temp = '<li class="page-item active"><a href="%s%d" class="page-link">%s</a></li>' % (baseurl, i, i)
        else:
            temp = '<li class="page-item"><a href="%s%d" class="page-link">%s</a></li>' % (baseurl, i, i)
        pager_list.append(temp)
    if currentPage >= totalpage:
        next = '<li class="page-item next"><a href="#" class="page-link">下一页</a></li>'
    else:
        next = '<li class="page-item next"><a href="%s%d" class="page-link">下一页</a></li>' % (baseurl, currentPage + 1)
    pager_list.append(next)
    if currentPage >= totalpage:
        last = '<li class="page-item last"><a href="#" class="page-link">末页</a></li>'
    else:
        last = '<li class="page-item last"><a href="%s%d" class="page-link">末页</a></li>' % (baseurl, totalpage)
    pager_list.append(last)
    result = ''.join(pager_list)
    return result  # 把字符串拼接起来


# 账户管理
@pub.is_login
@pub.is_auth
def account(request):
    company_name = request.session['company_name']
    user_id = request.session['user_id']
    user_profile_obj = models.UserProfile.objects.get(id=user_id)
    login_count = models.account_log.objects.filter(user_id=user_id).count()

    role_obj = models.Role.objects.filter(company__name=company_name)   # 取出当前公司的角色信息
    account_obj = models.account_log.objects.filter(user_id=user_id).order_by('-date')

    message_objs = models.Message.objects.filter(user_id=user_id).order_by('-create_at').order_by("status")

    message_unread_count = message_objs.filter(status=1).count()

    page_num = int(request.GET.get("page_num", 1))
    length = 10
    p = Paginator(message_objs, length)
    try:
        data_objs = p.page(page_num)
    except PageNotAnInteger:
        data_objs = p.page(1)
    except EmptyPage:
        data_objs = p.page(p.num_pages)

    message_objs = data_objs

    paging_html = Custompager("?page_num=", page_num, p.num_pages)

    if not message_unread_count:
        message_unread_count = ''

    if 'type' in request.GET:
        show_type = request.GET.get('type')
    else:
        show_type = None

    if "_pjax" in request.GET:
        return render(request, 'myadmin/account_pjax.html', locals())
    return render(request, 'myadmin/account.html', locals())


@pub.is_login
def account_oper(request, oper_type, o_id):
    response = pub.BaseResponse()

    if request.method == "POST":
        pass

    else:
        # 将消息改为已读
        if oper_type == "select":
            message_obj = models.Message.objects.get(id=o_id)
            message_obj.status = 2
            message_obj.save()

            response.status = True
            response.data = ShowMessageCount(request)
            return JsonResponse(response.__dict__)


