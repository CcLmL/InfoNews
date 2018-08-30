# 定义索引转换过滤器(如果使用装饰器的方法定义过滤器，这里先得使用current_app进行关联，init文件中也要声明这个装饰器，相比很麻烦)
import functools

from flask import session, current_app, g

from Info.models import User


def index_convert(index):
    index_dict = {
        1: "first",
        2: "second",
        3: "third"
    }
    return index_dict.get(index, "")



# 查询用户登陆状态
def user_login_data(f):
    @functools.wraps(f)  # 可以让闭包函数wrapper使用指定函数f的函数信息（如函数名__name__,文档注释__doc__）
    def wrapper(*args, **kwargs):
        # 判断用户是否登陆
        user_id = session.get("user_id")
        user = None  # 当某些极端情况下，user_id没有值，这样从库里就取不出数据，但是模板渲染里仍要传值，这时需要相当于对user进行初始化
        if user_id:
            # 根据user_id查询用户模型
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)

        # user = user.to_dict() if user else None  # 因为这里只是用于验证用户是否登陆，不需要对user里的取值进行格式化

        g.user = user  # 让g变量记录查询出的用户数据

        # 再执行原有的功能
        return f(*args, **kwargs)

    return wrapper
