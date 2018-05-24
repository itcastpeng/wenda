import sys
import datetime
import os
from django.db.models import Q, Count

project_dir = os.path.dirname(os.path.dirname(os.getcwd()))
sys.path.append(project_dir)
print(project_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'wenda.settings'
import django

django.setup()
from webadmin import models
from webadmin.modules.WeChat import WeChatPublicSendMsg

print('执行定时任务 - - - - - -发送微信公众号')
# 调用发送微信公众号模块
webchat_obj = WeChatPublicSendMsg()

# 判断日期满足日期的查出来
seventime = datetime.date.today() + datetime.timedelta(days=7)
q = Q()
q.add(Q(guwen__isnull=False) | Q(xiaoshou__isnull=False), Q.AND)
q.add(Q(jifei_stop_date__lte=seventime) & Q(is_delete=False) & Q(status=1) & Q(jifei_start_date__isnull=False) & Q(
    jifei_stop_date__isnull=False), Q.AND)


# 公用判断日期
def gonggong_weixin():
    objs = models.UserProfile.objects.filter(q)
    for obj in objs:
        if obj:
            # 用户名
            # print('user_obj -- > ', obj)
            # 结束日期
            stop_time = obj.jifei_stop_date
            # print('stop--->', stop_time)
            now_date = datetime.datetime.now()
            if obj.jifei_stop_date == datetime.date.today():
                openid = obj.guwen.openid
            # 增加判断  已过期负数的  不加入列表
            elif obj.jifei_stop_date < datetime.date.today():
                guoqishijian = obj.jifei_stop_date - datetime.date.today()

            # 如果当前时间 大于等于 计费结束日期减去七天
            else:
                if now_date.strftime('%Y-%m-%d') >= (
                        obj.jifei_stop_date - datetime.timedelta(days=7)).strftime(
                    '%Y-%m-%d'):
                    # 用结束日期减去当前日期 剩余天数
                    data_time = obj.jifei_stop_date - datetime.date.today()
                    if data_time <= datetime.timedelta(days=7):
                        data_str = '{}还有{}天到期'.format(obj.username, data_time.days)
            return obj


# 公用发送链接
def gongyong(openid, gongyong_id):
    post_data = {
        "touser": "o7Xw_0fq6LrmCjBbxAzDZHTbtQ3g",
        # "touser": "{openid}".format(openid=openid),
        "template_id": "ksNf6WiqO5JEqd3bY6SUqJvWeL2-kEDqukQC4VeYVvw",
        "url": "http://wenda.zhugeyingxiao.com/api/jifeidaoqitixing/null/{gongyong_id}".format(
            gongyong_id=gongyong_id),
        # "url": "http://127.0.0.1:8005/api/jifeidaoqitixing/null/{gongyong_id}".format(gongyong_id=gongyong_id),
        "data": {
            "first": {
                "value": "诸葛霸屏王提醒有计费到期！",
                "color": "#000"
            },
            "keyword1": {
                "value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                # "color": "#173177"
            },
            "keyword2": {
                "value": "请见详情页面",
            },
            # "keyword3": {
            #     "value": "发布失败",
            #     "color": "#173177"
            # },
            # "keyword4": {
            #     "value": "请修改",
            #     "color": "#173177"
            # },

            # "remark": {
            #     "value":'\n' + '\n '.join(data_list),
            #     "color": "#FF0000"
            # }
        }
    }
    print('post_data', post_data['url'])
    print('---------========================')
    webchat_obj.sendTempMsg(post_data)


# 发送顾问链接
def guwen_weixin():
    obj = gonggong_weixin()
    user_objs = models.UserProfile.objects.filter(q).values(
        'guwen_id'
    ).annotate(Count('id'))
    # enumerate 索引和值
    # for index,user_obj in enumerate(user_objs):
    openid = obj.guwen.openid
    for user_obj in user_objs:
        print('user_obj - - -- - - ->', user_obj)
        print('user_obj[xiaoshou_id] - - -- - - ->', user_obj['guwen_id'])
        print('openid - - -- - - ->', openid)
        gongyong(openid, user_obj['guwen_id'])


# 发送销售链接
def xiaoshou_weixin():
    obj = gonggong_weixin()
    user_objs = models.UserProfile.objects.filter(q).values(
        'xiaoshou_id'
    ).annotate(Count('id'))
    # enumerate 索引和值
    # for index,user_obj in enumerate(user_objs):
    openid = obj.guwen.openid
    for user_obj in user_objs:
        if obj.xiaoshou.id:
            print('user_obj - - -- - - ->', user_obj)
            print('user_obj[xiaoshou_id] - - -- - - ->', user_obj['xiaoshou_id'])
            print('openid - - -- - - ->', openid)
            gongyong(openid, user_obj['xiaoshou_id'])


if __name__ == '__main__':
    guwen_weixin()
    xiaoshou_weixin()
