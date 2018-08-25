# 定义索引转换过滤器(如果使用装饰器的方法定义过滤器，这里先得使用current_app进行关联，init文件中也要声明这个装饰器，相比很麻烦)
def index_convert(index):
    index_dict = {
        1: "first",
        2: "second",
        3: "third"
    }
    return index_dict.get(index, "")