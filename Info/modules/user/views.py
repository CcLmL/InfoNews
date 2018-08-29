from flask import g, redirect, render_template

from Info.common import user_login_data
from Info.modules.user import user_blu


# 显示个人中心
@user_blu.route('/user_info')
@user_login_data
def user_info():
    user = g.user
    if not user:
        return redirect("/")

    user = user.to_dict() if user else None
    return render_template("news/user.html", user=user)
