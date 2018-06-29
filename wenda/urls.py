"""wenda URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from webadmin.views_dir.myadmin import account, user_management, role_management, auth_management, \
    hospital_information, financial_management, global_settings, tixian_management, kehu_cunhuo_xiaohao_tongji

from webadmin.views_dir.wenda import task_list, personal_center, financial_center, message, wenda_robot, api, \
    wait_clearing, my_task, set_keywords, rank_data, edit_content_management, my_task_edit, edit_error_content,\
    sensitive_word_library, big_data, edit_content_detail, client_day_covering_num, keywords_top_set, cover_reports, \
    show_wenda_cover_num, zhidaohuida, case_library ,bianxiebaobiao,according_geturl,guwen_duijie_biao,fifty_guanjianci_jieping,my_client

from webadmin.views_dir.wechat import wechat

from webadmin import views

urlpatterns = [
    url(r'^django_admin/', admin.site.urls),

    # #################### 微信公众号 ####################
    url(r'^wechat/', wechat.index),

    # #################### API ####################
    url(r'^api/login/$', api.login),        # 登录
    url(r'^api/get_wenda_task/', api.get_wenda_task, name="get_wenda_task"),    # 获取任务
    url(r'^api/check_ipaddr/', api.check_ipaddr, name="check_ipaddr"),    # 查询ip是否已经使用

    url(r'^api/check_wenda_link/', api.check_wenda_link),    # 检查问答回链状态的接口

    url(r'^api/set_keywords_rank/', api.set_keywords_rank),    # 检查关键词排名状态
    url(r'^api/check_follow_wechat/', api.check_follow_wechat),    # 查看用户是否关注公众号

    # 通过公众号发送消息
    url(r'^api/sendMsg', api.sendMsg),

    # 检查的知道url 中的答案不存在
    url(r'^api/keywords_top_set/(?P<oper_type>\w+)', api.keywords_top_set_oper),

    # 查询关键词首页百度条数
    url(r'^api/keywords_top_set', api.keywords_top_set),

    # 查看3天未联系的客户信息
    url(r'^api/tongji_kehu_shiyong', api.tongji_kehu_shiyong),    # 查看3天未联系的客户信息

    # 缓存查询关键词数据到redis中
    url(r'^api/keywords_cover_select_models', api.keywords_cover_select_models),

    # 查询关键词覆盖(覆盖模式)
    url(r'^api/keywords_cover', api.keywords_cover),

    # 检查知道url 是我们自己操作的(覆盖模式)
    url(r'^api/check_zhidao_url', api.check_zhidao_url),

    # 添加知道问答
    url(r'api/add_zhidaohuida', api.add_zhidaohuida),

    # 链接跳转
    url(r'api/tiaozhuan', api.tiaozhuan),

    # 判断当前应该操作什么任务
    url(r'api/current_oper_task', api.current_oper_task),

    # 渠道操作商务通存活
    url(r'api/qudao_shangwutong_cunhuo', api.qudao_shangwutong_cunhuo),

    # 查询用户到期信息
    url(r'^api/jifeidaoqitixing/(?P<oper_type>\w+)/(?P<o_id>\d+)',api.jifeidaoqitixing),

    # 查询每日覆盖量
    url(r'^api/fugailiangtixing/(?P<oper_type>\w+)/(?P<o_id>\d+)',api.fugailiangtixing),

    # 新问答完成不会打回到编辑
    url(r'api/xinwenda_wancheng_budahui', api.xinwenda_wancheng_budahui),

    # 五十个关键词 获取关键词
    url(r'api/fifty_guanjianci_fabu', api.fifty_guanjianci_fabu),

    # 指定关键词-优化-协助调用查询数据库
    url(r'api/keywords_select_models', api.keywords_select_models),
    # #################### 问答 ####################

    # 问答机器人
    url(r'^wenda_robot/(?P<oper_type>\w+)/(?P<o_id>\d+)/', wenda_robot.wenda_robot_oper),
    url(r'^wenda_robot/', wenda_robot.wenda_robot, name="wenda_robot"),

    # 我的任务
    url(r'^my_task/(?P<oper_type>\w+)/(?P<o_id>\d+)/', my_task.my_task_oper),
    url(r'^my_task/', my_task.my_task, name="my_task"),

    # 任务大厅
    url(r'^task_list/(?P<oper_type>\w+)/(?P<o_id>\d+)/', task_list.task_list_oper),
    url(r'^task_list/', task_list.task_list, name="task_list"),

    # 指定关键词
    url(r'^set_keywords/(?P<oper_type>\w+)/(?P<o_id>\d+)/', set_keywords.set_keywords_oper),
    url(r'^set_keywords/', set_keywords.set_keywords, name="set_keywords"),

    # 排名数据
    url(r'^rank_data/(?P<oper_type>\w+)/(?P<o_id>\d+)/', rank_data.rank_data_oper),
    url(r'^rank_data/', rank_data.rank_data, name="rank_data"),

    # 客户日覆盖数
    url(r'^client_day_covering_num/', client_day_covering_num.client_day_covering_num, name="client_day_covering_num"),

    # 个人中心
    url(r'^personal_center/(?P<oper_type>\w+)/(?P<o_id>\d+)/', personal_center.personal_center_oper),
    url(r'^personal_center/', personal_center.personal_center, name="personal_center"),

    # 医院信息
    url(r'^hospital_information/(?P<oper_type>\w+)/(?P<o_id>\d+)/', hospital_information.hospital_information_oper),
    url(r'^hospital_information/', hospital_information.hospital_information, name="hospital_information"),

    # 财务中心
    url(r'^financial_center/(?P<oper_type>\w+)/(?P<o_id>\d+)/', financial_center.financial_center_oper,),
    url(r'^financial_center/', financial_center.financial_center, name="financial_center"),

    # 消息中心
    url(r'^message/(?P<oper_type>\w+)/(?P<o_id>\d+)/', message.message_oper),
    url(r'^message/', message.message, name="message"),

    # 结算任务
    url(r'^wait_clearing/(?P<oper_type>\w+)/(?P<o_id>\d+)/', wait_clearing.wait_clearing_oper),
    url(r'^wait_clearing/', wait_clearing.wait_clearing, name="wait_clearing"),

    # 编辑内容管理
    url(r'^edit_content_management/(?P<oper_type>\w+)/(?P<o_id>\d+)/', edit_content_management.edit_content_management_oper),
    url(r'^edit_content_management/', edit_content_management.edit_content_management, name="edit_content_management"),


    # 我的任务-编辑
    url(r'^my_task_edit/(?P<oper_type>\w+)/(?P<o_id>\d+)/', my_task_edit.my_task_edit_oper),
    url(r'^my_task_edit/', my_task_edit.my_task_edit, name="my_task_edit"),

    # 编辑内容详情
    url(r'^edit_content_detail/(?P<oper_type>\w+)/(?P<o_id>\d+)/', edit_content_detail.edit_content_detail_oper),
    url(r'^edit_content_detail/', edit_content_detail.edit_content_detail, name="edit_content_detail"),


    url(r'^edit_error_content/(?P<o_id>\d+)/', edit_error_content.edit_error_content),    # 编辑修改出现异常的内容

    # 敏感词库
    url(r'^sensitive_word_library/(?P<oper_type>\w+)/(?P<o_id>\d+)/', sensitive_word_library.sensitive_word_library_oper),
    url(r'^sensitive_word_library/', sensitive_word_library.sensitive_word_library, name="sensitive_word_library"),


    # 问答大数据
    url(r'^big_data/(?P<oper_type>\w+)/(?P<o_id>\d+)/', big_data.big_data_oper),
    url(r'^big_data/', big_data.big_data, name="big_data"),

    # 指定首页关键词
    url(r'^keywords_top_set/(?P<oper_type>\w+)/(?P<o_id>\d+)/', keywords_top_set.keywords_top_set_oper),
    url(r'^keywords_top_set/', keywords_top_set.keywords_top_set, name="keywords_top_set"),

    # 覆盖报表
    url(r'^cover_reports/(?P<oper_type>\w+)/(?P<o_id>\d+)/', cover_reports.cover_reports_oper),
    url(r'^cover_reports/', cover_reports.cover_reports, name="cover_reports"),

    # 覆盖报表(公众号)
    url(r'^show_wenda_cover_num/(?P<openid>\w+)/(?P<date>(\d+)-(\d+)-(\d+))', show_wenda_cover_num.show_wenda_cover_num_oper),
    url(r'^show_wenda_cover_num/(?P<openid>\w+)/', show_wenda_cover_num.show_wenda_cover_num, name="show_wenda_cover_num"),

    # 知道回答
    url(r'^zhidaohuida/(?P<oper_type>\w+)/(?P<o_id>\d+)/', zhidaohuida.zhidaohuida_oper),
    url(r'^zhidaohuida/', zhidaohuida.zhidaohuida, name="zhidaohuida"),

    # 案例库
    url(r'^case_library/(?P<oper_type>\w+)/(?P<o_id>\d+)/', case_library.case_library_oper),
    url(r'^case_library/', case_library.case_library, name="case_library"),

    # 编辑编写报表
    url(r'^bianxiebaobiao/', bianxiebaobiao.bianxiebaobiao, name="bianxiebaobiao"),

    # 接收链接返回电话号码
    url(r'^according/',according_geturl.according_geturl,name='according_geturl'),

    # 营销顾问对接表
    url(r'^guwen_duijie_biao/(?P<oper_type>\w+)/(?P<o_id>\d+)/', guwen_duijie_biao.guwen_duijie_oper),
    url(r'^guwen_duijie_biao/', guwen_duijie_biao.guwen_duijie, name="guwen_duijie_biao"),

    # 关键词截屏
    url(r'^guanjianci_jieping/(?P<oper_type>\w+)/(?P<o_id>\d+)/', fifty_guanjianci_jieping.guanjianci_jieping_oper),
    url(r'^guanjianci_jieping/', fifty_guanjianci_jieping.guanjianci_jieping, name="guanjianci_jieping"),

    # 我的客户
    url(r'^my_client/(?P<oper_type>\w+)/(?P<o_id>\d+)/', my_client.my_client_oper),
    url(r'^my_client/', my_client.my_client, name="my_client"),

    # #################### 后台管理 ####################
    # 用户管理
    url(r'^admin/user_management/(?P<oper_type>\w+)/(?P<o_id>\d+)/', user_management.user_management_oper),
    url(r'^admin/user_management/', user_management.user_management, name="user_management"),

    # 角色管理
    url(r'^admin/role_management/(?P<oper_type>\w+)/(?P<o_id>\d+)/', role_management.role_management_oper),
    url(r'^admin/role_management/', role_management.role_management, name="role_management"),

    # 权限管理
    url(r'^admin/auth_management/(?P<oper_type>\w+)/(?P<o_id>\d+)/', auth_management.auth_management_oper),
    url(r'^admin/auth_management/', auth_management.auth_management, name="auth_management"),

    # 财务管理
    url(r'^admin/financial_management/', financial_management.financial_management, name="financial_management"),

    # 全局设置
    url(r'^admin/global_settings/', global_settings.global_settings, name="global_settings"),

    # 提现管理
    url(r'^admin/tixian_management/(?P<oper_type>\w+)/(?P<o_id>\d+)/', tixian_management.tixian_management_oper),
    url(r'^admin/tixian_management/', tixian_management.tixian_management, name="tixian_management"),

    # 客户存活消耗统计
    url(r'^admin/kehu_cunhuo_xiaohao_tongji/(?P<oper_type>\w+)/(?P<o_id>\d+)/', kehu_cunhuo_xiaohao_tongji.kehu_cunhuo_xiaohao_tongji_oper),
    url(r'^admin/kehu_cunhuo_xiaohao_tongji/', kehu_cunhuo_xiaohao_tongji.kehu_cunhuo_xiaohao_tongji, name="kehu_cunhuo_xiaohao_tongji"),

    url(r'^account/login/', views.login, name="login"),     # 登录
    url(r'^account/logout/', views.logout, name="logout"),     # 登出
    url(r'^account/check_code/$', views.check_code, name="check_code"),     # 获取验证码
    url(r'^account/update_password/$', views.update_password, name="update_password"),     # 修改密码

    url(r'^admin/account/(?P<oper_type>\w+)/(?P<o_id>\d+)/', account.account_oper),   # 操作账户管理信息, 增删改
    url(r'^admin/account/', account.account, name="account"),  # 账户管理


    url(r'^test/', views.test),
    url(r'', views.index),
]
