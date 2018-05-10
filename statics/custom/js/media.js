/**
 * Created by congzhang on 17/6/7.
 */


(function ($) {
    $('#dataTable').DataTable({
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
        "ajax": "/cover/media/?type=ajax_json", // ajax 取数据
        "aaSorting": [
            [6, "desc"]
        ], // 默认排序

        "columns": [
            {
                "data": "id",
                "orderable": false  // 禁止排序
            },
            {
                "data": "media_name",
                "orderable": false  // 禁止排序
            },
            {
                "data": "media_url",
                "orderable": false  // 禁止排序
            },
            {
                "data": "now_time",
                "orderable": false  // 禁止排序
            },
            {
                "data": "spider_num"
            },
            {
                "data": "include_num"
            },
            {
                "data": "pc_cover"
            },
            {
                "data": "wap_cover"
            }

        ],
        "columnDefs": [
            {
              "targets": [0, 2, 3, 4, 5, 6, 7],     // 这些列禁止搜索
              "searchable": false
            }
        ]

    });
})((jQuery));
