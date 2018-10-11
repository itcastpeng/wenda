from django.db.models import Count, Q
import datetime
from webadmin import models
from webadmin.views_dir import pub
from django.http import JsonResponse

from django.db.models import Count, Sum


def celery_apiFuGaiBaoBiaoUpdate(request):
    response = pub.BaseResponse()
    now_date = datetime.datetime.now().strftime("%Y-%m-%d")
    data_objs = models.KeywordsCover.objects.select_related(
        # "keywords__client_user",
        "keywords",
    ).values(
        # .filter(
        #     create_date__gte=now_date
        # )
        # "keywords__client_user__username",
        "keywords__client_user_id",
    ).annotate(Count('id'))

    print(data_objs)

    for obj in data_objs:
        client_user_id = obj['keywords__client_user_id']

        # 总覆盖数
        total_cover_num = 0
        userprofile_keywords_cover_objs = models.UserprofileKeywordsCover.objects.filter(
            client_user_id=client_user_id
        ).values('create_date', 'cover_num').annotate(Count('cover_num'))

        for userprofile_keywords_cover_obj in userprofile_keywords_cover_objs:
            total_cover_num += userprofile_keywords_cover_obj['cover_num']

        # if client_user_id == 140:  # 西宁东方泌尿专科 删除词了,之前对应的覆盖也删除了,单独处理
        #     userprofile_keywords_cover_objs = models.UserprofileKeywordsCover.objects.filter(
        #         client_user_id=client_user_id)
        #     for userprofile_keywords_cover_obj in userprofile_keywords_cover_objs:
        #         total_cover_num += userprofile_keywords_cover_obj.cover_num
        #
        # else:
        #     total_cover_num = obj['id__count']
            # objs = models.UserprofileKeywordsCover.objects.filter(client_user_id=obj['keywords__client_user_id'])
            # for obj in objs:
            #     total_cover_num += obj.cover_num

        keywords_topset_obj = models.KeywordsTopSet.objects.filter(
            client_user_id=obj["keywords__client_user_id"],
            is_delete=False
        )

        # 关键词总数
        keyword_count = keywords_topset_obj.count()

        now_date = datetime.datetime.now().strftime("%Y-%m-%d")

        # 今日覆盖数
        today_cover_num = models.KeywordsCover.objects.filter(
            keywords__client_user_id=client_user_id,
            create_date__gte=now_date
        ).count()

        if client_user_id == 285:  # 晓嘉容艺术中心 覆盖量太多减少到200-300之间
            # today_cover_num = randint(150,400)
            num_objs = models.UserprofileKeywordsCover.objects.filter(
                client_user_id=client_user_id,
                create_date__gte=now_date
            )
            if num_objs:
                today_cover_num = num_objs[0].cover_num

        # 总发布次数
        total_publish_num = models.RobotAccountLog.objects.filter(
            wenda_robot_task__task__release_user_id=client_user_id,
            wenda_robot_task__wenda_type=2
        ).count()

        q = Q(Q(update_select_cover_date__isnull=True) | Q(update_select_cover_date__lt=now_date))

        # 未查询的关键词数
        keyword_no_select_count = keywords_topset_obj.filter(q).count()

        data = {
            "keywords_num": keyword_count,
            "keyword_no_select_count": keyword_no_select_count,
            "today_cover_num": today_cover_num,
            "total_cover_num": total_cover_num,
            "total_publish_num": total_publish_num,
            "update_date": datetime.datetime.now()
        }

        client_covering_data_objs = models.ClientCoveringData.objects.filter(client_user_id=client_user_id)
        if client_covering_data_objs:
            client_covering_data_objs.update(**data)
        else:
            data['client_user_id'] = client_user_id
            models.ClientCoveringData.objects.create(**data)

    response.code = 200
    return JsonResponse(response.__dict__)