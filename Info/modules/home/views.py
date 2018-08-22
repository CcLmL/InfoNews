from flask import current_app

from Info.modules.home import home_blu


# 2.使用蓝图来装饰路由
@home_blu.route('/')
def index():
    try:
        1/0
    except Exception as e:
        # logging.error("发现一个错误：%s" % e)  # 显示效果不友好
        current_app.logger.error("发信一个错误： %s" % e)  # 使用flask内置的日志表达形式（显示行号）
    return 'hello world'
