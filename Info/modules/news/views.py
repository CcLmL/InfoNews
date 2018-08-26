from flask import current_app, abort, render_template

from Info.models import News
from Info.modules.news import news_blu


# 显示新闻详情页
@news_blu.route('/<int:news_id>')
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
    # 将模型数据传到模板中
    return render_template("detail.html", news=news.to_dict())
