from mysql import mysql
from mysql import DB_Exception
from random import sample
from datetime import date
from time import sleep
from PIL import Image
from urllib import request
from server_api import upload_image_insert_db
from server_api import upload_text_insert_db
from server_api import delete_image_or_text_data
from server_api import get_credentials
from server_api import get_upcoming_events
from pprint import pprint
from apiclient.http import MediaIoBaseDownload
from apiclient import discovery
from news_crawler.news_crawler import *
import httplib2
import io
import datetime
import signal
import time
import os.path
import json

#make now activity to is used
def mark_now_activity():
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        target_sn = 0
    
        #connect to mysql
        db = mysql()
        db.connect()
        
        #find schedule
        sql = ("SELECT sche_sn FROM schedule WHERE sche_is_used=0 ORDER BY sche_sn ASC LIMIT 1")
        pure_result = db.query(sql)
        try:
            target_sn = int(pure_result[0][0])
        except:
            db.close()
            return_msg["error"] = "no schedule"
            return return_msg
    
        #mark target
        sql = ("UPDATE schedule SET sche_is_used=1 WHERE sche_sn=" + str(target_sn))
        db.cmd(sql)
    
        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg
        
#child function of load_next_schedule
def find_next_schedule(db):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        sql = ("SELECT sche_id, sche_target_id, sche_display_time, sche_is_artificial_edit, sche_sn "\
                    +"FROM schedule WHERE sche_is_used=0 ORDER BY sche_sn ASC LIMIT 1")
        pure_result = db.query(sql)
        try:
            return_msg["schedule_id"] = pure_result[0][0]
            return_msg["sche_target_id"] = pure_result[0][1]
            return_msg["display_time"] = int(pure_result[0][2])
            return_msg["no_need_check_time"] = pure_result[0][3]
            return_msg["target_sn"] = int(pure_result[0][4])
        except:
            return_msg["error"] = "no schedule"
            return return_msg
        
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

#The API load schedule.txt and find out the first image which has not print and still meet the time limit
def load_next_schedule(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        target_dir = ""
        sche_target_id = ""
        target_sn = 0
        type_id = ""
        system_file_name = ""
        no_need_check_time = 0
        try:
            target_dir = json_obj["board_py_dir"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg
    
        #connect to mysql
        db = mysql()
        db.connect()
        
        while True:
            #find schedule
            receive_msg = {}
            receive_msg = find_next_schedule(db)
            if receive_msg["result"]=="fail":
                db.close()
                return_msg["error"] = receive_msg["error"]
                return return_msg
            
            return_msg["schedule_id"] = receive_msg["schedule_id"]
            sche_target_id = receive_msg["sche_target_id"]
            return_msg["display_time"] = receive_msg["display_time"]
            no_need_check_time = receive_msg["no_need_check_time"]
            target_sn = receive_msg["target_sn"]
    
            #find the file
            if sche_target_id[0:4]=="imge":
                sql = ("SELECT type_id, img_system_name FROM image_data WHERE img_id='" + sche_target_id + "' ")
                return_msg["file_type"] = "image" 
            elif sche_target_id[0:4]=="text":
                sql = ("SELECT type_id, text_system_name FROM text_data WHERE text_id='" + sche_target_id + "' ")
                return_msg["file_type"] = "text"
            else :
                # mark activity is used
                if target_sn != 0:
                    sql = ("UPDATE schedule SET sche_is_used=1 WHERE sche_sn=" + str(target_sn))
                    db.cmd(sql)
                    target_sn = 0
                continue
            pure_result = db.query(sql)
            try:
                type_id = int(pure_result[0][0])
                system_file_name = pure_result[0][1]
            except:
                # mark activity is used
                if target_sn != 0:
                    sql = ("UPDATE schedule SET sche_is_used=1 WHERE sche_sn=" + str(target_sn))
                    db.cmd(sql)
                    target_sn = 0
                continue
    
            #check time if needed
            if no_need_check_time == b'\x00':
                if return_msg["file_type"]=="image":
                    sql = ("SELECT type_id FROM image_data WHERE img_id='" + sche_target_id + "' "\
                        +" and img_is_delete=0 and img_is_expire=0 "\
                        +" and (TO_DAYS(NOW()) between TO_DAYS(img_start_date) and TO_DAYS(img_end_date)) " \
                        +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(img_start_time) and TIME_TO_SEC(img_end_time)) ")
                elif return_msg["file_type"]=="text":
                    sql = ("SELECT type_id FROM text_data WHERE text_id='" + sche_target_id + "' "\
                        +" and text_is_delete=0 and text_is_expire=0 "\
                        +" and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) " \
                        +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time)) ")
                else:
                    "impossible"
                pure_result = db.query(sql)
                if len(pure_result)==0:
                    # mark activity is used
                    if target_sn != 0:
                        sql = ("UPDATE schedule SET sche_is_used=1 WHERE sche_sn=" + str(target_sn))
                        db.cmd(sql)
                        target_sn = 0
                    continue
            
            #find type dir
            check_target_dir = ""
            sql = ("SELECT type_dir FROM data_type WHERE type_id=" + str(type_id))
            pure_result = db.query(sql)
            try:
                check_target_dir = os.path.join(target_dir, "static/")
                check_target_dir = os.path.join(check_target_dir, pure_result[0][0])
                check_target_dir = os.path.join(check_target_dir, system_file_name)
            except:
                # mark activity is used
                if target_sn != 0:
                    sql = ("UPDATE schedule SET sche_is_used=1 WHERE sche_sn=" + str(target_sn))
                    db.cmd(sql)
                    target_sn = 0
                continue
    
            #if text read file
            if not os.path.isfile(check_target_dir) :
                # mark activity is used
                if target_sn != 0:
                    sql = ("UPDATE schedule SET sche_is_used=1 WHERE sche_sn=" + str(target_sn))
                    db.cmd(sql)
                    target_sn = 0
                continue
            else :
                return_msg["file"] = check_target_dir
                break
        
        #check less activity number
        sql = "SELECT count(sche_sn) FROM schedule WHERE sche_is_used=0"
        pure_result = db.query(sql)
        try:
            return_msg["last_activity"] = int(pure_result[0][0])
        except:
            db.close()
            return_msg["error"] = "sql error"
            return return_msg

        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg
    
#The API connect mysql and find text data that can be scheduled
def find_text_acticity(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        deal_result = []
        arrange_mode = 1
        arrange_condition = []
        try:
            arrange_mode = json_obj["arrange_mode"]
            if "condition" in json_obj:
                arrange_condition = json_obj["condition"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        #connect to mysql
        db = mysql()
        db.connect()
        
        #find images that may be schedule
        if arrange_mode == 0 :
            sql = "SELECT text_id, text_display_time FROM text_data" \
                +" WHERE text_is_delete=0 and text_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time)) " \
                +" ORDER BY text_id ASC"
        elif arrange_mode == 1 or arrange_mode == 2:
            sql = "SELECT text_id, text_display_time FROM text_data" \
                +" WHERE text_is_delete=0 and text_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time))" 
        elif arrange_mode == 3 :
            sql = "SELECT text_id, text_display_time FROM text_data WHERE ( "
            for num1 in range(len(arrange_condition)):
                if num1 == 0:
                    sql = sql + " type_id=" + str(arrange_condition[num1]) + " "
                else :
                    sql = sql + " or type_id=" + str(arrange_condition[num1]) + " "
            sql = sql + " ) and text_is_delete=0 and text_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time))"\
                +" ORDER BY text_id ASC"
        elif arrange_mode == 4 or arrange_mode == 5:
            sql = "SELECT text_id, text_display_time FROM text_data WHERE ( "
            for num1 in range(len(arrange_condition)):
                if num1 == 0:
                    sql = sql + " type_id=" + str(arrange_condition[num1]) + " "
                else :
                    sql = sql + " or type_id=" + str(arrange_condition[num1]) + " "
            sql = sql + " ) and text_is_delete=0 and text_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time))"
        elif arrange_mode == 6:
            sql = "SELECT a0.text_id, a0.text_display_time, a1.type_weight FROM " \
                +" (SELECT text_id, type_id, text_display_time FROM text_data WHERE " \
                +" text_is_delete=0 and text_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time))) AS a0 "\
                +" LEFT JOIN (SELECT type_id, type_weight FROM data_type ) AS a1 "\
                + " ON a0.type_id=a1.type_id ORDER BY a1.type_weight ASC"
        elif arrange_mode == 7:
            sql = "SELECT a0.text_id, a0.text_display_time, a1.type_weight FROM " \
                +" (SELECT text_id, type_id, text_display_time FROM text_data WHERE ( "
            for num1 in range(len(arrange_condition)):
                if num1 == 0:
                    sql = sql + " type_id=" + str(arrange_condition[num1]) + " "
                else :
                    sql = sql + " or type_id=" + str(arrange_condition[num1]) + " "
            sql = sql + " ) and text_is_delete=0 and text_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time))) AS a0 "\
                +" LEFT JOIN (SELECT type_id, type_weight FROM data_type WHERE ("
            for num1 in range(len(arrange_condition)):
                if num1 == 0:
                    sql = sql + " type_id=" + str(arrange_condition[num1]) + " "
                else :
                    sql = sql + " or type_id=" + str(arrange_condition[num1]) + " "
            sql = sql + ")) AS a1 ON a0.type_id=a1.type_id ORDER BY a1.type_weight ASC"
        
        pure_result = db.query(sql)
        #restruct results of query
        for result_row in pure_result:
            if len(result_row)==2:
                deal_result.append([result_row[0], int(result_row[1])])
            elif len(result_row)==3:
                deal_result.append([result_row[0], int(result_row[1]), float(result_row[2])])
            else:
                "DO NOTHING"
        
        #display in loop or random display
        if arrange_mode == 0:
            "DO NOTHING"
        elif arrange_mode == 1:
            deal_result = sample(deal_result, len(deal_result))
        elif arrange_mode == 2:
            if len(deal_result)>20:
                deal_result = sample(deal_result, 20)
        elif arrange_mode == 3:
            "DO NOTHING"
        elif arrange_mode == 4:
            deal_result = sample(deal_result, len(deal_result))
        elif arrange_mode == 5:
            if len(deal_result)>20:
                deal_result = sample(deal_result, 20)
        elif arrange_mode == 6:
            "DO NOTHING"
        elif arrange_mode == 7:
            "DO NOTHING"

        #reshape deal result
        return_msg["ans_list"] = deal_result
        
        db.close()  
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

#The API connect mysql and find image data that can be scheduled
def find_image_acticity(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        deal_result = []
        arrange_mode = 1
        arrange_condition = []
        try:
            arrange_mode = json_obj["arrange_mode"]
            if "condition" in json_obj:
                arrange_condition = json_obj["condition"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        #connect to mysql
        db = mysql()
        db.connect()
        
        #find images that may be schedule
        if arrange_mode == 0 :
            sql = "SELECT img_id, img_display_time FROM image_data" \
                +" WHERE img_is_delete=0 and img_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(img_start_date) and TO_DAYS(img_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(img_start_time) and TIME_TO_SEC(img_end_time)) " \
                +" ORDER BY img_id ASC"
        elif arrange_mode == 1 or arrange_mode == 2:
            sql = "SELECT img_id, img_display_time FROM image_data" \
                +" WHERE img_is_delete=0 and img_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(img_start_date) and TO_DAYS(img_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(img_start_time) and TIME_TO_SEC(img_end_time))" 
        elif arrange_mode == 3 :
            sql = "SELECT img_id, img_display_time FROM image_data WHERE ( "
            for num1 in range(len(arrange_condition)):
                if num1 == 0:
                    sql = sql + " type_id=" + str(arrange_condition[num1]) + " "
                else :
                    sql = sql + " or type_id=" + str(arrange_condition[num1]) + " "
            sql = sql + " ) and img_is_delete=0 and img_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(img_start_date) and TO_DAYS(img_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(img_start_time) and TIME_TO_SEC(img_end_time))"\
                +" ORDER BY img_id ASC"
        elif arrange_mode == 4 or arrange_mode == 5:
            sql = "SELECT img_id, img_display_time FROM image_data WHERE ( "
            for num1 in range(len(arrange_condition)):
                if num1 == 0:
                    sql = sql + " type_id=" + str(arrange_condition[num1]) + " "
                else :
                    sql = sql + " or type_id=" + str(arrange_condition[num1]) + " "
            sql = sql + " ) and img_is_delete=0 and img_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(img_start_date) and TO_DAYS(img_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(img_start_time) and TIME_TO_SEC(img_end_time))"
        elif arrange_mode == 6:
            sql = "SELECT a0.img_id, a0.img_display_time, a1.type_weight FROM " \
                +" (SELECT img_id, type_id, img_display_time FROM image_data WHERE " \
                +" img_is_delete=0 and img_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(img_start_date) and TO_DAYS(img_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(img_start_time) and TIME_TO_SEC(img_end_time))) AS a0 "\
                +" LEFT JOIN (SELECT type_id, type_weight FROM data_type ) AS a1 "\
                + " ON a0.type_id=a1.type_id ORDER BY a1.type_weight ASC"
        elif arrange_mode == 7:
            sql = "SELECT a0.img_id, a0.img_display_time, a1.type_weight FROM " \
                +" (SELECT img_id, type_id, img_display_time FROM image_data WHERE ( "
            for num1 in range(len(arrange_condition)):
                if num1 == 0:
                    sql = sql + " type_id=" + str(arrange_condition[num1]) + " "
                else :
                    sql = sql + " or type_id=" + str(arrange_condition[num1]) + " "
            sql = sql + " ) and img_is_delete=0 and img_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(img_start_date) and TO_DAYS(img_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(img_start_time) and TIME_TO_SEC(img_end_time))) AS a0 "\
                +" LEFT JOIN (SELECT type_id, type_weight FROM data_type WHERE ("
            for num1 in range(len(arrange_condition)):
                if num1 == 0:
                    sql = sql + " type_id=" + str(arrange_condition[num1]) + " "
                else :
                    sql = sql + " or type_id=" + str(arrange_condition[num1]) + " "
            sql = sql + ")) AS a1 ON a0.type_id=a1.type_id ORDER BY a1.type_weight ASC"
        
        pure_result = db.query(sql)
        #restruct results of query
        for result_row in pure_result:
            if len(result_row)==2:
                deal_result.append([result_row[0], int(result_row[1])])
            elif len(result_row)==3:
                deal_result.append([result_row[0], int(result_row[1]), float(result_row[2])])
            else:
                "DO NOTHING"
         
        #display in loop or random display
        if arrange_mode == 0:
            "DO NOTHING"
        elif arrange_mode == 1:
            deal_result = sample(deal_result, len(deal_result))
        elif arrange_mode == 2:
            if len(deal_result)>20:
                deal_result = sample(deal_result, 20)
        elif arrange_mode == 3:
            "DO NOTHING"
        elif arrange_mode == 4:
            deal_result = sample(deal_result, len(deal_result))
        elif arrange_mode == 5:
            if len(deal_result)>20:
                deal_result = sample(deal_result, 20)
        elif arrange_mode == 6:
            "DO NOTHING"
        elif arrange_mode == 7:
            "DO NOTHING"

        #reshape deal result
        return_msg["ans_list"] = deal_result
        
        
        db.close()  
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

#The API connect mysql and find image data that can be scheduled
def find_acticity(json_obj):
    return_msg = {}
    return_msg["result"] = "fail"
    receive_obj = {}
    deal_obj = []
    arrange_mode = 1
    arrange_condition = []

    try:
        arrange_mode = int(json_obj["arrange_mode"])
        if "condition" in json_obj:
            arrange_condition = json_obj["condition"]
    except:
        return_msg["error"] = "input parameter missing"
        return return_msg

    #check condition
    if arrange_mode==3 or arrange_mode==4 or arrange_mode==5 or arrange_mode==7:
        if len(arrange_condition) == 0:
            return_msg["error"] = "input parameter missing"
            return return_msg
    
    
    #get text activity
    receive_obj = find_text_acticity(json_obj)
    if receive_obj["result"] == "success":
        for num1 in range(len(receive_obj["ans_list"])):
            deal_obj.append(receive_obj["ans_list"][num1])
    
    #get image activity
    receive_obj = find_image_acticity(json_obj)
    if receive_obj["result"] == "success":
        for num1 in range(len(receive_obj["ans_list"])):
            deal_obj.append(receive_obj["ans_list"][num1])
    
    #mix image and text
    if arrange_mode == 0 or arrange_mode == 3:
        "DO NOTHING"
    elif arrange_mode == 1 or arrange_mode == 4:
        deal_obj = sample(deal_obj, len(deal_obj))
    elif arrange_mode == 2 or arrange_mode == 5:        
        if len(deal_obj)>20:
            deal_obj = sample(deal_obj, 20)
    elif arrange_mode == 6 or arrange_mode == 7:
        img_start_num = 0
        for num1 in range(len(deal_obj)-1):
            if deal_obj[num1][2] < deal_obj[num1+1][2]:
                img_start_num = num1 + 1
        num1 = 0
        num2 = img_start_num
        new_list = []
        for num3 in range(len(deal_obj)):
            if num1 == img_start_num:
                new_list.append(deal_obj[num2])
                num2 += 1
            elif num2 == len(deal_obj):
                new_list.append(deal_obj[num1])
                num1 += 1
            elif deal_obj[num1][2] >= deal_obj[num2][2]:
                new_list.append(deal_obj[num1])
                num1 += 1
            else :
                new_list.append(deal_obj[num2])
                num2 += 1
        deal_obj = new_list

    #reshape data
    content_id = ""
    content_time = 5
    return_msg["target_id"] = []
    return_msg["display_time"] = []
    for num1 in range(len(deal_obj)):
        try:
            content_id = str(deal_obj[num1][0])
            content_time = int(deal_obj[num1][1])
        except:
            continue
        return_msg["target_id"].append(content_id)
        return_msg["display_time"].append(content_time)

    return_msg["result"] = "success"
    return return_msg

#The API connect mysql and clean expire data
def expire_data_check():
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        deal_result = []

        #connect to mysql
        db = mysql()
        db.connect()

        #find expire image data
        sql = ("SELECT img_id FROM image_data "\
            +"WHERE img_is_delete=0 and img_is_expire=0 and (TO_DAYS(NOW())>TO_DAYS(img_end_date) "\
            +"or (TO_DAYS(NOW())=TO_DAYS(img_end_date) and TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s'))>TIME_TO_SEC(img_end_time)))")    
        pure_result = db.query(sql)
        #update expire data
        for num1 in range(len(pure_result)):
            deal_result.append(pure_result[num1][0])
            sql = ("UPDATE image_data SET img_is_expire=1 WHERE img_id='" + pure_result[num1][0] + "' ")
            try:
                db.cmd(sql)
            except DB_Exception as e:
                return_msg["error"] = e.args[1]
                
        if "error" in return_msg:
            db.close()
            return return_msg

        #find expire text data
        sql = ("SELECT text_id FROM text_data "\
            +"WHERE text_is_delete=0 and text_is_expire=0 and ( TO_DAYS(NOW())>TO_DAYS(text_end_date) "\
            +"or (TO_DAYS(NOW())=TO_DAYS(text_end_date) and TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s'))>TIME_TO_SEC(text_end_time)))")  
        pure_result = db.query(sql)
        #update expire data
        for num1 in range(len(pure_result)):
            deal_result.append(pure_result[num1][0])
            sql = ("UPDATE text_data SET text_is_expire=1 WHERE text_id='" + pure_result[num1][0] + "' ")
            try:
                db.cmd(sql)
            except DB_Exception as e:
                return_msg["error"] = e.args[1]
                
        if "error" in return_msg:
            db.close()
            return return_msg
        
        #update expire schedule
        for num1 in range(len(deal_result)):
            sql = ("UPDATE schedule SET sche_is_used=1 " \
                +"WHERE sche_is_used=0 and sche_is_artificial_edit=0 and sche_target_id='" + deal_result[num1] + "'")
            try:
                db.cmd(sql)
            except DB_Exception as e:
                return_msg["error"] = e.args[1]
                
        if "error" in return_msg:
            db.close()
            return return_msg

        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

#The API connect mysql and add activity to schedule
def edit_schedule(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        next_sn = 0
        target_id_list = []
        display_time_list = []
        target_id = ""
        display_time = 5
        arrange_mode_sn = 1
        try:
            next_sn = json_obj["next_sn"]
            target_id_list = json_obj["target_id"]
            display_time_list = json_obj["display_time"]
            arrange_mode_sn = json_obj["arrange_sn"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        #connect to mysql
        db = mysql()
        db.connect()

        for num0 in range(len(display_time_list)):
            target_id = target_id_list[num0]
            display_time = int(display_time_list[num0])
            
            #get now sn
            sql = ("SELECT sche_sn FROM schedule WHERE sche_is_used=0 ORDER BY sche_sn ASC LIMIT 1")
            pure_result = db.query(sql)
            if len(pure_result)>0:
                #check use update or insert
                sql = ("SELECT sche_sn FROM schedule WHERE sche_sn="+str(int(pure_result[0][0])+next_sn) +" and sche_id != 'sche0undecided'")
                pure_result = db.query(sql)
                if len(pure_result)>0:
                    sql = ("UPDATE schedule SET sche_target_id='" + target_id + "', "\
                        +"sche_display_time="+str(display_time)+", "\
                        +"sche_arrange_time=now(), "\
                        +"sche_arrange_mode="+str(arrange_mode_sn)+", "\
                        +"sche_is_used=0, sche_is_artificial_edit=0 "\
                        +" WHERE sche_sn="+str(pure_result[0][0]))
                    db.cmd(sql)
                else:
                    sql = ("INSERT INTO schedule (sche_id, sche_target_id, sche_display_time, sche_arrange_mode)"\
                        +" VALUES ('sche0undecided', '"+target_id+"', "+str(display_time)+", " + str(arrange_mode_sn) + ")")
                    db.cmd(sql)
                    sql = ("SELECT sche_sn FROM schedule WHERE sche_id='sche0undecided' ORDER BY sche_sn ASC LIMIT 1")
                    pure_result = db.query(sql)
                    if len(pure_result)>0:
                        new_id = "sche" + "{0:010d}".format(int(pure_result[0][0]))
                        sql = ("UPDATE schedule SET sche_id='" + new_id + "' WHERE sche_sn="+str(pure_result[0][0]))
                        db.cmd(sql)
                    else :
                        db.close()
                        return_msg["error"] = "may be another arrange.exe is working"
                        return return_msg
            else :
                sql = ("INSERT INTO schedule (sche_id, sche_target_id, sche_display_time, sche_arrange_mode)"\
                    +" VALUES ('sche0undecided', '"+target_id+"', "+str(display_time)+", " + str(arrange_mode_sn) + ")")
                db.cmd(sql)
                sql = ("SELECT sche_sn FROM schedule WHERE sche_id='sche0undecided' ORDER BY sche_sn ASC LIMIT 1")
                pure_result = db.query(sql)
                
                if len(pure_result)>0:
                    new_id = "sche" + "{0:010d}".format(int(pure_result[0][0]))
                    sql = ("UPDATE schedule SET sche_id='" + new_id + "' WHERE sche_sn="+str(pure_result[0][0]))
                    db.cmd(sql)
                else :
                    db.close()
                    return_msg["error"] = "may be another arrange.exe is working"
                    return return_msg
            next_sn += 1

        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

#The API connect mysql and add activity to schedule
def add_schedule(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        target_id_list = []
        display_time_list = []
        target_id = ""
        display_time = 5
        arrange_mode_sn = 1
        try:
            target_id_list = json_obj["target_id"]
            display_time_list = json_obj["display_time"]
            arrange_mode_sn = json_obj["arrange_sn"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        #connect to mysql
        db = mysql()
        db.connect()

        for num0 in range(len(display_time_list)):
            target_id = target_id_list[num0]
            display_time = int(display_time_list[num0])
            
            #insert
            sql = ("INSERT INTO schedule (sche_id, sche_target_id, sche_display_time, sche_arrange_mode)"\
                +" VALUES ('sche0undecided', '"+target_id+"', "+str(display_time)+", " + str(arrange_mode_sn) + ")")
            db.cmd(sql)
            sql = ("SELECT sche_sn FROM schedule WHERE sche_id='sche0undecided' ORDER BY sche_sn ASC LIMIT 1")
            pure_result = db.query(sql)
            if len(pure_result)!=0:
                new_id = "sche" + "{0:010d}".format(int(pure_result[0][0]))
                sql = ("UPDATE schedule SET sche_id='" + new_id + "' WHERE sche_sn="+str(pure_result[0][0]))
                db.cmd(sql)
            else :
                db.close()
                return_msg["error"] = "may be another arrange.exe is working"
                return return_msg

        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

#The API connect mysql and clean non used schedule
def clean_schedule():
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        #connect to mysql
        db = mysql()
        db.connect()

        sql = "DELETE FROM schedule WHERE sche_is_used=0"
        db.cmd(sql)
        
        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg   


#The API connect mysql and clean up schedule and write it to the schedule.txt
def set_schedule_log(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        log_dir = ""
        max_is_used = 100
        is_used_count = 0
        try:
            log_dir = json_obj["board_py_dir"]
            max_is_used = json_obj["max_db_log"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        #connect to mysql
        db = mysql()
        db.connect()
        
        #count sche_is_used schedule
        sql = ("SELECT count(sche_sn) FROM schedule WHERE sche_is_used=1")
        pure_result = db.query(sql)
        try:
            is_used_count = int(pure_result[0][0])
        except:
            "DO NOTHING"
        
        #if log > max_is_used then clean up
        if is_used_count > max_is_used:
            #get schedule
            sql = ("SELECT * FROM schedule WHERE sche_is_used=1 ORDER BY sche_sn ASC LIMIT " + str(is_used_count - max_is_used))
            pure_result = db.query(sql)

            #generate log
            date_now = date.today()
            schedule_file = ("schedule_" + str(date_now.year) + "_" + str(date_now.month) + "_" + str(date_now.day) + ".txt")
            schedule_file = os.path.join(log_dir,("static/log/"+schedule_file))
            file_pointer = ''
            try:
                if not os.path.isfile(schedule_file) :
                    file_pointer = open(schedule_file, "w")
                else :
                    file_pointer = open(schedule_file, "a")

                for num1 in range(len(pure_result)):
                    write_str = ""
                    for num2 in range(len(pure_result[num1])):
                        write_str = write_str + str(pure_result[num1][num2]) + " "
                    write_str = write_str + "\n"
                    file_pointer.write(write_str)
                file_pointer.close()
            except:
                db.close()
                return_msg["error"] = "generate log error"
                return return_msg
            
            #delete schedule
            for num1 in range(len(pure_result)):
                sql = "DELETE FROM schedule WHERE sche_sn=" + str(pure_result[num1][0])
                try:
                    db.cmd(sql)
                except DB_Exception as e:
                    return_msg["error"] = e.args[1]
            if "error" in return_msg:
                db.close()
                return return_msg
        
        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

#future can write to log.txt. now just print it
def read_system_setting():
    return_msg = {}
    return_msg["result"] = "fail"
    file_name = "setting.txt"
    
    if not os.path.isfile(file_name) :
        return_msg["error"] = "file missing"
        return return_msg
    
    try:
        file_pointer = open(file_name,"r")
        for line in file_pointer:
            pure_data = []
            pure_data = line.rstrip('\n').split(' ')
            if pure_data[0] == "board_py_dir":
                return_msg["board_py_dir"] = pure_data[1]
            elif pure_data[0] == "shutdown":
                return_msg["shutdown"] = int(pure_data[1])
            elif pure_data[0] == "max_db_log":
                return_msg["max_db_log"] = int(pure_data[1])
            elif pure_data[0] == "min_db_activity":
                return_msg["min_db_activity"] = int(pure_data[1])
        file_pointer.close()
    except:
        return_msg["error"] = "read error"
        return return_msg

    return_msg["result"] = "success"
    return return_msg

#future can write to log.txt. now just print it
def read_arrange_mode():
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        #connect to mysql
        db = mysql()
        db.connect()

        #find arrange mode
        sql = ("SELECT armd_sn, armd_mode, armd_condition FROM arrange_mode WHERE armd_is_delete=0 and armd_is_expire=0 and "\
            +"(TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(armd_start_time) and TIME_TO_SEC(armd_end_time))"\
            +" ORDER BY armd_set_time DESC LIMIT 1")
        pure_result = db.query(sql)
        try:
            return_msg["arrange_sn"] = int(pure_result[0][0])
            return_msg["arrange_mode"] = int(pure_result[0][1])
            return_msg["condition"] = []
            
            if len(pure_result[0]) > 2  and pure_result[0][2] is not None:
                str_condition = pure_result[0][2].split(' ')
                for num1 in range(len(str_condition)):
                    return_msg["condition"].append(int(str_condition[num1]))
        except:
            db.close()
            return_msg["error"] = "no match schedule mode"
            return return_msg

        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

#
def crawler_cwb_img(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        server_dir = ""
        user_id = 1
        try:
            server_dir = json_obj["server_dir"]
            user_id = json_obj["user_id"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg
        data_type = 3
        now_time = time.time()
        send_obj = {}
        receive_obj = {}

        #connect to mysql
        db = mysql()
        db.connect()

        #find 氣像雲圖 type id 
        sql = "SELECT type_id FROM data_type WHERE type_name='氣像雲圖'"
        pure_result = db.query(sql)
        try:
            data_type = int(pure_result[0][0])
        except:
            db.close()
            return_msg["error"] = "no cwb img data type"
            return return_msg


        for num1 in range(60):
            target_img = 'CV1_TW_3600_' + time.strftime("%Y%m%d%H%M", time.localtime(now_time)) + '.png'
            url = 'http://www.cwb.gov.tw/V7/observe/radar/Data/HD_Radar/' + target_img
            try:
                request.urlretrieve(url, "static/img/"+target_img)
            except:
                now_time -= 60
                continue

            #delete old cwb img
            error_list_id = []
            sql = "SELECT img_id FROM image_data WHERE img_is_delete=0 and img_file_name like 'CV1_TW_3600_%'" 
            pure_result = db.query(sql)
            for num2 in range(len(pure_result)):
                try:                
                    send_obj["server_dir"] = server_dir
                    send_obj["target_id"] = str(pure_result[num2][0])
                    send_obj["user_id"] = user_id
                    receive_obj = delete_image_or_text_data(send_obj)
                    if receive_obj["result"] == "fail":
                        error_list_id.append(send_obj["target_id"])
                except:
                    error_list_id.append(send_obj["target_id"])
                    continue

            #mark old cwb img
            for num2 in range(len(error_list_id)):
                sql = "UPDATE image_data SET img_is_expire=1 WHERE img_is_expire=0 and img_is_delete=0 and img_id='" + str(error_list_id[num2]) + "'" 
                db.cmd(sql)

            #upload new file
            send_obj["server_dir"] = server_dir
            send_obj["file_type"] = data_type
            send_obj["file_dir"] = 'static/img/' + target_img
            send_obj["start_date"] = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            send_obj["end_date"] = time.strftime("%Y-%m-%d", time.localtime(time.time()+86400))
            send_obj["start_time"] = "00:00:00"
            send_obj["end_time"] = "23:59:59"
            send_obj["display_time"] = 5
            send_obj["user_id"] = user_id
            receive_obj = upload_image_insert_db(send_obj)
            #pprint(receive_obj)
            try:
                if receive_obj["result"] == "success":
                    filepath = receive_obj["img_system_dir"]
                    thumbnail_path = "static/thumbnail/"
                    thumbnail_path = os.path.join(thumbnail_path,receive_obj["img_thumbnail_name"])
                    im = Image.open(filepath)
                    im.thumbnail((100,100))
                    im.save(thumbnail_path)
                    #print(target_img)
                    break
                else:
                    db.close()
                    return_msg = receive_obj
                    return return_msg
            except:
                db.close()
                return_msg["error"] = "save thumbnail image fail"
                return return_msg
                
        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

def google_calendar_text():
    return_msg = {}
    return_msg["result"] = "fail"
    credentials = get_credentials()
    if not credentials:
        return_msg["error"] = "No credential file"
        return return_msg
    else:
        try:
            eventsResult = get_upcoming_events(credentials)
            events = eventsResult['items']
            for e in events:
                check_event_exist_or_insert(e)
                sleep(1.5)
            return_msg["result"] = "success"
            return return_msg
        except DB_Exception as e:
            return_msg["error"] = e.arg[1]
            return return_msg

def rule_base_agent(event):
    addition_msg = {}
    holidays = ['放假','假期','補假','休假']
    if '節' in event['summary']:
        addition_msg['title1'] = event['summary'] + '快樂'
        addition_msg['description'] = '｡:.ﾟヽ(*´∀`)ﾉﾟ.:｡'

    if any(holiday in event['summary'] for holiday in holidays):
        addition_msg['title2'] = '放假就是爽(*´∀`)~♥'

    if '期中預警' in event['summary']:
        addition_msg['title2'] = '退選單簽了沒？(,,・ω・,,)'
        addition_msg['description'] = ''

    if '考試' in event['summary']:
        addition_msg['title2'] = '考古題背完了沒?'
        addition_msg['description'] = '考試不作弊</br>三分靠賭運</br>七分靠運氣</br>猜錯當學弟</br>_(:3 」∠ )_'

    if 'title1' not in addition_msg:
        addition_msg['title1'] = event['summary']

    for key in ['title1','title2','description']:
        if key not in addition_msg:
            addition_msg[key] = ''

    return addition_msg

def check_event_exist_or_insert(event):
    event_id = event['id']
    db = mysql()
    db.connect()
    sql = 'SELECT COUNT(*) from text_data where text_invisible_title ="%s"' % event_id
    pure_result = db.query(sql)
    if pure_result[0][0]:
        # event existed
        # do nothing
        return
    else:
        send_msg = {}
        send_msg["server_dir"] = os.path.dirname(__file__)
        send_msg["file_type"] = 6
        send_msg["start_date"] = datetime.datetime.strftime(datetime.datetime.strptime(event['start']['date'],'%Y-%m-%d') - datetime.timedelta(3),'%Y-%m-%d')
        send_msg["end_date"] = event['start']['date']
        send_msg["start_time"] = ""
        send_msg["end_time"] = ""
        send_msg["display_time"] = 5
        send_msg["user_id"] = 1
        send_msg["invisible_title"] = event_id
        receive_msg = upload_text_insert_db(send_msg)
        addition_msg = rule_base_agent(event)
        text_file = {   "con" : send_msg["end_date"],
                        "title1" : addition_msg['title1'],
                        "title2" : addition_msg['title2'],
                        "description": addition_msg['description'],
                        "background_color" : "#984B4B"
        }
        with open(receive_msg["text_system_dir"],"w") as fp:
            print(json.dumps(text_file),file=fp)

#crawler google drive image
def crawler_google_drive_img(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        server_dir = ""
        user_id = 1
        try:
            server_dir = json_obj["server_dir"]
            user_id = json_obj["user_id"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg
        data_type = 4
        now_time = time.time()
        send_obj = {}
        receive_obj = {}

        #connect to mysql
        db = mysql()
        db.connect()

        #find google_drive_image type id 
        sql = "SELECT type_id FROM data_type WHERE type_name='google_drive_image'"
        pure_result = db.query(sql)
        try:
            data_type = int(pure_result[0][0])
        except:
            db.close()
            return_msg["error"] = "no google_drive_image data type"
            return return_msg

        #get google credentials
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)

        #set time
        start_time = time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime(now_time-86400))
        results = service.files().list(
            q="modifiedTime > '" + start_time + "' and mimeType contains 'image/'", 
            fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        if not items:
            "No images found."
        else:
            #pprint(items)
            for item in items:
                #print('##{0} ({1})'.format(item['name'], item['id']))
                file_name = item['id'] + os.path.splitext(item['name'])[1]
                download_file_place = os.path.join(server_dir, "static/img/"+file_name)
                
                #check if file is existed
                sql = "SELECT COUNT(*) FROM image_data WHERE img_is_expire=0 and img_is_delete=0 "
                sql = sql + "and type_id=" + str(data_type) + " and img_file_name='" + file_name + "'"
                pure_result = db.query(sql)
                if pure_result[0][0]:
                    #image existed
                    continue
            
                #download files
                request = service.files().get_media(fileId=item['id'])
                fh = io.FileIO(download_file_place, mode='wb')
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
                
                #upload new file
                send_obj["server_dir"] = server_dir
                send_obj["file_type"] = data_type
                send_obj["file_dir"] = 'static/img/' + file_name
                send_obj["start_date"] = time.strftime("%Y-%m-%d", time.localtime(time.time()))
                send_obj["end_date"] = time.strftime("%Y-%m-%d", time.localtime(time.time()+86400*7))
                send_obj["start_time"] = "00:00:00"
                send_obj["end_time"] = "23:59:59"
                send_obj["display_time"] = 3
                send_obj["user_id"] = user_id
                receive_obj = upload_image_insert_db(send_obj)
                #pprint(receive_obj)
                #save thumbnail image
                try:
                    if receive_obj["result"] == "success":
                        filepath = receive_obj["img_system_dir"]
                        thumbnail_path = "static/thumbnail/"
                        thumbnail_path = os.path.join(thumbnail_path,receive_obj["img_thumbnail_name"])
                        im = Image.open(filepath)
                        im.thumbnail((100,100))
                        im.save(thumbnail_path)
                        #print(thumbnail_path)
                    else:
                        db.close()
                        return_msg = receive_obj
                        return return_msg
                except:
                    db.close()
                    return_msg["error"] = "save thumbnail image fail"
                    return return_msg
                
        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg 

def crawler_inside_news():
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        data_type = 5

        #connect to mysql
        db = mysql()
        db.connect()
        #check if table 'news' exists
        check_sql = "SELECT count(*) \
                     FROM information_schema.tables \
                     WHERE table_schema = 'broadcast'\
                     AND table_name = 'news'"
        check = db.query(check_sql)
        if check[0][0] == 0:
            create_news_table()

        #check inside data type exist or not 
        check_sql = "SELECT COUNT(*) FROM data_type WHERE  type_name='inside'"
        exist = db.query(check_sql)
        if exist[0][0] == 0:
             create_news_data_types()

        #start grab INSIDE info
        try:
            grab_inside_articles()
        except:
            return_msg["error"] = "ERROR occurs in INSIDE crawler. Please check the correction of news_crawler"
            return return_msg

        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

#deal with defunct 
def CHLD_handler(para1, para2):
    try:
        os.waitpid(-1, os.WNOHANG)
    except:
        send_obj = {}
        send_obj["result"] = "fail" 
        send_obj["error"] = ("kill : ( " + str(para1) + ", " + str(para2)+" ) ")
        set_system_log(send_obj)

#future can write to log.txt. now just print it
def set_system_log(json_obj):
    return_msg = {}
    return_msg["result"] = "fail"
    file_name = "static/log/impossible_error.txt"
    debug = 1
    file_pointer = ""

    if debug == 1:
        try:
            if json_obj["result"]=="fail":
                print("#error : " + json_obj["error"])
                if not os.path.isfile(file_name) :
                    file_pointer = open(file_name, "w")
                else :
                    file_pointer = open(file_name, "a")
                str_write = str(time.time()) + " fail : " + str(json_obj["error"]) + "\n"
                file_pointer.write(str_write)
                file_pointer.close()
        except:
            return_msg["result"] = "fail to print error"
            return return_msg
    
    return_msg["result"] = "success"
    return return_msg
        

    
    

def main():
    just_startup = 1
    board_py_dir = ""
    shutdown = 0
    max_db_log = 100
    min_db_activity = 10
    arrange_mode_change = 0
    arrange_sn = 0
    arrange_mode = 0
    check_file_dir = "NO_FILE"
    condition = []
    send_obj = {}
    receive_obj = {}

    #for non blocking fork
    signal.signal(signal.SIGCHLD, CHLD_handler)

    #read initial setting
    raw_time = time.time()
    now_time = time.localtime(raw_time)
    receive_obj = read_system_setting()
    if receive_obj["result"] == "success":
        board_py_dir = str(receive_obj["board_py_dir"])
        shutdown = int(receive_obj["shutdown"])
        max_db_log = int(receive_obj["max_db_log"])
        min_db_activity = int(receive_obj["min_db_activity"])
    receive_obj = read_arrange_mode()
    if receive_obj["result"] == "success":
        arrange_sn = int(receive_obj["arrange_sn"])
        arrange_mode = int(receive_obj["arrange_mode"])
        condition = receive_obj["condition"]

    #time initial
    raw_time = time.time()
    now_time = time.localtime(raw_time)
    alarm_read_system_setting = raw_time + 300.0
    alarm_expire_data_check = raw_time + 3.0
    alarm_set_schedule_log = raw_time + 10.0
    alarm_load_next_schedule = raw_time
    alarm_add_schedule = 1960380833.0
    alarm_crawler_cwb_img = raw_time + 7.0
    alarm_google_calendar_text = raw_time + 5.0
    alarm_crawler_google_drive_img = raw_time + 13.0
    alarm_crawler_inside = raw_time + 15.0

    #start scheduling
    while shutdown == 0:
        raw_time = time.time()
        now_time = time.localtime(raw_time)
        
        #read_system_setting
        if raw_time >= alarm_read_system_setting:
            print("#1 "+str(raw_time))
            receive_obj = read_system_setting()
            if receive_obj["result"] == "success":
                board_py_dir = str(receive_obj["board_py_dir"])
                shutdown = int(receive_obj["shutdown"])
                max_db_log = int(receive_obj["max_db_log"])
                min_db_activity = int(receive_obj["min_db_activity"])
            else :
                receive_obj["error"] = "read_system_setting : " + receive_obj["error"]
                set_system_log(receive_obj)
            alarm_read_system_setting = raw_time + 300.0
        
        #expire_data_check
        if raw_time >= alarm_expire_data_check:
            print("#2 "+str(raw_time))
            try:
                newpid = os.fork()
                if newpid == 0: #child
                    shutdown = 1
                    receive_obj = expire_data_check()
                    if receive_obj["result"] == "success":
                        "DO NOTHING"
                    else :
                        receive_obj["error"] = "expire_data_check : " + receive_obj["error"]
                        set_system_log(receive_obj)
                    os._exit(0)
                else: #Parent
                    alarm_expire_data_check = raw_time + 1800.0
            except:
                receive_obj["result"] = "fail"
                receive_obj["error"] = "fork1 error"
                set_system_log(receive_obj)
                alarm_expire_data_check = raw_time + 3.0
        
        #set_schedule_log
        if raw_time >= alarm_set_schedule_log:
            print("#3 "+str(raw_time))
            try:
                newpid = os.fork()
                if newpid == 0: #child
                    shutdown = 1
                    send_obj["board_py_dir"] = board_py_dir
                    send_obj["max_db_log"] = max_db_log
                    receive_obj = set_schedule_log(send_obj)
                    if receive_obj["result"] == "success":
                        "DO NOTHING"
                    else :
                        receive_obj["error"] = "set_schedule_log : " + receive_obj["error"]
                        set_system_log(receive_obj)
                    os._exit(0)
                else: #Parent
                    alarm_set_schedule_log = raw_time + 1800.0
            except:
                receive_obj["result"] = "fail"
                receive_obj["error"] = "fork2 error"
                set_system_log(receive_obj)
                alarm_set_schedule_log = raw_time + 3.0
            

        #load next schedule
        if not os.path.isfile(check_file_dir) or raw_time >= alarm_load_next_schedule:
            print("#4 "+str(raw_time))
            #mark now activity
            if just_startup == 0:
                receive_obj = mark_now_activity()
                if receive_obj["result"] == "success":
                    "DO NOTHING"
                else :
                    if receive_obj["error"] == "no schedule":
                        "DO NOTHING"
                    else :
                        receive_obj["error"] = "mark_now_activity : " + receive_obj["error"]
                        set_system_log(receive_obj)
            
            #load next schedule
            send_obj["board_py_dir"] = board_py_dir
            receive_obj = load_next_schedule(send_obj)
            if receive_obj["result"] == "success":
                just_startup = 0
                alarm_load_next_schedule = raw_time + int(receive_obj["display_time"])
                check_file_dir = receive_obj["file"]
                if int(receive_obj["last_activity"]) < min_db_activity:
                    alarm_add_schedule = raw_time
            else :
                if receive_obj["error"] == "no schedule":
                    alarm_add_schedule = raw_time
                    alarm_load_next_schedule = raw_time + 1.0
                    just_startup = 1
                receive_obj["error"] = "load_next_schedule : " + receive_obj["error"]
                set_system_log(receive_obj)

        #add_schedule
        if raw_time >= alarm_add_schedule:
            print("#5 "+str(raw_time))
            #get arrange mode
            receive_obj = read_arrange_mode()
            if receive_obj["result"] == "success":
                if arrange_sn != int(receive_obj["arrange_sn"]):
                    arrange_mode_change = 1
                    arrange_sn = int(receive_obj["arrange_sn"])
                    arrange_mode = int(receive_obj["arrange_mode"])
                    condition = receive_obj["condition"]
            else :
                receive_obj["error"] = "read_arrange_mode : " + receive_obj["error"]
                set_system_log(receive_obj)
                arrange_mode_change = 0
                
            
            try:
                newpid = os.fork()
                if newpid == 0: #child
                    shutdown = 1
                    #find activity
                    send_obj["arrange_mode"] = arrange_mode
                    send_obj["condition"] = condition
                    receive_obj = find_acticity(send_obj)
                    if receive_obj["result"] == "success":
                        "DO NOTHING"
                    else :
                        receive_obj["error"] = "find_acticity : " + receive_obj["error"]
                        set_system_log(receive_obj)
                        os._exit(0)

                    #use add or edit schedule
                    send_obj["next_sn"] = 3
                    send_obj["target_id"] = receive_obj["target_id"]
                    send_obj["display_time"] = receive_obj["display_time"]
                    send_obj["arrange_sn"] = arrange_sn
                    if arrange_mode_change == 0:
                        receive_obj = add_schedule(send_obj)
                    else :
                        receive_obj = edit_schedule(send_obj)
                    if receive_obj["result"] == "success":
                        "DO NOTHING"
                    else :
                        receive_obj["error"] = "add_or_edit_schedule : " + receive_obj["error"]
                        set_system_log(receive_obj)
                        os._exit(0)
                    os._exit(0)
                else: #Parent
                    alarm_add_schedule = 1960380833.0
                    arrange_mode_change = 0
            except:
                receive_obj["result"] = "fail"
                receive_obj["error"] = "fork3 error"
                set_system_log(receive_obj)
                arrange_mode_change = 0
                alarm_add_schedule = raw_time + 3
        
        #crawl cwb radar image
        if raw_time >= alarm_crawler_cwb_img:
            print("#6 "+str(raw_time))
            try:
                newpid = os.fork()
                if newpid == 0: #child
                    shutdown = 1
                    send_obj["server_dir"] = board_py_dir
                    send_obj["user_id"] = 1
                    receive_obj = crawler_cwb_img(send_obj)
                    if receive_obj["result"] == "success":
                        "DO NOTHING"
                    else :
                        receive_obj["error"] = "crawler_cwb_img : " + receive_obj["error"]
                        set_system_log(receive_obj)
                    os._exit(0)
                else: #Parent
                    alarm_crawler_cwb_img = raw_time + 3600.0
            except:
                receive_obj["result"] = "fail"
                receive_obj["error"] = "fork4 error"
                set_system_log(receive_obj)
                alarm_crawler_cwb_img = raw_time + 600.0

        #google calendar add to text data
        if raw_time >= alarm_google_calendar_text:
            print("#7 "+str(raw_time))
            try:
                newpid = os.fork()
                if newpid == 0: #child
                    shutdown = 1
                    receive_obj = google_calendar_text()
                    if receive_obj["result"] == "success":
                        "DO NOTHING"
                    else:
                        receive_obj["error"] = "google_calendar_text" + receive_obj["error"]
                        set_system_log(receive_obj)
                    os._exit(0)
                else: #Parent
                    alarm_google_calendar_text = raw_time + 43200.0
            except:
                receive_obj["result"] = "fail"
                receive_obj["error"] = "fork5 error"
                set_system_log(receive_obj)
                alarm_google_calendar_text = raw_time + 10.0
        
        #google drive add to text data
        if raw_time >= alarm_crawler_google_drive_img:
            print("#8 "+str(raw_time))
            try:
                newpid = os.fork()
                if newpid == 0: #child
                    shutdown = 1
                    send_obj["server_dir"] = board_py_dir
                    send_obj["user_id"] = 1
                    receive_obj = crawler_google_drive_img(send_obj)
                    if receive_obj["result"] == "success":
                        "DO NOTHING"
                    else :
                        receive_obj["error"] = "crawler_google_drive_img : " + receive_obj["error"]
                        set_system_log(receive_obj)
                    os._exit(0)
                else: #Parent
                    alarm_crawler_google_drive_img = raw_time + 3600.0
            except:
                receive_obj["result"] = "fail"
                receive_obj["error"] = "fork6 error"
                set_system_log(receive_obj)
                alarm_crawler_google_drive_img = raw_time + 600.0

        #crawler INSIDE
        if raw_time >= alarm_crawler_inside:
            print("#9 "+str(raw_time))
            try:
                newpid = os.fork()
                if newpid == 0: #child
                    shutdown = 1
                    receive_obj = crawler_inside_news()
                    if receive_obj["result"] == "success":
                        "DO NOTHING"
                    else :
                        receive_obj["error"] = "crawler_inside_news : " + receive_obj["error"]
                        set_system_log(receive_obj)
                    os._exit(0)
                else: #Parent
                    alarm_crawler_inside = raw_time + 3600.0
            except:
                receive_obj["result"] = "fail"
                receive_obj["error"] = "fork7 error"
                set_system_log(receive_obj)
                alarm_crawler_inside = raw_time + 600.0

        #delay
        sleep(0.1)
    print("arrange_schedule shutdown")
    sleep(10)
    return 1

if __name__ == "__main__":
    main()


