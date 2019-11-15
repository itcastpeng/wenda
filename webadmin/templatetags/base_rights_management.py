#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com

"""
权限管理
"""

from django import template

from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

from webadmin import models
import json

register = template.Library()
# rights_management_sales_list


# 显示消息的总数
@register.simple_tag
def ShowMessageCount(request):
    user_id = request.session['user_id']
    message_count = models.Message.objects.filter(user_id=user_id, status=1).count()

    if message_count == 0:
        message_count = ''

    return message_count


# 判断权限是否授权
@register.simple_tag
def WhetherAuthorized(request, auth_name, auth_url, top=False, left=False):
    """
    :param request:
    :param auth_name:   权限的名称
    :param auth_url:    权限的url
    :param top:         是否是顶部功能
    :return:
    """
    admin_role_list = [1, 4, 7, 11]

    user_id = request.session["user_id"]
    user_profile_obj = models.UserProfile.objects.select_related("role").get(id=user_id)
    access_rules = [int(i) for i in user_profile_obj.role.access_rules.split(',')]   # 该用户的角色具有的权限

    access_rules_objs = models.AccessRules.objects.all()

    # 顶部功能
    if top:
        if auth_name == "问答":
            if user_profile_obj.role.id != 11:
                result_html = get_top_wenda_html()
                return mark_safe(result_html)

        elif auth_name == "后台管理":
            if user_profile_obj.role.id in admin_role_list:     # 如果具有管理员权限,就可以看到顶部后台管理功能
                result_html = get_top_houtai_html()

                return mark_safe(result_html)

    # 左侧功能
    elif left:
        if auth_name == "问答":
            if user_profile_obj.role.id != 11:
                result_html = get_left_wenda_html(request,access_rules, access_rules_objs)

                return mark_safe(result_html)

        elif auth_name == "后台管理":
            if user_profile_obj.role.id in admin_role_list:  # 如果具有管理员权限,就可以看到左侧后台管理功能
                if user_profile_obj.role.id == 11:
                    active = "active"
                else:
                    active = ""
                result_html = get_left_houtai_html(access_rules, access_rules_objs, active)
                return mark_safe(result_html)

    return ''


# 顶部功能 问答
def get_top_wenda_html():
    result_html = """
        <li role="presentation" class="">
            <a data-toggle="tab" href="#admui-navTabsItem-1" aria-controls="admui-navTabsItem-1" role="tab" aria-expanded="false">
                <i class="icon wb-desktop"></i> <span>问答</span>
            </a>
        </li>
    """

    return result_html


# 顶部功能 后台管理
def get_top_houtai_html():
    result_html = """
        <li role="presentation" class="">
            <a data-toggle="tab" href="#admui-navTabsItem-2" aria-controls="admui-navTabsItem-2" role="tab" aria-expanded="false">
                <i class="icon wb-library"></i> <span>后台管理</span>
            </a> 
        </li>
    """

    return result_html


# 左侧功能 问答
def get_left_wenda_html(request,access_rules, access_rules_objs):

    result_html = """
        <div class="tab-pane animation-fade height-full" id="admui-navTabsItem-1" role="tabpanel">
            <div>
                <ul class="site-menu">

                    <li class="site-menu-category">问答</li>

                    {wenda_robot_html}
                    {my_task_html}
                    {task_list_html}
                    {my_client_html}
                    {search_rank_html}
                    {personal_center_html}
                    {hospital_information_html}
                    {financial_center_html}
                    {message_html}
                    {wait_clearing_html}
                    {edit_content_management_html}
                    {my_task_edit_html}
                    {sensitive_word_library_html}
                    {big_data_html}
                    {edit_content_detail_html}
                    {keywords_top_set_html}
                    {cover_reports_html}
                    {zhidaohuida_html}
                    {case_library_html}
                    {bianxiebaobiao_html}
                    {guwen_duijie_biao_html}
                    {fifty_guanjianci_jieping_html}
                    {partner_html}
                </ul>
            </div>
        </div>
    """

    wenda_robot_html = ""
    my_task_html = ""
    task_list_html = ""
    search_rank_html = ""
    personal_center_html = ""
    hospital_information_html = ""
    financial_center_html = ""
    message_html = ""
    wait_clearing_html = ""
    edit_content_management_html = ""
    my_task_edit_html = ""
    sensitive_word_library_html = ""
    big_data_html = ""
    edit_content_detail_html = ""
    keywords_top_set_html = ""
    cover_reports_html = ""
    zhidaohuida_html = ""
    case_library_html = ""
    bianxiebaobiao_html = ""
    guwen_duijie_biao_html = ""
    fifty_guanjianci_jieping_html = ""
    my_client_html = ""
    partner_html = ""

    # 问答机器人
    access_rules_obj = access_rules_objs.filter(name="问答机器人", url_path=reverse("wenda_robot"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        wenda_robot_html = """
                        <li class="site-menu-item">
                            <a data-pjax="" href="{wenda_robot}" target="_blank">
                                <i class="icon fa-github-alt" aria-hidden="true"></i>
                                <span class="site-menu-title margin-left-5">小明</span>
                            </a>
                        </li>
                    """.format(wenda_robot=reverse("wenda_robot"))

    # 我的任务
    access_rules_obj = access_rules_objs.filter(name="我的任务", url_path=reverse("my_task"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        my_task_html = """
                    <li class="site-menu-item">
                        <a data-pjax="" href="{my_task}" target="_blank">
                            <i class="icon fa-tasks" aria-hidden="true"></i>
                            <span class="site-menu-title margin-left-5">我的任务</span>
                        </a>
                    </li>
                """.format(my_task=reverse("my_task"))

    # 任务大厅
    access_rules_obj = access_rules_objs.filter(name="任务大厅", url_path=reverse("task_list"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        task_list_html = """
                <li class="site-menu-item">
                    <a data-pjax="" href="{task_list}" target="_blank">
                        <i class="icon fa-tasks" aria-hidden="true"></i>
                        <span class="site-menu-title margin-left-5">任务大厅</span>
                    </a>
                </li>
            """.format(task_list=reverse("task_list"))

    # 排名查询
    access_rule_obj_ids = [i[0] for i in access_rules_objs.filter(name__in=["指定关键词", "排名数据"]).values_list('id')]    # 取出这两个功能的id
    flag = False
    for access_rule_obj_id in access_rule_obj_ids:      # 判断当前用户所属角色是否拥有这个功能
        if access_rule_obj_id in access_rules:
            flag = True

    access_rules_obj = access_rules_objs.filter(name="排名查询", url_path="javascript:;")
    if (access_rules_obj and access_rules_obj[0].id in access_rules) or flag:

        search_rank_html = """
                <li class="site-menu-item has-sub">
                    <a href="javascript:;">
                        <i class="icon fa-bar-chart" aria-hidden="true"></i>
                        <span class="site-menu-title margin-left-5"> 排名查询</span>
                        <span class="site-menu-arrow"></span>
                    </a>
                    <ul class="site-menu-sub">
                        {set_keywords_html}
                        {rank_data_html}
                        {client_day_covering_num_html}
                    </ul>
                </li>
            """

        set_keywords_html = ""
        rank_data_html = ""
        client_day_covering_num_html = ""
        access_rules_obj = access_rules_objs.filter(name="指定关键词", url_path=reverse("set_keywords"))
        if access_rules_obj and access_rules_obj[0].id in access_rules:
            set_keywords_html = """
                    <li class="site-menu-item">
                        <a data-pjax="" href="{set_keywords}" target="_blank">
                            <span class="site-menu-title">指定关键词</span>
                        </a>
                    </li>
                """.format(set_keywords=reverse("set_keywords"))

        access_rules_obj = access_rules_objs.filter(name="排名数据", url_path=reverse("rank_data"))
        if access_rules_obj and access_rules_obj[0].id in access_rules:
            rank_data_html = """
                    <li class="site-menu-item">
                        <a data-pjax="" href="{rank_data}" target="_blank">
                            <span class="site-menu-title">排名数据</span>
                        </a>
                    </li>
                """.format(rank_data=reverse("rank_data"))

        access_rules_obj = access_rules_objs.filter(name="客户日覆盖数", url_path=reverse("client_day_covering_num"))
        if access_rules_obj and access_rules_obj[0].id in access_rules:
            client_day_covering_num_html = """
                        <li class="site-menu-item">
                            <a data-pjax="" href="{client_day_covering_num}" target="_blank">
                                <span class="site-menu-title">客户日覆盖数</span>
                            </a>
                        </li>
                    """.format(client_day_covering_num=reverse("client_day_covering_num"))

        search_rank_html = search_rank_html.format(
            set_keywords_html=set_keywords_html,
            rank_data_html=rank_data_html,
            client_day_covering_num_html=client_day_covering_num_html,
        )

    # 个人中心
    access_rules_obj = access_rules_objs.filter(name="个人中心", url_path=reverse("personal_center"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        personal_center_html = """
                <li class="site-menu-item">
                    <a data-pjax="" href="{personal_center}" target="_blank">
                        <i class="icon fa-user" aria-hidden="true"></i>
                        <span class="site-menu-title margin-left-5">个人中心</span>
                    </a>
                </li>
            """.format(personal_center=reverse("personal_center"))

    # 医院信息
    access_rules_obj = access_rules_objs.filter(name="医院信息", url_path=reverse("hospital_information"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        hospital_information_html = """
                <li class="site-menu-item">
                    <a data-pjax="" href="{hospital_information}" target="_blank">
                        <i class="icon fa-file" aria-hidden="true"></i>
                        <span class="site-menu-title margin-left-5">医院信息</span>
                    </a>
                </li>
            """.format(hospital_information=reverse("hospital_information"))

    # 财务中心
    access_rules_obj = access_rules_objs.filter(name="财务中心", url_path=reverse("financial_center"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        financial_center_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{financial_center}" target="_blank">
                    <i class="icon fa-jpy" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">财务中心</span>
                </a>
            </li>
        """.format(financial_center=reverse("financial_center"))

    # 消息中心
    access_rules_obj = access_rules_objs.filter(name="消息中心", url_path=reverse("message"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        message_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{financial_center}" target="_blank">
                    <i class="icon wb-bell" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">消息中心</span>
                </a>
            </li>
        """.format(financial_center=reverse("message"))

    # 待结算任务
    access_rules_obj = access_rules_objs.filter(name="待结算任务", url_path=reverse("wait_clearing"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        wait_clearing_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{wait_clearing}" target="_blank">
                    <i class="icon fa-legal" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">结算任务</span>
                </a>
            </li>
        """.format(wait_clearing=reverse("wait_clearing"))

    # 编辑内容管理
    access_rules_obj = access_rules_objs.filter(name="编辑内容管理", url_path=reverse("edit_content_management"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        edit_content_management_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{edit_content_management}" target="_blank">
                    <i class="icon fa-pencil" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">编辑内容管理</span>
                </a>
            </li>
        """.format(edit_content_management=reverse("edit_content_management"))

    # 我的任务-编辑
    access_rules_obj = access_rules_objs.filter(name="我的任务-编辑", url_path=reverse("my_task_edit"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        my_task_edit_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{my_task_edit}" target="_blank">
                    <i class="icon fa-pencil" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">我的任务-编辑</span>
                </a>
            </li>
        """.format(my_task_edit=reverse("my_task_edit"))

    # 敏感词库
    access_rules_obj = access_rules_objs.filter(name="敏感词库", url_path=reverse("sensitive_word_library"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        sensitive_word_library_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{sensitive_word_library}" target="_blank">
                    <i class="icon fa-pencil" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">敏感词库</span>
                </a>
            </li>
        """.format(sensitive_word_library=reverse("sensitive_word_library"))

    # 问答大数据
    access_rules_obj = access_rules_objs.filter(name="问答大数据", url_path=reverse("big_data"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        big_data_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{big_data}" target="_blank">
                    <i class="icon fa-database" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">问答大数据</span>
                </a>
            </li>
        """.format(big_data=reverse("big_data"))

    # 编辑内容详情
    access_rules_obj = access_rules_objs.filter(name="编辑内容详情", url_path=reverse("edit_content_detail"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        edit_content_detail_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{edit_content_detail}" target="_blank">
                    <i class="icon fa-crosshairs" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">编辑内容详情</span>
                </a>
            </li>
        """.format(edit_content_detail=reverse("edit_content_detail"))

    # 指定首页关键词
    access_rules_obj = access_rules_objs.filter(name="指定首页关键词", url_path=reverse("keywords_top_set"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        keywords_top_set_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{keywords_top_set}" target="_blank">
                    <i class="icon wb-flag" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">指定首页关键词</span>
                </a>
            </li>
        """.format(keywords_top_set=reverse("keywords_top_set"))
    if request.session['user_id'] != 26:
        # 覆盖报表
        access_rules_obj = access_rules_objs.filter(name="覆盖报表", url_path=reverse("cover_reports"))
        if access_rules_obj and access_rules_obj[0].id in access_rules:
            cover_reports_html = """
                <li class="site-menu-item">
                    <a data-pjax="" href="{cover_reports}" target="_blank">
                        <i class="icon fa-bar-chart" aria-hidden="true"></i>
                        <span class="site-menu-title margin-left-5">覆盖报表</span>
                    </a>
                </li>
            """.format(cover_reports=reverse("cover_reports"))

    objs = models.UserProfile.objects.filter(id=request.session['user_id'])
    print('-----------------> ', request.session['user_id'])
    if objs:
        obj = objs[0]
        if int(obj.role_id) in [15, '15']: # 知道合伙人
            print('-------obj.role_id---obj.role_id----obj.role_id---> ', obj.role_id)
            access_rules_obj = access_rules_objs.filter(name="合伙人信息", url_path=reverse("cover_reports"))
            if access_rules_obj and access_rules_obj[0].id in access_rules:
                print('access_rules_obj[0].id -------------> ', access_rules_obj[0].id, access_rules)
                partner_html = """
                            <li class="site-menu-item">
                                <a data-pjax="" href="{partner}" target="_blank">
                                    <i class="icon fa-bar-chart" aria-hidden="true"></i>
                                    <span class="site-menu-title margin-left-5">合伙人信息</span>
                                </a>
                            </li>
                        """.format(partner=reverse("partner"))


    # 知道回答
    access_rules_obj = access_rules_objs.filter(name="知道回答", url_path=reverse("zhidaohuida"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        zhidaohuida_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{cover_reports}" target="_blank">
                    <i class="icon fa-paw" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">知道回答</span>
                </a>
            </li>
        """.format(cover_reports=reverse("zhidaohuida"))

    # 案例库
    access_rules_obj = access_rules_objs.filter(name="案例库", url_path=reverse("case_library"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        case_library_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{cover_reports}" target="_blank">
                    <i class="icon fa-lightbulb-o" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">案例库</span>
                </a>
            </li>
        """.format(cover_reports=reverse("case_library"))

    # 编辑编写报表
    access_rules_obj = access_rules_objs.filter(name="编辑编写报表", url_path=reverse("bianxiebaobiao"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        bianxiebaobiao_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{cover_reports}" target="_blank">
                    <i class="icon fa-pie-chart" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">编辑编写报表</span>
                </a>
            </li>
        """.format(cover_reports=reverse("bianxiebaobiao"))

    # 营销顾问对接表
    access_rules_obj = access_rules_objs.filter(name="营销顾问对接表", url_path=reverse("guwen_duijie_biao"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        guwen_duijie_biao_html = """
               <li class="site-menu-item">
                   <a data-pjax="" href="{cover_reports}" target="_blank">
                       <i class="icon fa-random"></i>
                       <span class="site-menu-title margin-left-5">营销顾问对接表</span>
                   </a> 
               </li>
           """.format(cover_reports=reverse("guwen_duijie_biao"))

    # 五十个关键词截屏
    access_rules_obj = access_rules_objs.filter(name="关键词截屏", url_path=reverse("guanjianci_jieping"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        fifty_guanjianci_jieping_html = """
                 <li class="site-menu-item">
                     <a data-pjax="" href="{cover_reports}" target="_blank">
                         <i class="icon fa-photo"></i>   
                         <span class="site-menu-title margin-left-5">关键词截屏</span>
                     </a> 
                 </li>
             """.format(cover_reports=reverse("guanjianci_jieping"))
    # 我的客户
    access_rules_obj = access_rules_objs.filter(name="我的客户", url_path=reverse("my_client"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        my_client_html = """
                  <li class="site-menu-item">
                      <a data-pjax="" href="{cover_reports}" target="_blank">
                          <i class="icon fa-user"></i>
                          <span class="site-menu-title margin-left-5">我的客户</span>
                      </a> 
                  </li>
              """.format(cover_reports=reverse("my_client"))


    result_html = result_html.format(
        wenda_robot_html=wenda_robot_html,
        my_task_html=my_task_html,
        task_list_html=task_list_html,
        personal_center_html=personal_center_html,
        hospital_information_html=hospital_information_html,
        financial_center_html=financial_center_html,
        message_html=message_html,
        wait_clearing_html=wait_clearing_html,
        search_rank_html=search_rank_html,
        edit_content_management_html=edit_content_management_html,
        my_task_edit_html=my_task_edit_html,
        sensitive_word_library_html=sensitive_word_library_html,
        big_data_html=big_data_html,
        edit_content_detail_html=edit_content_detail_html,
        keywords_top_set_html=keywords_top_set_html,
        cover_reports_html=cover_reports_html,
        zhidaohuida_html=zhidaohuida_html,
        case_library_html=case_library_html,
        bianxiebaobiao_html=bianxiebaobiao_html,
        guwen_duijie_biao_html=guwen_duijie_biao_html,
        fifty_guanjianci_jieping_html=fifty_guanjianci_jieping_html,
        my_client_html=my_client_html,
        partner_html=partner_html
    )
    return result_html


# 左侧功能 后台管理
def get_left_houtai_html(access_rules, access_rules_objs, active):

    result_html = """
        <div class="tab-pane animation-fade height-full {active}" id="admui-navTabsItem-2" role="tabpanel">
            <div>
                <ul class="site-menu">

                    <li class="site-menu-category">后台管理</li>

                    {account_management_html}
                    {financial_management_html}
                    {global_settings_html}
                    {tixian_management_html}
                    {kehu_cunhuo_xiaohao_tongji_html}
                </ul>
            </div>
        </div>
    """

    account_management_html = ""
    financial_management_html = ""
    global_settings_html = ""
    tixian_management_html = ""
    kehu_cunhuo_xiaohao_tongji_html = ""

    access_rules_obj = access_rules_objs.filter(name="账户管理", url_path="javascript:;")

    if (access_rules_obj and access_rules_obj[0].id in access_rules) or access_rules_objs.filter(name__in=["用户管理", "角色管理", "权限管理"]):
        account_management_html = """
            <li class="site-menu-item has-sub">
                <a href="javascript:;">
                    <i class="icon fa-bar-chart" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5"> 账户管理</span>
                    <span class="site-menu-arrow"></span>
                </a>
                <ul class="site-menu-sub">
                    {user_management_html}
                    {role_management_html}
                    {auth_management_html}

                </ul>
            </li>
        """

        user_management_html = ""
        role_management_html = ""
        auth_management_html = ""
        access_rules_obj = access_rules_objs.filter(name="用户管理", url_path=reverse("user_management"))
        if access_rules_obj and access_rules_obj[0].id in access_rules:
            user_management_html = """
                <li class="site-menu-item">
                    <a data-pjax="" href="{user_management}" target="_blank">
                        <span class="site-menu-title">用户管理</span>
                    </a>
                </li>
            """.format(user_management=reverse("user_management"))

        access_rules_obj = access_rules_objs.filter(name="角色管理", url_path=reverse("role_management"))
        if access_rules_obj and access_rules_obj[0].id in access_rules:
            role_management_html = """
                <li class="site-menu-item">
                    <a data-pjax="" href="{role_management}" target="_blank">
                        <span class="site-menu-title">角色管理</span>
                    </a>
                </li>
            """.format(role_management=reverse("role_management"))

        access_rules_obj = access_rules_objs.filter(name="权限管理", url_path=reverse("auth_management"))
        if access_rules_obj and access_rules_obj[0].id in access_rules:
            auth_management_html = """
                <li class="site-menu-item">
                    <a data-pjax="" href="{auth_management}" target="_blank">
                        <span class="site-menu-title">权限管理</span>
                    </a>
                </li>
            """.format(auth_management=reverse("auth_management"))

        account_management_html = account_management_html.format(
            user_management_html=user_management_html,
            role_management_html=role_management_html,
            auth_management_html=auth_management_html
        )

    # 财务管理
    access_rules_obj = access_rules_objs.filter(name="财务管理", url_path=reverse("financial_management"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        financial_management_html = """
                    <li class="site-menu-item">
                        <a data-pjax="" href="{financial_management}" target="_blank">
                            <i class="icon fa-usd" aria-hidden="true"></i>
                            <span class="site-menu-title margin-left-5">财务管理</span>
                        </a>
                    </li>
                """.format(financial_management=reverse("financial_management"))

    # 全局设置
    access_rules_obj = access_rules_objs.filter(name="全局设置", url_path=reverse("global_settings"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        global_settings_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{global_settings}" target="_blank">
                    <i class="icon fa-cog" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">全局设置</span>
                </a>
            </li>
        """.format(global_settings=reverse("global_settings"))

    # 提现管理
    access_rules_obj = access_rules_objs.filter(name="提现管理", url_path=reverse("tixian_management"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        tixian_management_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{tixian_management}" target="_blank">
                    <i class="icon fa-cog" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">提现管理</span>
                </a>
            </li>
        """.format(tixian_management=reverse("tixian_management"))

    # 客户存活消耗统计
    access_rules_obj = access_rules_objs.filter(name="客户存活消耗统计", url_path=reverse("kehu_cunhuo_xiaohao_tongji"))
    if access_rules_obj and access_rules_obj[0].id in access_rules:
        kehu_cunhuo_xiaohao_tongji_html = """
            <li class="site-menu-item">
                <a data-pjax="" href="{kehu_cunhuo_xiaohao_tongji}" target="_blank">
                    <i class="icon fa-cog" aria-hidden="true"></i>
                    <span class="site-menu-title margin-left-5">客户存活消耗统计</span>
                </a>
            </li>
        """.format(kehu_cunhuo_xiaohao_tongji=reverse("kehu_cunhuo_xiaohao_tongji"))

    result_html = result_html.format(
        account_management_html=account_management_html,
        financial_management_html=financial_management_html,
        global_settings_html=global_settings_html,
        tixian_management_html=tixian_management_html,
        kehu_cunhuo_xiaohao_tongji_html=kehu_cunhuo_xiaohao_tongji_html,
        active=active
    )

    return result_html
