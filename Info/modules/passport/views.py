from flask import request, abort, current_app, make_response

from Info import sr
from Info.modules.passport import passport_blu

from Info.utils.captcha.pic_captcha import captcha


# 2.使用蓝图来装饰路由
@passport_blu.route('/get_img_code')
def get_img_code():
    # 获取参数
    img_code_id = request.args.get("img_code_id")
    # 校验参数
    if not img_code_id:
        return abort(403)
    # 生成图片验证码
    img_name, img_code_text, img_code_bytes = captcha.generate_captcha()  # 使用的是第三方工具（utils里面）
    # 将图片key和验证码文字保存到redis数据库中
    # 一旦是关于数据库的操作都应当进行异常捕获,提高程序稳定性
    try:
        sr.set("img_code_id" + img_code_id, img_code_text, ex=180)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)
    # 返回验证码图片
    # 创建响应头
    response = make_response(img_code_bytes)
    # 设置响应头
    response.content_type="image/jpeg"
    return response