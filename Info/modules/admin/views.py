from flask import request, render_template, current_app, redirect, url_for, session, g

from Info.common import user_login_data
from Info.models import User
from Info.modules.admin import admin_blu


# 后台登陆
@admin_blu.route('/login', methods=["GET","POST"])
def login():
    if request.method == "GET":
        # 判断用户是否登陆
        user_id = session.get("user_id")
        is_admin = session.get("is_admin")

        if user_id and is_admin:  # 免密码登陆
            return redirect(url_for("admin.index"))

        # 渲染页面
        return render_template("admin/login.html")
    # POST处理
    username = request.form.get("username")
    password = request.form.get("password")
    if not all([username, password]):
        return render_template("admin/login.html", errmsg="用户名.密码不完整")

    # 判断该超级管理员是否存在
    try:
        user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html", errmsg="数据查询失败")

    if not user:
        return render_template("admin/login.html", errmsg="用户不存在")

    # 校验密码
    if not user.check_password(password):
        return render_template("admin/login.html", errmsg="用户名/密码错误")

    # 状态保持
    session["user_id"] = user.id
    session["is_admin"] = True

    # 跳转页面
    return redirect(url_for("admin.index"))


# 后台首页
@admin_blu.route('/index')  # 不仅后台首页,包括其中的各种网页都应该以以登陆后的状态进行访问,所以进入网站前应该先进行判断
@user_login_data
def index():
    user = g.user
    return render_template("admin/index.html", user=user.to_dict())


# 后台退出
@admin_blu.route('/logout')
def logout():
    # 将用户信息从session中删除pop可以这是默认值,当键值对不存在时,不会报错并返回默认值
    session.pop("user_id", None)  # 设置默认值,如果没有要删除的值也不会报错
    session.pop("is_admin", None)

    # 将结果返回
    return redirect(url_for("admin.login"))

