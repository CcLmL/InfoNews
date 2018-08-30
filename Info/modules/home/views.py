from flask import current_app, render_template, session, request, jsonify

from Info.constants import CLICK_RANK_MAX_NEWS, HOME_PAGE_MAX_NEWS
from Info.models import User, News, Category
from Info.modules.home import home_blu


# 2.使用蓝图来装饰路由
from Info.utils.response_code import RET, error_map


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

    # 原html页面中各个类别是写死的，这里可以从数据库中取出值进行全局渲染
    categories = []
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)

    return render_template("news/index.html", user=user, rank_list=rank_list, categories=categories)  # 不能直接对其中的user=user.todict()，因为user可能为none，这样会报错


# 设置图标（浏览器只会请求一次，不管是否请求到之后都不会请求了）
@home_blu.route('/favicon.ico')
def favicon():
    # send_static_file用于返回静态文件（详细见day08个人笔记）
    return current_app.send_static_file("news/favicon.ico")


# 获取新闻列表
@home_blu.route('/get_news_list')
def get_news_list():
    # 获取参数
    cid = request.args.get("cid")  # 新闻类型
    cur_page = request.args.get("cur_page")  # 当前页码
    per_count = request.args.get("per_count",HOME_PAGE_MAX_NEWS)  # 每页新闻个数
    # 校验参数
    if not all([cid, cur_page]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 将参数转为整形（从请求中获取的数据统一是str）
    try:
        cid = int(cid)
        per_count = int(per_count)
        cur_page = int(cur_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    filter_list = [News.status == 0]  # 只有审核通过的文章才能被战士
    if cid != 1:  # 因为类别1并不是对应的类别，而是取最新（根据发布时间来获得）
        filter_list.append(News.category_id == cid)
    # 根据参数查询新闻数据  按照分类进行分页查询（生成日期倒序）
    try:
        pn = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(cur_page,per_count)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    data = {
        "news_list": [news.to_dict() for news in pn.items],  # 自定义类型的数据不能转换为json字符串，所以需要将其转换为字典
        "total_page": pn.pages  # 用于帮助前端判断最终页
    }

    # 将数据以json返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=data)
