from mysql import mysql
from mysql import DB_Exception
from datetime import date
from datetime import datetime
from datetime import timedelta
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

        #find schedule
        sql = ("SELECT sche_id, sche_target_id, sche_display_time FROM schedule WHERE sche_is_used=0 ORDER BY sche_sn ASC LIMIT 1")
        pure_result = db.query(sql)
        try:
            return_msg["schedule_id"] = pure_result[0][0]
            sche_target_id = pure_result[0][1]
            return_msg["display_time"] = int(pure_result[0][2])
        except:
            db.close()
            return_msg["error"] = "no schedule"
            return return_msg


        #find the file
        if sche_target_id[0:4]=="imge":
            sql = ("SELECT type_id, img_system_name, img_like_count FROM image_data WHERE img_id=\"" + sche_target_id + "\" ")
            return_msg["file_type"] = "image" 
        elif sche_target_id[0:4]=="text":
            sql = ("SELECT type_id, text_system_name, text_like_count FROM text_data WHERE text_id=\"" + sche_target_id + "\" ")
            return_msg["file_type"] = "text"
        else :
            db.close()
            return_msg["error"] = "target id type error"
            return return_msg
        pure_result = db.query(sql)
        try:
            type_id = int(pure_result[0][0])
            system_file_name = pure_result[0][1]
            return_msg["like_count"] = int(pure_result[0][2])
        except:
            db.close()
            return_msg["error"] = "no file record"
            return return_msg

        #find type dir
        sql = ("SELECT type_dir, type_name FROM data_type WHERE type_id=" + str(type_id))
        pure_result = db.query(sql)
        try:
            schedule_dir = os.path.join(schedule_dir, "static/")
            schedule_dir = os.path.join(schedule_dir, pure_result[0][0])
            schedule_dir = os.path.join(schedule_dir, system_file_name)
            return_msg["file"] = os.path.join(pure_result[0][0], system_file_name)
            return_msg["type_name"] = str(pure_result[0][1])
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








