import os
import time
import json
import shutil


"""
对比两个字典之间的差异，把差异返回来。
"""
def diff2dict(old_data, new_data):
    diff_data = {}
    if isinstance(old_data, dict) and isinstance(new_data, dict):
        if old_data.__str__().__eq__(new_data.__str__()):
            return diff_data
        else:
            for k, v in new_data.items():
                # 当值不是字典的时候进行对比，如果值是字典则重新操作
                if not isinstance(v, dict):
                    if k in old_data:
                        if v == old_data.get(k, ""):
                            continue
                        else:
                            diff_data.update({k: v})
                    else:
                        diff_data.update({k: v})
                else:
                    if k in old_data:
                        temp = diff2dict(old_data.get(k, {}), v)
                        if temp:
                            diff_data.update({k: temp})
                    else:
                        diff_data.update({k: v})
        return diff_data
    elif isinstance(old_data, dict) and (not isinstance(new_data, dict)):
        raise TypeError("参数类型错误，请确认以后重传old_data type:{}, new_data type: {}".format(type(old_data), type(new_data)))
    elif (not isinstance(old_data, dict)) and isinstance(new_data, dict):
        return new_data
    else:
        return {}


"""
创建历史文件夹, 返回历史文件
"""
def createHistoryFolder(module=None):
    folder = "module"
    if module:
        folder = module
    dir_folder = os.path.join(os.path.dirname(__file__), "history", folder)
    os.makedirs(dir_folder, exist_ok=True)

    file_lists = os.listdir(dir_folder)
    if file_lists:
        file_lists = [i for i in file_lists if i.__contains__(folder)]
        file_lists.sort(reverse=True)
        return os.path.join(dir_folder, file_lists[0])
    else:
        return dir_folder


    #获取年月日时分秒
    # file_name = os.path.join(dir_folder, "{}-{}.json".format(folder, time.strftime("%Y%m%d%H%M%S", time.localtime()), ".json"))



"""
保存上一次的数据
"""
def saveOlderData(old_data_dir, swaggerData, updateDate):
    if not isinstance(swaggerData, dict):
        raise TypeError("swagger数据为字典模式，请确认以后再执行")
    if not isinstance(updateDate, dict):
        raise TypeError("相比上次数据，本次swagger更新的数据是为字典模式，请确认以后再次执行")


    swaggerData_file = os.path.join(old_data_dir, "{}_{}.json".format(os.path.basename(old_data_dir), time.strftime("%Y%m%d%H%M%S", time.localtime())))
    updateDate_file = os.path.join(old_data_dir, "update_{}.json".format(time.strftime("%Y%m%d%H%M%S", time.localtime())))

    with open(swaggerData_file, 'w') as f:
        json.dump(swaggerData, f)

    with open(updateDate_file, 'w') as f:
        json.dump(updateDate, f)


"""
清空用力文件夾
"""
def clearTestCaseFolder(folder_path):
    try:
        if os.path.isdir(folder_path):
            shutil.rmtree(folder_path)
            return True
        else:
            return True
    except:
        return False



def getConfig(config=None):
    config_path = ""
    if config and os.path.isfile(config):
        with open(config, 'r') as f:
            return json.load(f)

    else:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, 'r') as f:
            return json.load(f)









if __name__ == "__main__":
    createHistoryFolder()