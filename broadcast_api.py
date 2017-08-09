from mysql import mysql
from mysql import DB_Exception
from datetime import date
from datetime import datetime
from datetime import timedelta
from dataAccessObjects import *
import os.path
import json



#The API load schedule.txt and find out the first image which has not print and the time limit still allow
def load_schedule():
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        schedule_dir = ""
        sche_target_id = ""
        type_id = ""
        system_file_name = ""

        #connect to mysql
        db = mysql()
        db.connect()

        #find next schedule
        with ScheduleDao() as scheduleDao:
            next_schedule = scheduleDao.getNextSchedule()
        if next_schedule is None:
            return_msg["error"] = "no schedule"
            return return_msg
        return_msg["schedule_id"] = next_schedule['schedule_id']
        sche_target_id = next_schedule['sche_target_id']
        return_msg["display_time"] = int(next_schedule['display_time'])

        #find the file
        if sche_target_id[0:4]=="imge":
            with ImageDao() as imageDao:
                file_info = imageDao.getIdSysName(Id=sche_target_id)
            return_msg["file_type"] = "image" 
        elif sche_target_id[0:4]=="text":
            with TextDao() as textDao:
                file_info = textDao.getIdSysName(Id=sche_target_id)
            return_msg["file_type"] = "text"
        else :
            db.close()
            return_msg["error"] = "target id type error"
            return return_msg
        try:
            type_id = int(file_info['typeId'])
            system_file_name = file_info['systemName']
            return_msg["like_count"] = int(file_info['likeCount'])
        except:
            db.close()
            return_msg["error"] = "no file record"
            return return_msg

        #find type dir
        with DataTypeDao() as dataTypeDao:
            type_dir = dataTypeDao.getTypeDir(typeId=type_id)
            type_name = dataTypeDao.getTypeName(typeId=type_id)
        try:
            schedule_dir = os.path.join(schedule_dir, "static", type_dir, system_file_name)
            return_msg["file"] = os.path.join(type_dir, system_file_name)
            return_msg["type_name"] = str(type_name)
        except:
            db.close()
            return_msg["error"] = "no type record"
            return return_msg

        #if text read file
        if return_msg["file_type"] == "text":
            if not os.path.isfile(schedule_dir) :
                db.close()
                return_msg["error"] = "no file"
                return return_msg
            else :
                with open(schedule_dir,"r") as fp:
                    file_content = json.load(fp)
                return_msg["file_text"] = file_content

        #update display count
        if return_msg["file_type"] == "image":
            sql = "UPDATE image_data SET img_display_count=img_display_count+1 WHERE img_id='"+sche_target_id+"'"
        elif return_msg["file_type"] == "text":
            sql = "UPDATE text_data SET text_display_count=text_display_count+1 WHERE text_id='"+sche_target_id+"'"
        db.cmd(sql)

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

