from flask import current_app, abort, render_template, g, jsonify, request

from Info.common import user_login_data
from Info.constants import CLICK_RANK_MAX_NEWS
from Info.models import News
from Info.modules.news import news_blu


# 显示新闻详情页
from Info.utils.response_code import RET, error_map


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    # 根据新闻id来查询该新闻模型、
    news = None  # type:News
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return abort(404)  # 模板渲染时的to_dict不需要管是否为none的情况，因为这里已经进行对应的处理了

    # 让新闻的点击量+1
    news.clicks += 1

    # 查询新闻 按照点击量的倒序排列 取前10条
    rank_list = []
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS).all()
    except Exception as e:
        current_app.logger.error(e)

    rank_list = [news.to_dict() for news in rank_list]

    # 查询当前用户是否收藏了该新闻
    is_collected = False
    user = g.user
    if user:
        if news in user.collection_news:
            is_collected = True

    # 将用户登陆信息传到模板中
    user = user.to_dict() if user else None

    # 将模型数据传到模板中
    return render_template("news/detail.html", news=news.to_dict(), rank_list=rank_list, user=user,
                           is_collected=is_collected)


# 收藏/取消收藏
@news_blu.route('/news_collect',methods=["POST"])
@user_login_data
def news_collect():
    # 判断用户是否登陆
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])
    # 获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")
    # 校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        news_id = int(news_id)
    except Exception as e:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not news:
        return jsonify(errno=RET.NODATA, errmsg=error_map[RET.NODATA])

    # 根据action执行处理（新闻收藏与用户是多对多关系，user_id和new_id建立/取消关系）
    if action == "collect":  # 收藏
        if news not in user.collection_news:
            user.collection_news.append(news)
    else:  # 取消收藏
        if news in user.collection_news:
            user.collection_news.remove(news)

    # 返回json结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])