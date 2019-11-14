from django.db import models


# Create your models here.
# 角色表
class Role(models.Model):
    name = models.CharField(verbose_name="角色名称", max_length=32)
    access_rules = models.CharField(verbose_name="角色对应的权限", max_length=128, default="")

    create_date = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    oper_user = models.ForeignKey("UserProfile", verbose_name="操作人", related_name="r_user",null=True,blank=True)

    tag_id = models.SmallIntegerField(verbose_name="公众号标签id", null=True, blank=True)

    class Meta:
        verbose_name_plural = "角色表"

    def __str__(self):
        return "%s" % self.name


# 权限表
class AccessRules(models.Model):
    name = models.CharField(verbose_name="权限", max_length=64)
    url_path = models.CharField(verbose_name="权限url", max_length=64, null=True, blank=True)

    super_id = models.ForeignKey('self', verbose_name="上级ID", null=True, blank=True)

    create_date = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    oper_user = models.ForeignKey("UserProfile", verbose_name="操作人", related_name="a_user")

    class Meta:
        verbose_name_plural = "权限规则表"

    def __str__(self):
        return "%s" % self.name


# 用户信息表
class UserProfile(models.Model):
    status_choices = (
        (1, "启用"),
        (2, "未启用"),
    )
    status = models.SmallIntegerField(choices=status_choices, verbose_name="状态", default=1)
    password = models.CharField(verbose_name="密码", max_length=32, null=True, blank=True)
    username = models.CharField(verbose_name="姓名", max_length=32)

    zhidao_hehuoren_website = models.CharField(verbose_name="知道合伙人主页", max_length=128, null=True, blank=True)
    xiongzhanghao_website = models.CharField(verbose_name="熊掌号主页", max_length=128, null=True, blank=True)

    role = models.ForeignKey("Role", verbose_name="角色", null=True, blank=True, related_name="userProfile_role")

    balance = models.IntegerField(verbose_name="余额", default=0)

    create_date = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    last_login_date = models.DateTimeField(verbose_name="最后登录时间", null=True, blank=True)
    oper_user = models.ForeignKey("self", verbose_name="操作人", related_name="u_user", null=True, blank=True)

    token = models.CharField(verbose_name="token值", max_length=32, null=True, blank=True)

    xie_wenda_money = models.SmallIntegerField(verbose_name="写问答收益", null=True, blank=True)
    fa_wenda_money = models.SmallIntegerField(verbose_name="发问答收益", null=True, blank=True)

    tixian_name = models.TextField(verbose_name="提现信息", default='')
    tixian_zhanghao = models.TextField(verbose_name="提现信息", default='')

    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    guwen = models.ForeignKey("self", related_name="guwen_user", null=True)  # 营销顾问
    xiaoshou = models.ForeignKey("self", related_name="xiaoshou_user", null=True)  # 销售

    map_search_keywords = models.CharField(verbose_name="百度知道地图搜索关键词", max_length=64)
    map_match_keywords = models.CharField(verbose_name="百度知道地图匹配关键词", max_length=64)
    move_map_coordinate = models.CharField(verbose_name="移动地图坐标", max_length=64, null=True, blank=True)

    weixin_id = models.CharField(verbose_name="企业微信id", max_length=32, null=True, blank=True)
    openid = models.CharField(verbose_name="微信公众号id", max_length=32, null=True, blank=True)

    # 指定首页关键词功能中覆盖报表
    keywords_top_page_cover_excel_path = models.CharField(verbose_name="指定首页关键词覆盖报表", max_length=128, null=True,
                                                          blank=True)

    # 营销顾问能够直接上传的报表
    keywords_top_page_cover_yingxiao_excel_path = models.CharField(verbose_name="营销顾问能够直接上传的报表", max_length=128,
                                                                   null=True, blank=True)

    # 该客户的任务打回编辑是否显示
    task_edit_show = models.BooleanField(verbose_name="是否显示打回的任务", default=True)  # 默认显示

    # 该客户老问答是否正常返公众号报表
    send_statement = models.BooleanField(verbose_name="是否正式返报表", default=True)

    laowenda_youxian = models.BooleanField(verbose_name="老问答优先处理", default=False)

    shangwutong_url = models.CharField(verbose_name="商务通地址", max_length=128, null=True, blank=True)

    jifei_start_date = models.DateField(verbose_name="计费开始时间", null=True, blank=True)
    jifei_stop_date = models.DateField(verbose_name="计费结束时间", null=True, blank=True)

    fugai_youxian_choices = (
        (1, "默认查询"),
        (2, "优先查询"),
    )
    fugai_youxian = models.SmallIntegerField(verbose_name="覆盖优先查", choices=fugai_youxian_choices, default=1)

    xinlaowenda_status_choices = (
        (1,'新问答'),
        (2,'老问答')
    )

    xinlaowenda_status = models.SmallIntegerField(verbose_name='用户为_新老问答',choices=xinlaowenda_status_choices,default=2)

    company_choices = (
        (1, '合众'),
        (2, '华人医院'),
    )
    company = models.SmallIntegerField(verbose_name='公司', choices=company_choices, default=1)

    partner_info = models.CharField(verbose_name='合伙人信息', max_length=128, null=True)
    def __str__(self):
        return self.username


# 登录日志
class account_log(models.Model):
    date = models.DateTimeField(verbose_name="访问时间")
    ipaddress = models.GenericIPAddressField(verbose_name="访问IP地址")
    user = models.ForeignKey("UserProfile", verbose_name="用户")


# 余额明细
class BalanceDetail(models.Model):
    user = models.ForeignKey("UserProfile", verbose_name="被操作用户", related_name="m_user", null=True, blank=True)
    type_choices = (
        (1, "充值"),
        (2, "消费"),
        (3, "收益"),
        (4, "提现"),
        (5, "退款"),
    )
    account_type = models.SmallIntegerField(verbose_name="类型", choices=type_choices)
    money = models.IntegerField(verbose_name="金额")

    balance = models.IntegerField(verbose_name="充值", default=0)  # 财务做账用
    zbalance = models.IntegerField(verbose_name="赠送", default=0)  # 财务做账用

    create_date = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    oper_user = models.ForeignKey("UserProfile", verbose_name="操作人", related_name="o_user")
    remark = models.TextField(verbose_name="备注", null=True, blank=True)


# 提现信息
class TiXian(models.Model):
    user = models.ForeignKey("UserProfile", verbose_name="提现用户")
    money = models.IntegerField(verbose_name="提现金额")

    status_choices = (
        (1, "提现中"),
        (2, "已完成"),
    )
    status = models.SmallIntegerField(choices=status_choices, verbose_name="状态", default=1)
    remark = models.TextField(verbose_name="备注", null=True, blank=True)

    create_date = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    complete_date = models.DateTimeField(verbose_name="提现完成时间", null=True, blank=True)


# 消息表
class Message(models.Model):
    user = models.ForeignKey('UserProfile', verbose_name="用户")  # 表示这条消息属于谁
    status_choices = (
        (1, '未读'),
        (2, '已读'),
    )
    status = models.SmallIntegerField(verbose_name="消息状态", choices=status_choices, default=1)
    content = models.TextField(verbose_name="消息内容")
    url = models.CharField(verbose_name="该消息点击对应的链接", max_length=64, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_at = models.DateTimeField(verbose_name="已读时间", null=True, blank=True)

    m_user = models.ForeignKey('UserProfile', verbose_name="添加消息人", related_name="message_user")  # 表示谁添加的这条消息


# 医院科室
class Department(models.Model):
    name = models.CharField(verbose_name="科室名称", max_length=32)
    parent = models.ForeignKey('self', verbose_name="父id", null=True, blank=True)


# 医院信息
class HospitalInformation(models.Model):
    user = models.ForeignKey("UserProfile")
    name = models.CharField(verbose_name="医院名称", max_length=128)
    department = models.ForeignKey("Department", verbose_name="科室")
    web_site = models.CharField(verbose_name="官网", max_length=128)

    content_direction_choices = (
        (1, "品牌口碑"),
        (2, "医院专家"),
        (3, "医院先进疗法和设备"),
    )
    content_direction = models.CharField(verbose_name="内容方向", max_length=32)
    content_direction_custom = models.CharField(verbose_name="自定义内容方向", max_length=128, null=True, blank=True)

    reply_role_choices = (
        (1, "官方回复"),
        (2, "用户角度回复"),
    )
    reply_role = models.CharField(verbose_name="表达人称角色", max_length=32)


# 任务列表
class Task(models.Model):
    release_user = models.ForeignKey("UserProfile", verbose_name="发布任务的用户", related_name="release_user")
    name = models.CharField(verbose_name="任务名称", max_length=128)

    release_platform_choices = (
        (1, "百度知道"),
        (2, "知乎"),
        (3, "宝宝树"),
        # (4, "百度口碑"),
        (5, "拇指医生(站内搜索部分问答)"),
    )
    release_platform = models.SmallIntegerField(verbose_name="发布平台", choices=release_platform_choices)

    type_choices = (
        (1, "新问答"),
        (2, "老问答"),
        (10, "新问答(补发)")
    )

    wenda_type = models.SmallIntegerField(verbose_name="问答类型", choices=type_choices)
    num = models.SmallIntegerField(verbose_name="发布数量")
    publish_ok_num = models.SmallIntegerField(verbose_name="发布成功数量", default=0)

    status_choices = (
        (1, "新发布"),
        (2, "编写问答中"),
        (3, "等待审核"),
        (4, "驳回"),
        (5, "等待分配发布人员"),
        (6, "发布问答中"),
        (7, "等待验收"),
        (10, "已完结"),
        (11, "撤销"),
    )

    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices, default=1)
    task_demand_file_path = models.CharField(verbose_name="任务需求excel表格路径", max_length=128)
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    fabu_date = models.DateTimeField(verbose_name="进入小明时间",null=True, blank=True)
    update_date = models.DateTimeField(verbose_name="更新时间", null=True, blank=True)

    receive_user = models.ForeignKey("UserProfile", verbose_name="接收任务的用户", related_name="receive_user", null=True,
                                     blank=True)
    task_result_file_path = models.CharField(verbose_name="写问答结果", max_length=128, null=True, blank=True)

    publish_user = models.ForeignKey("UserProfile", verbose_name="发布任务的用户", related_name="publish_user", null=True,
                                     blank=True)
    publish_task_result_file_path = models.CharField(verbose_name="发问答结果", max_length=128, null=True, blank=True)

    complete_date = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)

    clearing_choices = (
        (1, "未结算"),
        (2, "已结算"),
    )
    clearing = models.SmallIntegerField(verbose_name="是否结算", choices=clearing_choices, default=1)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    # yichang = models.CharField(verbose_name="异常excel表格路径", null=True, blank=True, max_length=128)
    is_yichang = models.BooleanField(verbose_name="是否异常", default=False)
    yichang_date = models.DateTimeField(verbose_name="异常统计时间", null=True, blank=True)

    is_check = models.BooleanField(verbose_name="是否检查发布问答的 excel 表格", default=False)

    remark = models.TextField(verbose_name="写问答任务说明", null=True, blank=True)
    publish_remark = models.TextField(verbose_name="发布问答任务说明", null=True, blank=True)

    add_map = models.BooleanField(verbose_name="该任务所有子任务是否添加地图", default=False)
    is_test = models.BooleanField(verbose_name="该任务是否为测试任务", default=False)
    is_shangwutong = models.BooleanField(verbose_name="是否是商务通任务", default=False)


# 任务流程日志表
class TaskProcessLog(models.Model):
    task = models.ForeignKey('Task')

    status_choices = (
        (1, "新发布"),
        (2, "分配任务"),
        (3, "编辑已提交"),  # 写问答提交
        (4, "驳回"),
        (5, "审核通过"),
        (6, "编辑已提交"),  # 发问答提交
        (7, "撤销"),
        (10, "已完结"),
        (11, "已删除"),
    )

    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices, default=1)
    remark = models.TextField(verbose_name="备注", default="")
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    oper_user = models.ForeignKey("UserProfile", verbose_name="操作用户")


# 发布问答的反链
class WendaLink(models.Model):
    task = models.ForeignKey('Task')
    url = models.URLField(verbose_name="问答反链")

    status_choices = (
        (1, "审核中"),
        (2, "正常"),
        (3, "链接失效"),
        (4, "无答案"),
        (5, "未采纳"),
        (10, "未查询"),
    )
    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices, default=1)
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_date = models.DateTimeField(verbose_name="vps 检查完提交时间", null=True, blank=True)
    check_date = models.DateTimeField(verbose_name="什么时间检查该任务状态", null=True, blank=True)


# 问答机器人任务
class WendaRobotTask(models.Model):
    task = models.ForeignKey("Task", verbose_name="关联的任务", default=None, blank=True, null=True)
    # user = models.ForeignKey("UserProfile", verbose_name="发布任务的用户", related_name="wenda_robot_task_create_user")

    title = models.CharField(verbose_name="问题", max_length=128, null=True, blank=True)
    content = models.TextField(verbose_name="答案", null=True, blank=True)
    img_src = models.TextField(verbose_name="回复答案的图片获取到的链接", null=True, blank=True)
    img_content = models.TextField(verbose_name="答案", default=True, null=True)

    wenda_url = models.CharField(verbose_name="问答的url", null=True, blank=True, max_length=128)  # 新问答的反链,或者老问答需要回答的地址

    release_platform_choices = (
        (1, "百度知道"),
        # (2, "知乎"),
        # (3, "宝宝树"),
        # (4, "百度口碑"),
        # (5, "拇指医生(站内搜索部分问答)"),
    )
    release_platform = models.SmallIntegerField(verbose_name="发布平台", choices=release_platform_choices)

    wenda_type_choices = (
        (1, "新问答"),
        (2, "老问答"),
        (10, "新问答(补发)")
    )

    wenda_type = models.SmallIntegerField(verbose_name="问答类型", choices=wenda_type_choices)

    status_choices = (
        (1, "等待发布"),  # 新问答
        (2, "等待回复"),
        (3, "等待追问"),  # 新问答等待追问
        (4, "等待追答"),  # 新问答等待追答
        (5, "等待采纳"),  # 新问答等待采纳
        (6, "已完成"),  # 新任务采纳完成, 老任务回复完成
        (20, "回复内容异常"),  # 回复内容违反了知道规范
        (22, "发布内容异常"),  # 发布内容违反了知道规范
        (30, "标题超出长度"),  # 标题超出长度
        (40, "链接失效"),  # 链接失效
        (50, "未找到采纳答案"),  # 链接失效
        (60, "发布账号异常"),  # 发布账号异常
        (70, "链接异常"),  # 链接异常,操作老问答未找到链接
    )
    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices, default=1)

    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_date = models.DateTimeField(verbose_name="更新时间", null=True, blank=True)
    next_date = models.DateTimeField(verbose_name="下次执行任务时间")

    add_map_choices = (
        (1, "添加"),
        (2, "不添加"),
    )
    add_map = models.SmallIntegerField(verbose_name="添加地图", default=2, choices=add_map_choices)

    # 记录该任务是否已经转移到任务列表中, False 表示还没有转移
    is_2_task = models.BooleanField(default=False)

    oper_num = models.SmallIntegerField(verbose_name="操作次数", default=0)

    def __str__(self):
        return self.title


# 机器人登录日志
class RobotAccountLog(models.Model):
    wenda_robot_task = models.ForeignKey("WendaRobotTask", verbose_name="问答任务")

    status_choices = (
        (1, "发布成功"),  # 新问答
        (2, "回复成功"),
        (5, "采纳成功"),  # 新问答等待采纳
        (20, "回复内容异常"),  # 回复内容违反了知道规范
        (22, "发布内容异常"),  # 发布内容违反了知道规范
        (30, "标题超出长度"),  # 标题超出长度
        (40, "链接失效"),  # 链接失效
        (50, "未找到采纳答案"),  # 链接失效
    )
    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices, default=1)

    phone_num = models.CharField(verbose_name="发布消息登录的手机号", max_length=64, null=True, blank=True)
    ipaddr = models.CharField(verbose_name="ip地址", max_length=64, null=True, blank=True)
    area = models.CharField(verbose_name="城市", max_length=64)
    login_cookie = models.TextField(verbose_name="登录的cookie", null=True, blank=True)

    lapse = models.BooleanField(verbose_name="是否失效", default=False)

    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")


# # 机器人发布统计数量
class RobotReleaseNum(models.Model):
    create_date = models.DateTimeField(verbose_name="创建时间", null=True, blank=True)
    robot_count = models.IntegerField(verbose_name='发布数量', null=True, blank=True)


# 全局设置
class GlobalSettings(models.Model):
    new_wenda_money = models.SmallIntegerField(verbose_name="新问答价格", default=25)
    old_wenda_money = models.SmallIntegerField(verbose_name="老问答价格", default=35)

    xie_wenda_money = models.SmallIntegerField(verbose_name="写问答价格", default=1)
    fa_wenda_money = models.SmallIntegerField(verbose_name="发问答价格", default=2)

    fugaibaobiao_shengcheng_moshi =models.BooleanField(verbose_name='覆盖报表生成调试模式' ,default=True )
    bianji_shifou_dianji_add_map =models.BooleanField(verbose_name='编辑是否可以添加地图' ,default=True )

# 需要查询的关键词列表
class SearchKeywordsRank(models.Model):
    client_user = models.ForeignKey(to="UserProfile", verbose_name="所属客户", related_name="search_keywords_rank_c_user")
    task = models.ForeignKey("Task", verbose_name="关联的任务", null=True, blank=True)
    keywords = models.CharField(verbose_name="关键词", max_length=128)

    type_choices = (
        (1, "指定关键词"),
        (2, "问答发布问题"),
    )

    type = models.SmallIntegerField(verbose_name="类型", choices=type_choices)
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_date = models.DateTimeField(verbose_name="更新时间", null=True, blank=True)
    z_update_date = models.DateTimeField(verbose_name="后端更新时间", null=True, blank=True)
    oper_user = models.ForeignKey("UserProfile", verbose_name="操作用户", related_name="search_keywords_rank_o_user")
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)

    class Meta:
        unique_together = ('client_user', 'keywords')



# 关键词效果
class SearchKeywordsRankLog(models.Model):
    keywords = models.ForeignKey(to='SearchKeywordsRank', verbose_name="所属关键词")
    rank = models.CharField(verbose_name="排名", max_length=64)
    create_date = models.DateField(auto_now_add=True, verbose_name="创建时间")

    type_choices = (
        (1, "PC-网页"),
        # (2, "PC-知道"),
        (3, "移动-网页"),
    )
    task_type = models.SmallIntegerField(verbose_name="类型", choices=type_choices)
    search_url = models.TextField(verbose_name="搜索链接")

    data_type_choices = (
        (1, "前端"),
        (2, "后端"),
    )
    data_type = models.SmallIntegerField(verbose_name="数据类型", default=1, choices=data_type_choices)


# 编辑内容管理
class EditContentManagement(models.Model):
    task = models.ForeignKey(to="Task", verbose_name="任务")
    client_user = models.ForeignKey(to="UserProfile", verbose_name="客户", related_name="client_user")
    create_user = models.ForeignKey(to="UserProfile", verbose_name="创建任务用户")
    reference_file_path = models.CharField(verbose_name="参考文件路径", max_length=128)

    status_choices = (
        (1, "等待分配"),
        (2, "编写中"),
        (3, "等待发布"),
        (4, "已提交"),
        (10, "撤销"),

    )

    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices)
    number = models.SmallIntegerField(verbose_name="编写数量")
    remark = models.TextField(verbose_name="任务说明")

    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    complete_date = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)


# 编辑编写任务管理
class EditTaskManagement(models.Model):
    task = models.ForeignKey(to='EditContentManagement')
    edit_user = models.ForeignKey(to="UserProfile", verbose_name="编辑用户")
    number = models.SmallIntegerField(verbose_name="编写数量")

    status_choices = (
        (1, "编写中"),
        (2, "编写完成"),
        (5, "已验收"),
    )

    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices)
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    complete_date = models.DateTimeField(verbose_name="完成时间", null=True, blank=True)


# 编辑发布任务管理
class EditPublickTaskManagement(models.Model):
    task = models.ForeignKey(to='EditTaskManagement')
    url = models.CharField(verbose_name="链接", max_length=128, null=True, blank=True)
    title = models.CharField(verbose_name="问题", max_length=128, null=True, blank=True)
    content = models.TextField(verbose_name="答案", null=True, blank=True)
    img_content = models.TextField(verbose_name="图片内容", null=True, blank=True)
    submit_num = models.SmallIntegerField(verbose_name="提交次数", default=0)

    status_choices = (
        (1, "发布中"),
        (2, "发布异常"),
        (3, "发布成功"),
        (10, "链接失效"),
        (20, "审核中"),
        (21, "正常"),
        (22, "异常"),
    )

    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices)

    is_select_cover_back = models.BooleanField('查询覆盖打回', default=False)

    remark = models.TextField(verbose_name="备注", null=True, blank=True)

    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_date = models.DateTimeField(verbose_name="更新时间", null=True, blank=True)

    run_task = models.ForeignKey(to='WendaRobotTask', verbose_name="对应发布任务表", null=True, blank=True)


class QudaoCunhuoTongji(models.Model):
    client_user = models.ForeignKey('UserProfile', verbose_name="渠道名称")
    create_date = models.DateField(auto_now_add=True, verbose_name="创建时间")
    cunhuo_num = models.IntegerField(verbose_name="存活数量")
    total_num = models.IntegerField(verbose_name="总数量")


# 编辑修改日志
class EditTaskLog(models.Model):
    edit_public_task_management = models.ForeignKey(to="EditPublickTaskManagement")
    title = models.CharField(verbose_name="问题", max_length=128, null=True, blank=True)
    content = models.TextField(verbose_name="答案")
    remark = models.TextField(verbose_name="失败原因", null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    bianji_dahui_update_choices = (
        (1, '打回'),
        (2, '修改'),
    )
    bianji_dahui_update = models.SmallIntegerField(
        verbose_name='修改or打回',
        choices=bianji_dahui_update_choices,
        default=1
    )


# 敏感词库
class SensitiveWordLibrary(models.Model):
    name = models.CharField(verbose_name="敏感词", max_length=128)
    oper_user = models.ForeignKey(to="UserProfile")
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    w_type_choices = (
        (1, "问题敏感词"),
        (2, "答案敏感词")
    )
    w_type = models.SmallIntegerField(verbose_name="敏感词类型", choices=w_type_choices, default=2)

    class Meta:
        unique_together = ('name', 'w_type')


# 问答大数据
class BigData(models.Model):
    title = models.CharField(verbose_name="问答问题", max_length=128)
    content = models.TextField(verbose_name="问答答案")
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")


# 客户覆盖数量表
class ClientCoveringNumber(models.Model):
    client = models.ForeignKey('UserProfile', verbose_name="客户")
    date = models.DateField(verbose_name="日期")
    covering_number = models.IntegerField(verbose_name="总覆盖数量")

    covering_zhiding_number_pc = models.IntegerField(verbose_name="PC指定覆盖数量")
    covering_wenti_number_pc = models.IntegerField(verbose_name="PC问题覆盖数量")

    covering_zhiding_number_wap = models.IntegerField(verbose_name="WAP指定覆盖数量")
    covering_wenti_number_wap = models.IntegerField(verbose_name="WAP问题覆盖数量")


# 客户覆盖报表中显示的数据
class ClientCoveringData(models.Model):
    client_user = models.ForeignKey('UserProfile', verbose_name="客户")
    keywords_num = models.IntegerField(verbose_name="关键词总数")
    keyword_no_select_count = models.IntegerField(verbose_name="未查询的关键词数")

    today_cover_num = models.IntegerField(verbose_name="今日覆盖")
    total_cover_num = models.IntegerField(verbose_name="总覆盖")
    total_publish_num = models.IntegerField(verbose_name="总发布次数")
    update_date = models.DateTimeField(verbose_name="更新时间", null=True, blank=True)


# 指定首页关键词
class KeywordsTopSet(models.Model):
    keyword = models.CharField(verbose_name="关键词", max_length=128)

    status_choices = (
        (1, "查询中"),
        (2, "已查询"),
        (3, "正在查询"),
    )
    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices, default=1)

    keywords_type_choices = (
        (1, "普通词"),
        (2, "核心词"),
        (3, "任务词"),
    )
    keywords_type = models.SmallIntegerField(verbose_name="关键词类型", choices=keywords_type_choices, default=1)
    top_page_cover = models.SmallIntegerField(verbose_name="首页覆盖条数", default=0)
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_date = models.DateTimeField(verbose_name="更新时间", null=True, blank=True)
    client_user = models.ForeignKey("UserProfile", verbose_name="所属用户", related_name="keywords_top_set_client_user")
    oper_user = models.ForeignKey("UserProfile", verbose_name="操作用户", related_name="keywords_top_set_oper_user")

    update_select_cover_date = models.DateTimeField(verbose_name="更新查询排名的时间", null=True, blank=True)
    get_select_date = models.DateTimeField(verbose_name="获取关键词的时间", null=True, blank=True)
    is_delete = models.BooleanField(verbose_name="是否删除", default=False)
    area = models.CharField(verbose_name="查询地区", max_length=128)
    is_shangwutong = models.BooleanField(verbose_name="是否是商务通任务", default=False)

# 记录查询关键词覆盖日志
class KeywordsSearchLog(models.Model):
    keyword = models.ForeignKey('KeywordsTopSet', verbose_name='关键词')
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    area = models.CharField(verbose_name="查询地区", max_length=128)


# 指定关键词首页数据表
class KeywordsTopInfo(models.Model):
    keyword = models.ForeignKey('KeywordsTopSet')
    title = models.CharField(verbose_name="问题", max_length=128)
    url = models.CharField(verbose_name="知道链接", max_length=128)

    page_type_choices = (
        (1, "PC端"),
        (3, "移动端"),
    )

    page_type = models.SmallIntegerField(verbose_name="页面类型", choices=page_type_choices)
    rank = models.SmallIntegerField(verbose_name="名次")
    is_caina = models.BooleanField(verbose_name="是否采纳")
    huifu_num = models.SmallIntegerField(verbose_name="回复数量")

    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", null=True, blank=True)
    update_date = models.DateTimeField(verbose_name="更新时间", null=True, blank=True)
    initial_num = models.IntegerField(verbose_name='初始数量',null=True,blank=True)
    current_number = models.IntegerField(verbose_name='当前数量',null=True,blank=True,default=0)

# 客户存活消耗统计
class KehuCunhuoXiaohaoTongji(models.Model):
    client = models.ForeignKey('UserProfile', related_name='kehu_cunhuo_xiaohao_tongji_client')
    hezuo_num = models.SmallIntegerField(verbose_name="合作数量")
    shengyu_num = models.SmallIntegerField(verbose_name="剩余量")
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    oper_user = models.ForeignKey('UserProfile', related_name='kehu_cunhuo_xiaohao_tongji_oper_user')
    remark = models.TextField(verbose_name="备注", null=True, blank=True)


class KehuCunhuoXiaohaoTongjiInfo(models.Model):
    kehu_cunhuo_xiaohao_tongji = models.ForeignKey('KehuCunhuoXiaohaoTongji')
    fabu_num = models.SmallIntegerField(verbose_name="发布量")
    jifei_num = models.SmallIntegerField(verbose_name="计费量")
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    oper_user = models.ForeignKey('UserProfile', related_name='kehu_cunhuo_xiaohao_tongji_info_oper_user')
    remark = models.TextField(verbose_name="备注", null=True, blank=True)


# 关键词覆盖报表(覆盖模式)
class KeywordsCover(models.Model):
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    keywords = models.ForeignKey("KeywordsTopSet", verbose_name="关键词")
    page_type_choices = (
        (1, "PC端"),
        (3, "移动端"),
    )
    page_type = models.SmallIntegerField(verbose_name="页面类型", choices=page_type_choices)
    rank = models.SmallIntegerField(verbose_name="名次")
    url = models.CharField(verbose_name="知道链接", max_length=128)
    is_zhedie = models.BooleanField(verbose_name="是否折叠", default=False)

    task_type_choices = (
        (1, "普通"),
        (2, "带地图")
    )
    task_type = models.SmallIntegerField(choices=task_type_choices, default=1)

    rank_type_choices = (
        (1, "普通知道排名"),
        (2, "知道合伙人排名"),
        (3, "熊掌号排名"),
    )
    rank_type = models.SmallIntegerField(verbose_name="排名类型", choices=rank_type_choices, default=1)



# 客户每天关键词覆盖数和报表
class UserprofileKeywordsCover(models.Model):
    client_user = models.ForeignKey("UserProfile", verbose_name="所属用户")
    create_date = models.DateField(verbose_name="创建时间")
    cover_num = models.IntegerField(verbose_name="总覆盖数")
    statement_path = models.CharField(verbose_name="报表路径", max_length=128)
    is_send_wechat = models.BooleanField(verbose_name="是否发送报表查询完毕的通知", default=False)
    url_num = models.SmallIntegerField(verbose_name="链接数", default=0)


# 追答完的问答通通到这里来(覆盖模式)
class TongjiKeywords(models.Model):
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    task = models.ForeignKey("Task", verbose_name="属于哪个任务", related_name='tongjikeywords__task')
    title = models.CharField(verbose_name="问题", max_length=128)
    content = models.TextField(verbose_name="答案", null=True, blank=True)
    img_src = models.TextField(verbose_name="回复答案的图片获取到的链接", null=True, blank=True)
    url = models.CharField(verbose_name="知道链接", max_length=128)

    # 该字段用来判断自己操作的老问答被删除之后好用来打回给编辑
    run_task = models.ForeignKey(to='WendaRobotTask', verbose_name="对应发布任务表", null=True, blank=True)

    is_update = models.BooleanField(verbose_name="修改中", default=False)
    update_date = models.DateTimeField(verbose_name="更新时间", null=True, blank=True)

    # 表示问答是否暂停
    is_pause = models.BooleanField(verbose_name="是否暂停", default=False)


# 知道问答
class ZhidaoWenda(models.Model):
    create_date = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    title = models.CharField(verbose_name="问题", max_length=128)
    content = models.TextField(verbose_name="答案", null=True, blank=True)
    url = models.CharField(verbose_name="知道链接", max_length=128)
    update_date = models.DateTimeField(verbose_name="更新时间", null=True, blank=True)

    status_choices = (
        (1, "未编写答案"),
        (2, "已编写答案"),
    )
    status = models.SmallIntegerField(verbose_name="状态", choices=status_choices, default=1)
    run_task = models.ForeignKey(to='WendaRobotTask', verbose_name="对应发布任务表", null=True, blank=True)

    oper_user = models.ForeignKey(to='UserProfile', verbose_name="填写答案的人", null=True, blank=True)


# 编写报表
class BianXieBaoBiao(models.Model):
    xiangmu_choices = (
        (1, "问答库"),
        (2, "养账号"),
        (3, "新问答编写"),
        (4, "老问答编写"),
        (5, "新问答打回"),
        (6, "老问答打回"),
        (7, "新问答修改"),
        (8, "老问答修改"),
    )

    xiangmu = models.SmallIntegerField(verbose_name='项目', choices=xiangmu_choices)
    oper_user = models.ForeignKey(to='UserProfile', verbose_name="编辑", null=True, blank=True)
    create_date = models.DateField(verbose_name="创建时间")
    edit_count = models.IntegerField(verbose_name='编写数量')


# 营销顾问对接表 -- 外表
class YingXiaoGuWen_DuiJie(models.Model):
    market = models.ForeignKey(to='UserProfile',verbose_name='销售', null=True, blank=True)
    kehu_username = models.ForeignKey(to='UserProfile',verbose_name='客户名称',related_name='guwenduijie_kehuming', null=True, blank=True)
    guwen_duijie_bianji = models.ManyToManyField(to='UserProfile',verbose_name='编辑',related_name='guwen_duijie_bianji')
    shiji_daozhang = models.IntegerField(verbose_name='实际到账钱数',null=True, blank=True)

    daokuan_time = models.DateField(verbose_name='到款时间',null=True, blank=True)
    jifeishijian_start = models.DateField(verbose_name='开始计费时间',null=True, blank=True)
    jifeishijian_stop = models.DateField(verbose_name='停止计费时间',null=True, blank=True)
    fugai_count = models.IntegerField(verbose_name='覆盖总数',null=True, blank=True)
    xinwenda = models.BooleanField(verbose_name='是否操作新问答',default=False)
    xuanchuanyaoqiu = models.TextField(verbose_name='宣传要求',null=True, blank=True)
    shangwutong = models.TextField(verbose_name='商务通',null=True, blank=True)
    wenda_geshu = models.IntegerField(verbose_name='新问答个数',null=True, blank=True)


# 营销顾问对接表--内表
class YingXiaoGuWen_NeiBiao(models.Model):
    shiji_daozhang = models.IntegerField(verbose_name='实际到账钱数',null=True, blank=True)
    fugai_count = models.IntegerField(verbose_name='覆盖总数', null=True, blank=True)
    daokuan_time = models.DateField(verbose_name='客户到款日期', null=True, blank=True)
    jifeishijian_start = models.DateField(verbose_name='开始计费时间', null=True, blank=True)
    jifeishijian_stop = models.DateField(verbose_name='停止计费时间', null=True, blank=True)
    xinwenda = models.BooleanField(verbose_name='是否操作新问答', default=False)
    guishu = models.ForeignKey(to='YingXiaoGuWen_DuiJie',verbose_name='外键ID',null=True, blank=True)

# 关键词截屏  --  保存图片路径
class Fifty_GetKeywordsJiePing(models.Model):
    picture_path = models.TextField(verbose_name='图片路径',null=True,blank=True)
    guanjianci = models.ForeignKey(to='Fifty_GuanJianCi',verbose_name='属于哪个关键词')


# 关键词截屏  --  保存50个关键词
class Fifty_GuanJianCi(models.Model):
    guanjianci = models.TextField(verbose_name='五十个关键词',null=True, blank=True)
    yonghu_user = models.ForeignKey(to='UserProfile',verbose_name='归属哪个用户')
    jieping_time = models.DateTimeField(verbose_name='截屏时间', null=True, blank=True)
    create_time = models.DateField(auto_now_add=True,verbose_name='创建时间', null=True, blank=True)
    is_pandaun =  models.BooleanField(verbose_name='判断是否有截屏',default=False)
    capture_status = {
        (1,'有截屏'),
        (2,'无截屏'),
    }
    have_not_capture = models.SmallIntegerField(verbose_name='有无截屏',choices=capture_status,null=True,blank=True,default=2)

# 指定关键词--优化
class KeyWords_YouHua(models.Model):
    username = models.ForeignKey(to='UserProfile',verbose_name='用户名',null=True,blank=True)
    status_choices = {
        (1,"查询中"),
        (2,"已查询")
    }
    koywords_status = models.SmallIntegerField(verbose_name='关键词状态',choices=status_choices,null=True,blank=True)
    keywords_num = models.IntegerField(verbose_name='关键词总数',null=True,blank=True)
    total_cover = models.IntegerField(verbose_name='总覆盖',null=True,blank=True)
    pc_cover = models.IntegerField(verbose_name='移动端覆盖',null=True,blank=True)
    wap_cover = models.IntegerField(verbose_name='移动端覆盖',null=True,blank=True)
    no_select_keywords_num = models.IntegerField(verbose_name='未查询关键词总数',null=True,blank=True)
    keywords_top_page_cover_excel_path = models.CharField(verbose_name='客户下载报表路径',max_length=256)
    keywords_top_page_cover_yingxiao_excel_path = models.CharField(verbose_name='顾问下载报表路径',max_length=256)

# 我的客户
class My_Client_User(models.Model):
    client_user_name = models.ForeignKey(to=UserProfile,verbose_name='客户名称',null=True,blank=True)
    create_time = models.DateField(auto_now_add=True,verbose_name='创建时间')
    remark_beizhu = models.TextField(verbose_name='备注',null=True,blank=True)

# 我的客户- - -日志表
class My_Client_User_Log(models.Model):
    guishu_user = models.ForeignKey(to=UserProfile,verbose_name='归属哪个用户的日志',null=True,blank=True)
    update_time = models.DateTimeField(verbose_name='修改时间',null=True,blank=True)
    client_log = models.CharField(verbose_name='日志',null=True,blank=True,max_length=128)
    shijian_xinxi_yuan = models.TextField(verbose_name='事件信息原数据',null=True,blank=True)
    shijian_xinxi_xian = models.TextField(verbose_name='事件信息现数据',null=True,blank=True)


# 合伙人发布的地址
class HehuorenPublishLink(models.Model):
    url = models.CharField(verbose_name="合伙人回答过的链接", max_length=128)
    user = models.ForeignKey(verbose_name="那个客户", to='UserProfile')
    create_time = models.DateField(auto_now_add=True, verbose_name='创建时间')






