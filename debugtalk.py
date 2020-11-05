
import time
import ast
from loguru import logger
import sys


# 获取基础url地址的函数

def get_base_url():
    return "https://XXXXX"          #替换成自己项目的base_url



def teardown_hook_sleep_N_secs(response, n_secs):
    if response.status_code == 200:
        time.sleep(n_secs)
    else:
        time.sleep(0.5)


def get_Status_code(status_code):
    if status_code:
        return ast.literal_eval(status_code)
    else:
        return 0

def get_extract_variable(parameter_variable, extract_variable):
    #如果参数变量中的值为特殊字符--@@--的时候，则使用提取变量作为输入，否则使用参数变量
    if "@@".__eq__(parameter_variable):
        return extract_variable
    else:
        return parameter_variable