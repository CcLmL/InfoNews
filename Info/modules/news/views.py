from flask import current_app, abort, render_template, g

from Info.common import user_login_data
from Info.constants import CLICK_RANK_MAX_NEWS
from Info.models import News
from Info.modules.news import news_blu


# 显示新闻详情页
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

    # 将用户登陆信息传到模板中
    user = g.user.to_dict() if g.user else None

    # 将模型数据传到模板中
    return render_template("news/detail.html", news=news.to_dict(), rank_list=rank_list, user=user)
