from flask import current_app, render_template, session

from Info.constants import CLICK_RANK_MAX_NEWS
from Info.models import User, News
from Info.modules.home import home_blu


# 2.使用蓝图来装饰路由
@home_blu.route('/')
def index():
    # 判断用户是否登陆
    user_id = session.get("user_id")
    user = None  # 当某些极端情况下，user_id没有值，这样从库里就取不出数据，但是模板渲染里仍要传值，这时需要相当于对user进行初始化
    if user_id:
        # 根据user_id查询用户模型
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)
    # 将用户登陆信息传到模板中
    user = user.to_dict() if user else None  # 三元运算，将user模型中的数据进行字典中的封装（如果user存在进行to_dict()操作，否则user为none）

    # 查询新闻 按照点击量的倒序排列 取前10条
    rank_list = []
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(CLICK_RANK_MAX_NEWS).all()
    except Exception as e:
        current_app.logger.error(e)

    rank_list = [news.to_basic_dict() for news in rank_list]

    return render_template("index.html", user=user, rank_list=rank_list)  # 不能直接对其中的user=user.todict()，因为user可能为none，这样会报错


# 设置图标（浏览器只会请求一次，不管是否请求到之后都不会请求了）
@home_blu.route('/favicon.ico')
def favicon():
    # send_static_file用于返回静态文件（详细见day08个人笔记）
    return current_app.send_static_file("news/favicon.ico")