$(function() {
    var source = $("#pagination").attr('source')
    var cur_page = $("#pagination").attr('cur_page')
    var total_page = $("#pagination").attr('total_page')
    $("#pagination").pagination({
        currentPage: parseInt(cur_page),
        totalPage: parseInt(total_page),
        callback: function(current) {
            location.href = source + "?p=" + current  //这里会发出对应页的请求即:http:127.0.0.1:5000/admin/user_list?p=XX
        }
    });
});