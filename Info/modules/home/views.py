from flask import current_app, render_template

from Info.modules.home import home_blu


# 2.使用蓝图来装饰路由
@home_blu.route('/')
def index():

    return render_template("index.html")


# 设置图标（浏览器只会请求一次，不管是否请求到之后都不会请求了）
@home_blu.route('/favicon.ico')
def favicon():
    # send_static_file用于返回静态文件（详细见day08个人笔记）
    return current_app.send_static_file("news/favicon.ico")