from flask import Blueprint
# 一个页面对应一个包

# 1.创建蓝图对象（使视图函数能够全局使用）
home_blu = Blueprint("home", __name__)

# 4.关联视图函数
from .views import *  # 这个导入要写在创建的蓝图对象的后面，否则会出现我想使用view中的蓝图，view中又想使用我们创建的蓝图对象，这就陷入循环导入的情况
