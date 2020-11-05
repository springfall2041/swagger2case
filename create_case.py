import os
from createCaseFromSwagger import SwaggerHarParser
from httprunner.make import make_testcase, format_pytest_with_black
import copy
from loguru import logger
from util import *

common_config = {
    "name": "testcase description",
    "parameters": {},
    "path": "",
    "base_url": "${get_base_url()}",
    "verify": False,
    "variables": {"x_tenant_id": "${get_x_tenant_id()}"},
    "validate": [
        {'eq': ['status_code', "${get_Status_code($status_code)}"]},
        {'eq': ['body.code', "$body_code"]},
        {'eq': ['body.msg', "$body_msg"]},
        {'eq': ['headers."Content-Type"', "application/json;charset=UTF-8"]}
    ],
    "configParam": "status_code-body_code-body_msg"
}

runTestcase = {
    "name": "login",
    "testcase": "Login",
    "export": ["sessionId"],
}


if __name__ == "__main__":
    logger.add("./log.log")
    """
    清空用力文件夾
    """
    root_dir = os.path.join(os.path.dirname(__file__), "testcases")
    testcase_path = "testcases"
    clearTestCaseFolder(root_dir)

    swagger = SwaggerHarParser()

    definitions = {}
    tags = {}
    paths = {}

    url_dict = getConfig()

    for module, url in url_dict.items():

        (module, testRequests) = swagger.getSwaggerData(module, url)

        swagger.api_dir = "api"
        swagger.testcases_dir = testcase_path
        swagger.module_dir = module
        root_dir = swagger.createCase_dir(dir=swagger.api_dir)

        #创建debugtalk.py
        debutalk_dir = os.path.dirname(os.path.dirname(root_dir))
        debugtalk_file = os.path.join(debutalk_dir, "debugtalk.py")
        if not os.path.isfile(debugtalk_file):
            with open(debugtalk_file, "w") as f:
                f.write('')
        #创建module目录
        module_dir = swagger.createCase_dir(dir=module, rootDir=root_dir)
        for request in testRequests:
            config = copy.deepcopy(common_config)
            config["parameters"].update({url["parameter_key"]: url["parameter_value"]})

            tags = request.get("tags", "")
            #创建tag的文件夹
            if not tags:
                tag_dir = module_dir
            elif isinstance(tags, list):
                tag_dir = swagger.createCase_dir(dir=tags[0], rootDir=module_dir)
            elif isinstance(tags, str):
                tag_dir = swagger.createCase_dir(dir=tags, rootDir=module_dir)
            else:
                raise TypeError("tags类型错误，请确认以后再执行")
            swagger.tag_dir = os.path.basename(tag_dir)
            swagger.file_path = os.path.join(tag_dir, swagger.getFileName(request["request"].get("url", ""), method=request["request"].get("method", "").lower()))
            #创建对应的csv文件
            csv_file = os.path.join(tag_dir, "{}.csv".format(swagger.file_path))
            with open(csv_file, 'w') as f:
                temp = request.get("csv_params", "")
                if temp:
                    f.write("{}-{}".format(temp, common_config.get("configParam","")).replace("-", ","))
                else:
                    f.write("{}".format(common_config.get("configParam","")).replace("-", ","))

            if request.__contains__("tags"):
                request.pop('tags')
            request["request"]["url"] = "{}{}".format(url["prefix"], request["request"]["url"])
            request["validate"].extend(config["validate"])
            request["request"] = dict((k, v) for k, v in request["request"].items() if v)
            config["path"] = csv_file
            params = ""
            if request["csv_params"].replace(",", "-"):
                params = "{},{}".format(request["csv_params"].replace(",", "-"), common_config.get("configParam")).replace("-", ",")
            else:
                params = "{}".format(common_config.get("configParam")).replace("-", ",")
            config["parameters"].update({params.replace(",", "-"): "${parameterize(" + "{}/{}/{}/{}/{}".format("testcases", "api", module, tags[0], os.path.basename(csv_file)) + ")}"})

            testcase = {"config": config, "teststeps": [request]}

            output_testcase_file = make_testcase(testcase)
            format_pytest_with_black(output_testcase_file)
            os.rename(output_testcase_file, "{}.infancy".format(output_testcase_file))