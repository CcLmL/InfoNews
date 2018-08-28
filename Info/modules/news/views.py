from flask import current_app, abort, render_template, g, jsonify, request

from Info import db
from Info.common import user_login_data
from Info.constants import CLICK_RANK_MAX_NEWS
from Info.models import News, Comment
from Info.modules.news import news_blu


# 显示新闻详情页
from Info.utils.response_code import RET, error_map


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    # 根据新闻id来查询该新闻模型、
    news = None  # type:News
    try:
        news = News.query.get(news_id)  # get可以直接获得查询对象，因为是直接取主键对应的值
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
        if news in user.collection_news:  # 当执行了懒查询的关系属性和in连用时(if in/for in),会直接执行查询,而不需要添加all()
            is_collected = True

    # 查询该新闻的所有评论,传到模板中
    comments = Comment.query.filter(Comment.news_id == news.id).order_by(Comment.create_time.desc()).all()
    # 查询当前用户是否对某条评论点过赞
    comments_list = []
    for comment in comments:
        is_like = False
        comment_dict = comment.to_dict()
        if user:
            if comment in user.like_commments:
                is_like = True
            comment_dict["is_like"] = is_like
        # 将评论字典加入列表中
        comments_list.append(comment_dict)

    # 将用户登陆信息传到模板中
    user = user.to_dict() if user else None

    # 将模型数据传到模板中
    return render_template("news/detail.html", news=news.to_dict(), rank_list=rank_list, user=user,is_collected=is_collected, comments=comments_list)


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
        if news not in user.collection_news:  # 本质是一个AppenderQuery:官方解释为collection storage operations(一个容器)
            user.collection_news.append(news)
    else:  # 取消收藏
        if news in user.collection_news:
            user.collection_news.remove(news)

    # 返回json结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 评论/回复
@news_blu.route('/news_comment', methods=["POST"])
@user_login_data
def news_comment():
    # 判断用户是否登陆
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    # 获取参数
    comment_content = request.json.get("comment")
    news_id = request.json.get("news_id")
    parent_id = request.json.get("parent_id")

    # 校验参数
    if not all([comment_content, news_id]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 验证新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not news:
        return jsonify(errno=RET.NODATA, errmsg=error_map[RET.NODATA])

    # 创建评论模型
    comment = Comment()
    comment.content = comment_content
    comment.user_id = user.id
    comment.news_id = news.id
    if parent_id:
        try:
            parent_id = int(parent_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

        comment.parent_id = parent_id

    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # json返回数据
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=comment.to_dict())


# 点赞/取消点赞
@news_blu.route('/comment_like', methods=["POST"])
@user_login_data
def comment_like():
    # 判断用户是否登陆
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])
    # 获取参数
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")
    # 校验参数
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if action not in ['add', 'remove']:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg=error_map[RET.NODATA])

    # 根据action执行处理(user_id和comment_id建立/取消关系)
    if action == 'add':  # 点赞
        if comment not in user.like_commments:
            user.like_commments.append(comment)
            comment.like_count += 1
    else:  # 取消点赞
        if comment in user.like_commments:
            user.like_commments.remove(comment)
            comment.like_count -= 1

    # 返回json结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])




