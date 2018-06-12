from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse

# Create your views here.


from webadmin.views_dir import pub
from webadmin.forms import account
from webadmin import models
import datetime
import random
from io import BytesIO
from webadmin.views_dir.include.check_code import create_validate_code
import base64
import os
import time
import json

from webadmin.forms import account
from webadmin.modules import WeChat


@pub.is_login
def index(request):
    user_id = request.session['user_id']
    role_id = request.session['role_id']
    user_profile_obj = models.UserProfile.objects.get(id=user_id, is_delete=False)
    openid = user_profile_obj.openid

    get_msg_role_ids = [
        1,      # 超级管理员
        4,      # 管理员
        13,     # 内部编辑
        5,      # 问答客户
        12      # 销售
    ]  # 关注公众号的角色
    if not openid and user_profile_obj.role.id in get_msg_role_ids:
        we_chat_public_send_msg_obj = WeChat.WeChatPublicSendMsg()
        qc_code_url = we_chat_public_send_msg_obj.generate_qrcode(user_id)

    if "_pjax" in request.GET:
        return render(request, 'index_pjax.html', locals())

    login_count = models.account_log.objects.filter(user_id=user_id).count()
    return render(request, 'index.html', locals())


# 登录
def login(request):
    if request.method == "POST":
        response = pub.BaseResponse()

        form_obj = account.LoginForm(request.POST)
        if form_obj.is_valid():

            print(dict(request.session))
            if request.POST.get("check_code").lower() != request.session['code_CheckCode'].lower():  # 判断输入的验证码是否正确
                response.status = False
                response.error['check_code'] = "验证码不正确"
            else:
                user_profile_objs = models.UserProfile.objects.filter(
                    username=form_obj.cleaned_data["username"],
                    password=form_obj.cleaned_data["password"],
                    is_delete=False
                )

                if user_profile_objs:
                    user_profile_obj = user_profile_objs[0]
                    if user_profile_obj.status == 1:

                        response.status = True

                        request.session['username'] = user_profile_obj.username
                        request.session['user_id'] = user_profile_obj.id
                        request.session['role_id'] = user_profile_obj.role.id
                        request.session['is_login'] = True

                        access_date = datetime.datetime.now()
                        user_profile_obj.last_login_date = access_date
                        user_profile_obj.save()

                        models.account_log.objects.create(
                            date=access_date,
                            ipaddress=pub.get_ip(request),
                            user_id=user_profile_obj.id
                        )

                    else:
                        response.status = False
                        response.error['check_code'] = "该用户状态异常, 请联系营销顾问"

                else:
                    response.status = False
                    response.error['check_code'] = "账号或密码不正确"


        else:
            response.status = False
            for i in ["check_code", "username", "password"]:
                if i in form_obj.errors:
                    response.error[i] = json.loads(form_obj.errors.as_json())[i][0]["message"]
                    break

        return JsonResponse(response.__dict__)

    return render(request, 'login.html', locals())


# 登出
def logout(request):
    request.session.clear()
    return redirect('/account/login/')


# 验证码
def check_code(request):
    stream = BytesIO()
    img, code = create_validate_code()
    img.save(stream, 'PNG')
    request.session['code_CheckCode'] = code
    return HttpResponse(stream.getvalue())


def test(request):

    # ffmpeg -i 20171018_刘坤在诸葛分享.mov -strict -2 -s 1024*768 o1.mp4      // 转换
    # ffmpeg -i o1.mp4 -y -f image2 -ss 8 -t 0.001 -s 1024*768 test.jpg     // 获取图片

    # return render(request, 'test.html')
    return HttpResponse('dfdfdsfsd')


def img_upLoad(request):
    return HttpResponse('x')


# 图片上传
@pub.is_login
def img_upLoad(request):
    response = pub.BaseResponse()
    imgBase = request.POST.get('imgBase')
    imgFormat = request.POST.get('imgFormat')
    lookIndex = request.POST.get('lookIndex')

    imgdata = base64.b64decode(imgBase.split(',')[1])
    img_name = str(int(time.time() * 1000000)) + '.' + imgFormat
    img_abs_name = os.path.join("statics/upload_images", img_name)
    with open(img_abs_name, "wb") as f:
        f.write(imgdata)

    response.status = True
    response.ind = lookIndex
    response.img_url = '/' + img_abs_name
    return JsonResponse(response.__dict__)


# 修改密码
@pub.is_login
def update_password(request):
    user_id = request.session['user_id']
    response = pub.BaseResponse()
    if request.method == "POST":
        oldPwd = request.POST.get('oldPwd')
        newPwd = request.POST.get('newPwd')

        old_password = pub.str_encrypt(oldPwd)

        user_profile_objs = models.UserProfile.objects.filter(id=user_id, password=old_password, is_delete=False)
        if user_profile_objs:
            user_profile_obj = user_profile_objs[0]
            user_profile_obj.password = pub.str_encrypt(newPwd)
            user_profile_obj.save()
            response.status = True
            response.message = "修改成功"
        else:
            response.status = False
            response.message = "旧密码不正确"

    return JsonResponse(response.__dict__)
