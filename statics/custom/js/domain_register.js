/**
 * Created by congzhang on 17/6/12.
 */


(function ($) {

    $("#domain_select").on('click', function () {

        $("body").append('<div class="modal-backdrop fade in" style="z-index: 2001"></div>');
        $("#domain_register_ing").addClass('in');
        $("#domain_register_ing").css('display', 'block');
        $("#domain_register_ing").css('z-index', '2002');


        var domain_num = $(".form-horizontal input[name='domain_num']").val();

        var url = "?type=get_domain&domain_num=" + domain_num;
        $.get(url, function (data) {
            // var button = '<div><button type="button" data-target="#domain_confirm_model" data-toggle="modal" id="domain_select" class="btn btn-success">确认购买以下域名</button></div>';
            $("#domain_register").html(data['data']);   // 显示需要购买的域名
            // $("#domain_confirm").html(data['data']);    // 确认购买的域名
            $("#domain_register_ing").removeClass('in');
            $("#domain_register_ing").css('display', 'none');
            $(".modal-backdrop").remove()
        }, "json")

    });


    $("#domain_buy").on('click', function () {
        var csrfmiddlewaretoken = $("body input[name='csrfmiddlewaretoken']").val();
        var data = "type=buy_domain&csrfmiddlewaretoken=" + csrfmiddlewaretoken;
        $.post('./',data, function (data) {
            if(data['status']){

            }
        })
    })


})(jQuery);
