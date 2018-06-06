import sys
import datetime
import os
from django.db.models import Q, Count
project_dir = os.path.dirname(os.path.dirname(os.getcwd()))
sys.path.append(project_dir)
print(project_dir)
os.environ['DJANGO_SETTINGS_MODULE'] ='wenda.settings'
import django
django.setup()
from webadmin import models
from webadmin.modules.WeChat import WeChatPublicSendMsg


# 调用发送微信公众号模块
wechat_date = './wechat_data.json'
webchat_obj = WeChatPublicSendMsg(wechat_date)
now_date = datetime.datetime.today().strftime('%Y-%m-%d')
# 判断日期满足日期的查出来
seventime = datetime.date.today() + datetime.timedelta(days=7)
q = Q()
q.add(Q(guwen__isnull=False) | Q(xiaoshou__isnull=False), Q.AND)
q.add(Q(jifei_stop_date__lt=seventime) & Q(is_delete=False) & Q(status=1) & Q(jifei_start_date__isnull=False) & Q(jifei_stop_date__isnull=False), Q.AND)
# q.add(Q(jifei_stop_date__lte=seventime) & Q(is_delete=False) & Q(status=1) & Q(jifei_start_date__isnull=False) & Q(jifei_stop_date__isnull=False) & Q(create_date__gte=now_date), Q.AND)


# 公用判断日期
def gonggong_weixin():
    objs = models.UserProfile.objects.filter(q)
    # print('objs ---> ',objs )
    if objs:
        data_list = []
        for obj in objs:
            now_date = datetime.datetime.now()
            if obj.jifei_stop_date > datetime.date.today():
                # 今天到期
                if obj.jifei_stop_date == datetime.date.today():
                    data_list.append({
                        'xiaoshouopenid': obj.xiaoshou.openid,
                        'xiaoshou_id': obj.xiaoshou_id,
                        'guwen_id':obj.guwen_id,
                        'guwenopenid':obj.guwen.openid
                    })

                if now_date.strftime('%Y-%m-%d') >= (obj.jifei_stop_date - datetime.timedelta(days=7)).strftime('%Y-%m-%d'):
                    data_time = obj.jifei_stop_date - datetime.date.today()
                    # 还有七天到期
                    if data_time <= datetime.timedelta(days=7):
                        data_list.append({
                            'xiaoshouopenid': obj.xiaoshou.openid,
                            'xiaoshou_id': obj.xiaoshou_id,
                            'guwen_id': obj.guwen_id,
                            'guwenopenid': obj.guwen.openid
                        })
            # 已到期
            else:
                if obj.jifei_stop_date < datetime.date.today():
                    pass
        return data_list


# 公用发送链接
def gongyong(openid,gongyong_id):
    post_data = {
        "touser": "o7Xw_0fq6LrmCjBbxAzDZHTbtQ3g",
        # "touser": "{openid}".format(openid=openid),
        "template_id": "ksNf6WiqO5JEqd3bY6SUqJvWeL2-kEDqukQC4VeYVvw",
        "url": "http://wenda.zhugeyingxiao.com/api/jifeidaoqitixing/null/{gongyong_id}".format(gongyong_id=gongyong_id),
        # "url": "http://127.0.0.1:8006/api/jifeidaoqitixing/null/{gongyong_id}".format(gongyong_id=gongyong_id),
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
        }
    }
    print('post_data', post_data['url'])
    print('---------========================')
    webchat_obj.sendTempMsg(post_data)


# 发送顾问链接
def guwen_weixin():
    data_list = gonggong_weixin()
    data_dict = {}
    if data_list:
        print('objs - - -> ',data_list )
        for obj in data_list:
            guwen_openid = obj['guwenopenid']
            guwen_id = obj['guwen_id']
            data_dict[guwen_id] = guwen_openid
        for guwen_id, guwen_openid in data_dict.items():
            print('guwen _ id ', guwen_openid, guwen_id)
            gongyong(guwen_openid, guwen_id)


# 发送销售链接
def xiaoshou_weixin():
    data_list = gonggong_weixin()
    data_dict = {}
    if data_list:
        for obj in data_list:
            xiaoshou_openid = obj['xiaoshouopenid']
            xiaoshou_id = obj['xiaoshou_id']
            data_dict[xiaoshou_id] = xiaoshou_openid
        for xiaoshou_id, xiaoshou_openid in data_dict.items():
            print('guwen _ id ', xiaoshou_openid, xiaoshou_id)
            gongyong(xiaoshou_openid, xiaoshou_id)








