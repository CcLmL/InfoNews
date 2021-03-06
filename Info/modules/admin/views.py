import time
from datetime import datetime, timedelta

from flask import request, render_template, current_app, redirect, url_for, session, g, jsonify, abort

from Info.common import user_login_data
from Info.constants import USER_COLLECTION_MAX_NEWS, QINIU_DOMIN_PREFIX
from Info.models import User, News, Category
from Info.modules.admin import admin_blu


# 后台登陆
from Info.utils.image_storage import upload_img
from Info.utils.response_code import RET, error_map


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


# 用户统计
@admin_blu.route('/user_count')
def user_count():
    # 用户总数
    total_count = 0
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 月新增人数
    mon_count = 0
    # 获取本地日期
    t = time.localtime()
    # 先构建日期字符串
    date_mon_str = "%d-%02d-01" % (t.tm_year, t.tm_mon)
    # 日期字符串可以转为日期对象
    date_mon = datetime.strptime(date_mon_str, "%Y-%m-%d")
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= date_mon).count()
    except Exception as e:
        current_app.logger.error(e)

    # 日新增人数
    day_count = 0
    # 先构建日期字符串
    date_day_str = "%d-%02d-%2d" %(t.tm_year, t.tm_mon, t.tm_mday)
    # 日期字符串可以转为日期对象
    date_day = datetime.strptime(date_day_str, "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time >= date_day).count()
    except Exception as e:
        current_app.logger.error(e)

    # 获取日活跃人数(每日的登录人数)
    active_count = []
    active_time = []
    try:
        for i in range(30):
            begin_date = date_day - timedelta(days=i)
            end_date = date_day + timedelta(days=1-i)
            # 查询登录时间 >= 某日0点, < 次日0点
            one_day_count = User.query.filter(User.is_admin == False, User.last_login >= begin_date, User.last_login < end_date).count()
            active_count.append(one_day_count)
            # 将日期对象转为日期字符串
            one_day_str = begin_date.strftime("%Y-%m-%d")
            active_time.append(one_day_str)
    except Exception as e:
        current_app.logger.error(e)

    active_time.reverse()
    active_count.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }

    return render_template("admin/user_count.html", data=data)


# 显示用户列表
@admin_blu.route('/user_list')
def user_list():
    page = request.args.get("p", 1)

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 将当前用户的所有收藏传到模板中
    user_list = []
    total_page = 1
    try:
        pn = User.query.filter(User.is_admin == False).paginate(page, USER_COLLECTION_MAX_NEWS)
        user_list = pn.items
        total_page = pn.pages
    except Exception as e:
        current_app.logger.error(e)

    data = {
        "user_list": user_list,
        "cur_page": page,
        "total_page": total_page
    }

    return render_template("admin/user_list.html", data=data)


# 显示新闻待审核列表
@admin_blu.route('/news_review')
def news_review():
    page = request.args.get("p", 1)
    keyword = request.args.get("keywords")

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 将所有用户发布的新闻传到模板中
    news_list = []
    total_page = 1
    filter_list = [News.user_id != None]
    if keyword:
        filter_list.append(News.title.contains(keyword))

    try:
        pn = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(page, USER_COLLECTION_MAX_NEWS)
        news_list = pn.items
        total_page = pn.pages
    except Exception as e:
        current_app.logger.error(e)

    data = {
        "news_list":[news.to_dict() for news in news_list],
        "cur_page": page,
        "total_page": total_page
    }

    return render_template("admin/news_review.html", data=data)


# 显示待审核详情
@admin_blu.route('/news_review_detail<int:news_id>')
def news_review_detail(news_id):
    # 根据新闻id查询新闻
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return abort(404)

    if not news:
        return abort(404)

    return render_template("admin/news_review_detail.html", news=news.to_dict())


# 可以跟上面的路由合并
@admin_blu.route('/news_review_action', methods=["POST"])
def news_review_action():
    # 获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")
    reason = request.json.get("reason")
    # 校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        news_id = int(news_id)
    except Exception as e:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if action not in ["accept", "reject"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not news:
        return jsonify(errno=RET.NODATA, errmsg=error_map[RET.NODATA])

    # 根据action,修改news模型
    if action == "accept":
        news.status = 0
    else:
        news.status = -1
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
        news.reason = reason

    # 返回json
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])
    
    
# 显示新闻版式列表
@admin_blu.route('/news_edit')
def news_edit():
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords")

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 将所有的审核通过的新闻传到模板中
    news_list = []
    total_page = 1
    filter_list = [News.status == 0]
    if keywords:
        filter_list.append(News.title.contains(keywords))

    try:
        pn = News.query.filter(*filter_list).paginate(page, USER_COLLECTION_MAX_NEWS)
        news_list = pn.items
        total_page = pn.pages
    except Exception as e:
        current_app.logger.error(e)

    data = {
        "news_list": [news.to_review_dict() for news in news_list],
        "cur_page": page,
        "total_page": total_page
    }

    return render_template("admin/news_edit.html", data=data)


# 显示版式编辑详情
@admin_blu.route('/news_edit_detail', methods=["GET", "POST"])
def news_edit_detail():
    if request.method == "GET":
        # 获取参数
        news_id = request.args.get("news_id")
        # 校验参数
        try:
            news_id = int(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return abort(404)
        # 查询新闻模型
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return abort(404)

        # 将所有的类别传到模板
        categories = []
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return abort(404)
        # 标记新闻对应的类别
        categories_list = []
        for category in categories:
            is_selected = False
            category_dict = category.to_dict()
            if category.id == news.category_id:
                is_selected = True
            category_dict["is_selected"] = is_selected
            categories_list.append(category_dict)

        if len(categories_list):
            categories_list.pop(0)
        # 将模型数据传到模板中
        return render_template("admin/news_edit_detail.html", news=news.to_dict(), categories_list=categories_list)

    # POST处理
    news_id = request.form.get("news_id")
    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    index_image = request.files.get("index_image")
    content = request.form.get("content")

    if not all([news_id, title, category_id, digest, content]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 取出新闻模型
    try:
        news = News.query.get(news_id)
        category = Category.query.get(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not news or not category:
        return jsonify(errno=RET.NODATA, errmsg=error_map[RET.NODATA])

    # 修改新闻模型
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.content = content
    if index_image:
        try:
            img_bytes = index_image.read()
            file_name = upload_img(img_bytes)
            news.index_image_url = QINIU_DOMIN_PREFIX + file_name
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])
