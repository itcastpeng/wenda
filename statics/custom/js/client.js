/**
 * Created by congzhang on 17/6/7.
 */

(function ($) {
    
    /* 格式化详情功能 - 根据需要修改 */
    function format(d) {
        // `d` 是该行的原始数据对象
        //cellpadding="5"

        var url = "/cover/client/domain/select/" + d.id + '/';

        $.ajaxSetup({
            async : false
        });
        $.get(url, function (data) {
            result = data;
        });

        return result

    }


    var table = $('#dataTable').DataTable({
        language: {
            "sProcessing": "处理中...",
            "sLengthMenu": "每页显示 _MENU_ 条",
            "sZeroRecords": "没有匹配结果",
            "sInfo": "第 _START_ 至 _END_ 项，共 _TOTAL_ 项",
            "sInfoEmpty": "第 0 至 0 项，共 0 项",
            "sInfoFiltered": "",
            "sInfoPostFix": "",
            "sSearch": "搜索:",
            "sUrl": "",
            "sEmptyTable": "表中数据为空",
            "sLoadingRecords": "载入中...",
            "sInfoThousands": ",",
            "oPaginate": {
                "sFirst": "首页",
                "sPrevious": "上页",
                "sNext": "下页",
                "sLast": "末页"
            },
            "oAria": {
                "sSortAscending": ": 以升序排列此列",
                "sSortDescending": ": 以降序排列此列"
            }
        },
        "processing": true,
        "serverSide": true,  // 服务器模式
        "ajax": "/cover/client/?type=ajax_json", // ajax 取数据
        "aaSorting": [
            [5, "desc"]
        ], // 默认排序

        "columns": [
            {
                "class": 'details-control',
                "orderable": false,
                "data": null,
                "defaultContent": ''
            },
            {
                "data": "id",
                "orderable": false,  // 禁止排序
                "visible": false   // 隐藏该列

            },
            {
                "data": "client_id",
                "orderable": false  // 禁止排序
            },
            {
                "data": "client_name",
                "orderable": false  // 禁止排序
            },
            {
                "data": "now_time",
                "orderable": false  // 禁止排序
            },
            {"data": "pc_cover"},
            {"data": "wap_cover"},
            {
                "data": "options",
                "orderable": false  // 禁止排序
            }

        ],
        "columnDefs": [
            {
              "targets": [0, 1, 2, 4, 5, 6],     // 这些列禁止搜索
              "searchable": false
            }
        ]
    });


    // 展开关闭详情时的事件监听
    $('#dataTable tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        if (row.child.isShown()) {
            // 本行已展开
            row.child.hide();
            tr.removeClass('shown');
        }
        else {
            // 展开本行
            row.child(format(row.data())).show();
            tr.addClass('shown');
        }
    });

    $("#table_client_edit").on("hidden.bs.modal", function() {
        $(this).removeData("bs.modal");
        $(this).find(".modal-content").children().remove();
    });

})(jQuery);
