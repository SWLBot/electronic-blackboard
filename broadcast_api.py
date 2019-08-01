from mysql import mysql
from mysql import DB_Exception
from datetime import date
from datetime import datetime
from datetime import timedelta
from dataAccessObjects import *
import os.path
import json

def getDisplayContent(sche_target_id, return_msg):
    """
    Get the display content of the display target.

    Args:
        sche_target_id: The id of display target
        return_msg: Output paramter
    """
    targetIdPrefix = sche_target_id[:4]
    if targetIdPrefix == "imge":
        with ImageDao() as imageDao:
            file_info = imageDao.getIdSysName(Id=sche_target_id)
        return_msg["display_type"] = "image"
    elif targetIdPrefix == "text":
        with TextDao() as textDao:
            file_info = textDao.getIdSysName(Id=sche_target_id)
        return_msg["display_type"] = "text"
    else :
        raise Exception("target id type error {}".format(targetIdPrefix))

    try:
        type_id = file_info['typeId']
        system_file_name = file_info['systemName']
        return_msg["like_count"] = file_info['likeCount']
    except:
        raise Exception("no file record")

    with DataTypeDao() as dataTypeDao:
        type_dir = dataTypeDao.getTypeDir(typeId=type_id)
        type_name = dataTypeDao.getTypeName(typeId=type_id)
    if type_dir == None or type_name == None:
        raise Exception("No such type id {}".format(type_id))
    return_msg["type_name"] = type_name

    targetFile = os.path.join("static", type_dir, system_file_name)
    if return_msg["display_type"] == "image":
        return_msg["img"] = targetFile
    elif return_msg["display_type"] == "text":
        if not os.path.isfile(targetFile) :
            raise Exception("Text file doesn't exists")
        else :
            with open(targetFile,"r") as fp:
                file_content = json.load(fp)
            if file_content.get('text_type','') == 'news':
                return_msg['display_type'] = 'news'
            return_msg.update(file_content)

def load_schedule():
    """
    Get the next display target

    Returns:
        return_msg: Display target filled with its attributes
    """
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        #find next schedule
        with ScheduleDao() as scheduleDao:
            next_schedule = scheduleDao.getNextSchedule()
        if next_schedule is None:
            return_msg["error"] = "no schedule"
            return return_msg
        return_msg["display_time"] = next_schedule['display_time']

        sche_target_id = next_schedule['sche_target_id']

        getDisplayContent(sche_target_id, return_msg)

        if return_msg["display_type"] == "image":
            with ImageDao() as imageDao:
                imageDao.addDisplayCount(sche_target_id)
        elif return_msg["display_type"] in ["text","news"]:
            with TextDao() as textDao:
                textDao.addDisplayCount(sche_target_id)
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg
    except Exception as e:
        return_msg["error"] = str(e)
        return return_msg

