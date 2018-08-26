from flask import Blueprint

news_blu = Blueprint("news", __name__, url_prefix="/news")  # 别忘记加url前缀啊

from .views import *