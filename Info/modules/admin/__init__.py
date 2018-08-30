from flask import Blueprint

admin_blu = Blueprint("admin", __name__, url_prefix="/admin")


# 使用蓝图的请求钩子(只要访问该蓝图注册的路由,都会被钩子拦截),对后台访问进行控制
@admin_blu.before_request
def check_superuser():
    # 判断是否登陆管理员
    is_admin = session.get("is_admin")
    # 如果没有后台登陆 且不是访问后台登陆页面,则重定向到前台首页
    if not is_admin and not request.url.endswith("admin/login"):  # 在没有登陆的情况下,只要不是进入后台登陆界面都会被重定向回首页
        return redirect("/")


from .views import *
