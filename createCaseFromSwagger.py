from httprunner.ext.har2case.core import HarParser
from loguru import logger
import requests
import re
import copy
from util import *
import json

class SwaggerHarParser(HarParser):


    def __init__(self, config=None):
        if config:
            self.config = config
        else:
            self.config = {}


    def getFileName(self, url, method=None):
        if not url:
            raise Exception("路径不存在，所以无法根据路径创建文件名")
        if url.__contains__("/{") and isinstance(url, str):
            url = url[:url.index("/{")]
        url = url.replace("$", "")
        if url.__contains__("/") and isinstance(url, str):
            if url.index('/') == 0:
                url = url[1:]
            url = url.replace('/', "_")
            if not method:
                return url
            else:
                return "{}_{}".format(url, method.__str__())
        else:
            raise Exception("路径错误{}".format(url))

    def getReqDto(self, name, definitions):
        annotation = ""
        if isinstance(definitions, dict):
            data = copy.deepcopy(definitions.get(name, {}))
            if "properties" in data:
                data = data["properties"]
            else:
                logger.info("springfallspringfall{}".format(data))
            if isinstance(data, dict):
                for k, v in data.items():
                    if "items" in v and "array".__eq__(v["type"]):
                        if v["items"].get("originalRef"):
                            temp_annotation, temp_data = self.getReqDto(v["items"]["originalRef"], definitions)
                            annotation = annotation + "," + temp_annotation
                            data[k] = [temp_data]
                        else:
                            annotation = annotation + "," + k.replace("-", "_")
                            data[k] = ["${}".format(k.replace("-", "_"))]
                    else:
                        annotation = annotation + "," + k.replace("-", "_")
                        data[k] = "${}".format(k.replace("-", "_"))
            return annotation, data
        else:
            raise TypeError("数据类型错误")

    def getRequestParams(self, data, definitions):
        result = {"params": {}, "headers": {}, "data": {}, "upload": {}, "json": {}}
        annotation = ""
        if not isinstance(data, list):
            raise Exception("数据格式不对")
        for parms in data:
            if not isinstance(parms, dict):
                raise TypeError("数据格式对")
            name = parms.get("name", "")
            where = parms.get("in", "")

            if parms.__contains__("schema"):
                schema = parms["schema"]
                if isinstance(schema, dict) and schema.__contains__("originalRef"):
                    annotation_temp, reqData = self.getReqDto(schema.get("originalRef"), definitions)
                    annotation = annotation + annotation_temp
                elif isinstance(schema, dict) and schema.__contains__("items") and schema["type"] == "array":
                    annotation_temp, reqData = self.getReqDto(schema["items"].get("originalRef"), definitions)
                    annotation = annotation + annotation_temp
                    reqData = [reqData]
                else:
                    continue

                if (where in ("query")) and name:
                    result["params"].update({name: reqData})
                elif "header".__eq__(where) and name:
                    if name.__contains__("sessionid"):
                        result["headers"].update({name: "$sessionId"})
                    else:
                        result["headers"].update({name: reqData})
                elif (where in ("json", "body")) and name:
                    if isinstance(reqData, list):
                        result["json"] = reqData
                    elif isinstance(reqData, dict):
                        result["json"] = reqData
                        # result["json"].update({name: reqData})
                    elif isinstance(reqData, str):
                        result["json"].update({name: reqData})
                elif "upload".__eq__(where):
                    result["upload"].update({name: reqData})
                elif "data".__eq__(where):
                    result["data"].update({name: reqData})
            else:
                if (where in ("query")) and name:
                    annotation = annotation + name.replace("-", "_") + ","
                    result["params"].update({name: "${}".format(name.replace("-", "_"))})
                elif "header".__eq__(where) and name:
                    if name.__contains__("sessionid"):
                        result["headers"].update({name: "$sessionId"})
                    else:
                        result["headers"].update({name: "${}".format(name.replace("-", "_"))})
                elif "upload".__eq__(where):
                    annotation = annotation + "," + name.replace("-", "_")
                    result["upload"].update({name: "${}".format(name.replace("-", "_"))})
                elif "data".__eq__(where):
                    annotation = annotation + "," + name.replace("-", "_")
                    result["data"].update({name: "${}".format(name.replace("-", "_"))})
                elif (where in ("json", "body")) and name:
                    annotation = annotation + "," + name.replace("-", "_")
                    result["json"].update({name: "${}".format(name.replace("-", "_"))})

        return annotation, self.manageParam(result)  # self._create_csv_param(result)

    def manageParam(self, result):
        if not isinstance(result, dict):
            raise TypeError("处理的数据为字典数据，请传入对应类型的数据类型")
        for key in list(result.keys()):
            if not result[key]:
                result.pop(key)
        return result



    def getSummary(self, data):
        if not isinstance(data, str):
            data = data.__str__()
        if data.__contains__(",") and data.__contains__("，"):
            return data[:min(data.index(","), data.index("，"))]
        elif data.__contains__(","):
            return data[:data.index(",")]
        elif data.__contains__("，"):
            return data[:data.index("，")]
        else:
            return data

    def getSwaggerData(self, module, url_data):
        url = url_data.get("url", "")
        if not module:
            module = "api"
        if not url:
            raise Exception("url不存在")
        if not url.__contains__("http:") and not url.__contains__("https"):
            raise Exception("网址不对()".format(url))
        testRequests = []

        apis_path = url_data.get("only", [])
        if not apis_path:
            old_data_file = createHistoryFolder(module)
            old_data = {}
            old_data_dir = ""
            if os.path.isfile(old_data_file):
                old_data_dir = os.path.join(os.path.dirname(old_data_file))
                with open(old_data_file, 'r') as f:
                    old_data = json.load(f)
            else:
                old_data_dir = old_data_file

            new_data = requests.get(url).json()
            data = diff2dict(old_data, new_data)
            for k, v in data["paths"].items():
                data["paths"][k] = copy.deepcopy(new_data["paths"][k])

            saveOlderData(old_data_dir, new_data, data)
            definitions = new_data.get("definitions", {})
        else:
            data = requests.get(url).json()
            only_path = {}
            for key in apis_path:
                if data["paths"].get(key, {}):
                    only_path[key] = data["paths"].get(key)
                else:
                    raise Exception("接口路径不对，请确认配置文件中的路径是正确", key)
            # only_path = [data["paths"].get(key) for key in apis_path]
            data["paths"] = only_path
            definitions = data.get("definitions", {})

        paths = data.get("paths", {})
        if not isinstance(paths, dict):
            raise TypeError("数据格式不是字典模式，请确认以后再重新运行")
        for k, v in paths.items():
            testRequest = {
                "tags": "",
                "name": "",
                "validate": [],
                "csv_params": ""
            }
            if k.__contains__("/{"):
                temp = re.findall("/\{(\w+)\}", k)
                csv_annotation = ""
                for t in temp:
                    csv_annotation = csv_annotation + t + ","
                if csv_annotation.startswith(","):
                    csv_annotation = csv_annotation[1:]
                if csv_annotation.endswith(","):
                    csv_annotation = csv_annotation[:-1]
                testRequest["csv_params"] = csv_annotation
                k = k.replace("{", "$").replace("}", "")
            # testRequest["request"]["url"] = k

            if not isinstance(v, dict):
                raise TypeError("数据格式不是字典模式，请确认以后再重新运行")
            for method, requestData in v.items():
                request = {"url": k}
                request["method"] = method.upper()
                # testRequest["request"]["method"] = method.upper()
                if not isinstance(requestData, dict):
                    raise TypeError("数据需要时字典模式")
                for name, parameters in requestData.items():
                    if "tags".__eq__(name):
                        testRequest["tags"] = parameters
                    elif "summary".__eq__(name):
                        if isinstance(name, str):
                            testRequest["name"] = self.getSummary(parameters)
                        else:
                            parameters = parameters.__str__()
                            testRequest["name"] = parameters[
                                                  :min(parameters.index(","), parameters.index("，"))]
                    elif "parameters".__eq__(name):
                        annotation, result = self.getRequestParams(parameters, definitions)
                        request.update(**result)
                        testRequest["request"] = request
                        if testRequest.get("csv_params"):
                            testRequest["csv_params"] = testRequest["csv_params"] + "," + annotation
                        else:
                            testRequest["csv_params"] = annotation
                testRequest["csv_params"] = self.formatCSVParams(testRequest["csv_params"])
                testRequests.append(copy.deepcopy(testRequest))

        return (module, testRequests)

    def formatCSVParams(self, text):
        if not isinstance(text, str):
            raise TypeError("参数类型错误")
        return ",".join([i for i in text.split(',') if i])


    def createCase_dir(self, dir="api", rootDir=None):
        try:
            if rootDir and os.path.isdir(rootDir):
                root_dir = rootDir
            else:
                root_dir = os.path.join(os.path.dirname(__file__), "testcases")

            if not os.path.isdir(root_dir):
                os.makedirs(root_dir)
                with open(os.path.join(root_dir, "__init__.py"), 'w') as f:
                    f.write("")
            else:
                if not os.path.isfile(os.path.join(root_dir, "__init__.py")):
                    with open(os.path.join(root_dir, "__init__.py"), 'w') as f:
                        f.write("")
            root_dir = os.path.join(root_dir, dir)
            if not os.path.isdir(root_dir):
                os.makedirs(root_dir)
                with open(os.path.join(root_dir, "__init__.py"), "w") as f:
                    f.write("")
            else:
                if not os.path.isfile(os.path.join(root_dir, "__init__.py")):
                    with open(os.path.join(root_dir, "__init__.py")) as f:
                        f.write("")
            return root_dir
        except:
            raise Exception("初始化文件夹的时候出错")
