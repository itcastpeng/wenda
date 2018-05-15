from django import forms

from webadmin import models

# 修改计费信息
class jifeiupdateForm(forms.Form):
    xiugaijifeiriqistart = forms.DateField(
        required=True,
        error_messages={
            'required': "开始时间不能为空"
        }
    )
    xiugaijifeiriqistop = forms.DateField(
        required=True,
        error_messages={
            'required': '结束时间不能为空'
        })



