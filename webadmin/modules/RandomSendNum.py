#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com

"""
计算口碑任务随机发布数量
发布时间为 8:00-24:00 之间
    每天最多发布10篇,最少发布1篇
"""


import random
import datetime


def time2seconds(t):
    h, m, s = t.strip().split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def seconds2time(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


# 随机发布时间
def random_send_pub_time(date, number):
    """
    :param date:  # 日期
    :param number:  # 一天发布次数
    :return:
    """
    st = "08:00:00"
    et = "24:00:00"
    sts = time2seconds(st)      # sts==27000
    ets = time2seconds(et)      # ets==34233

    rt = random.sample(range(sts, ets), number)

    rt.sort()
    result = []
    for i in rt:
        result.append(date + " " + seconds2time(i))

    return result


# 随机每日发布数量
def random_send_num(total_num, date, max_num=10, min_num=1):
    """
    :param total_num:   总发布条数
    :param date:        发多少天
    :param max_num:        每天最多发布多少条
    :param min_num:        每天最少发布多少条
    :return:
    """

    data = {}

    # 首先先给每天设置最少发布一篇
    for i in range(date):
        day = i + 1
        now_date = (datetime.datetime.now() + datetime.timedelta(days=day)).strftime("%Y-%m-%d")
        data[now_date] = min_num

    # 然后每天增加随机篇数
    result = []
    for i in data.keys():
        use_num = sum(data.values())
        if total_num - use_num > max_num-min_num:
            random_num = random.randint(1, max_num-min_num)
        else:
            random_num = total_num - use_num

        data[i] += random_num

        result.append(
            {
                "date": i,
                "number": data[i]
            }
        )

    return result

if __name__ == '__main__':
    random_send_num(100, 20)

