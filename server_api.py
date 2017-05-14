from mysql import mysql
from mysql import DB_Exception
from shutil import copyfile
from display_api import get_user_id
from PIL import Image
import os
import os.path
import shutil
import bcrypt
import json
import tornado
import time

from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import httplib2

from apiclient import discovery
import datetime
#
def add_like_count(db, target_id):
    try:
        sql = ""
        if target_id[0:4]=="imge":
            sql = ("UPDATE image_data SET img_like_count=img_like_count+1 WHERE img_id='" + str(target_id) + "'")
        elif target_id[0:4]=="text":
            sql = ("UPDATE text_data SET text_like_count=text_like_count+1 WHERE text_id='" + str(target_id) + "'")
        else :
            return 0
        db.cmd(sql)
        
        return 1
    except:
        return 0
#
def find_now_schedule(db):
    try:
        sql = "SELECT sche_target_id FROM schedule WHERE sche_is_used=0 ORDER BY sche_sn ASC LIMIT 1"
        pure_result = db.query(sql)
        return str(pure_result[0][0])
    except:
        return 0
#
def add_now_like_count():
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        db = mysql()
        db.connect()

        #find image or text id from current schedule
        target_id = find_now_schedule(db)
        if target_id==0:
            db.close()
            return_msg["error"] = "can not find current schedule"
            return return_msg
            
        #add like count
        if add_like_count(db, target_id)==0:
            db.close()
            return_msg["error"] = "can not add like count"
            return return_msg

        return_msg["result"] = "success"
        return return_msg
                
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg 
    except Exception as e:
        db.close()
        return_msg["error"] = e
        return return_msg
#
def check_bluetooth_mode_available():
    file_dir = "setting"
    file_name = "server_setting.txt"
    #check setting file exist
    if not os.path.exists(file_dir):
        return 0
    if not os.path.isfile(file_dir+'/'+file_name):
        return 0
    
    try:
        #read setting file
        filename = file_dir + '/' + file_name
        file_pointer = open(filename,"r")
        bluetooth_available = 0
        for line in file_pointer:
            pure_data = []
            pure_data = line.rstrip('\n').split(' ')
            if pure_data[0] == "bluetooth_enable":
                bluetooth_available = int(pure_data[1])
        file_pointer.close()
        
        #check function available
        if bluetooth_available==1:
            return 1
        else :
            return 0
        
        return 0
    except :
        return 0
#
def find_user_by_bluetooth(db, bluetooth_id):
    try:
        sql = "SELECT user_id FROM user WHERE user_bluetooth_id='" + str(bluetooth_id) + "'"
        pure_result = db.query(sql)
        return int(pure_result[0][0])
    except:
        return 0
#
def load_now_user_prefer(db, user_id):
    try:
        sql = "SELECT "
        now_hour = time.localtime(time.time())[3]
        #use now time to choose preference rule
        if now_hour >= 7 and now_hour < 11:
            sql = sql + "pref_data_type_01 "
        elif now_hour >= 11 and now_hour < 13:
            sql = sql + "pref_data_type_02 "
        elif now_hour >= 13 and now_hour < 18:
            sql = sql + "pref_data_type_03 "
        elif now_hour >= 18 and now_hour < 22:
            sql = sql + "pref_data_type_04 "
        else :
            sql = sql + "pref_data_type_05 "
        
        sql = sql + "FROM user_prefer WHERE pref_is_delete=0 and user_id=" + str(user_id)
        sql = sql + " ORDER BY pref_set_time DESC LIMIT 1"
        pure_result = db.query(sql)
        
        #reshap pref_data_type_XX from varchar to int array
        data_type_array = []
        if len(pure_result) > 0  and pure_result[0][0] is not None:
            str_condition = pure_result[0][0].split(' ')
            for num1 in range(len(str_condition)):
                data_type_array.append(int(str_condition[num1]))
        else:
            return -1
        
        return data_type_array
    except:
        return -1
#
def insert_customized_schedule(prefer_data_type):
    from arrange_schedule import find_acticity
    from arrange_schedule import edit_schedule

    try:
        receive_msg = {}
        send_msg = {}

        #find customer prefer information
        send_msg["arrange_mode"]=5
        send_msg["condition"]=prefer_data_type
        receive_msg = find_acticity(send_msg)
        if receive_msg["result"]=="fail":
            return -1
        target_id = receive_msg["target_id"][0]
        display_time = receive_msg["display_time"][0]

        #insert infromation to schedule
        send_msg["next_sn"] = 1
        send_msg["target_id"] = [target_id]
        send_msg["display_time"] = [display_time]
        send_msg["arrange_sn"] = 0
        receive_msg = edit_schedule(send_msg)
        if receive_msg["result"]=="fail":
            return -1

        return 1
    except:
        return -1
#
def deal_with_bluetooth_id(bluetooth_id):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        db = mysql()
        db.connect()
        user_id=0

        #check bluetooth mode available
        if check_bluetooth_mode_available()==0:
            db.close()
            return_msg["error"] = "the bluetooth function is closed"
            return return_msg

        #find user by bluetooth id
        user_id = find_user_by_bluetooth(db, bluetooth_id)
        if user_id==0:
            db.close()
            return_msg["error"] = "no such bluetooth id"
            return return_msg

        #load now user prefer
        prefer_data_type = load_now_user_prefer(db, user_id)
        if prefer_data_type == -1:
            db.close()
            return_msg["error"] = "no prefer data type"
            return return_msg

        #insert customized schedule to next schedule
        receive_result = insert_customized_schedule(prefer_data_type)
        if receive_result == -1:
            db.close()
            return_msg["error"] = "insert fail"
            return return_msg
    
        return_msg["result"] = "success"
        return return_msg
        
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg 
    except Exception as e:
        db.close()
        return_msg["error"] = e
        return return_msg
#
def get_user_name_and_password(handler):
    return_msg = {}
    return_msg['user_name'] = tornado.escape.xhtml_escape(handler.get_argument("username"))
    return_msg['user_password'] = tornado.escape.xhtml_escape(handler.get_argument("password"))
    return return_msg
#
def check_user_existed_or_signup(user_info):
    try:
        return_msg = {}
        db = mysql()
        db.connect()

        cursor = db.cursor

        sql = 'select Count(*) from `user` where `user_name`="%s"' % user_info['user_name']
        pure_result = db.query(sql)

        is_existed = pure_result[0][0]
        if is_existed:
            return_msg['flash'] = 'The name "%s" has been used' % user_info['user_name']
            return return_msg

        hashed_passwd = bcrypt.hashpw(user_info['user_password'].encode('utf-8'),bcrypt.gensalt())
        ret = cursor.execute('insert into `user` (`user_name`,`user_password`) values (%s,%s)',(user_info['user_name'],hashed_passwd))
        db.db.commit()

        return_msg['flash'] = 'User "%s" create success!' % user_info['user_name']
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

def check_user_password(user_info):
    try:
        return_msg = {}
        db = mysql()
        db.connect()

        sql = 'select `user_password` from user where `user_name` = "%s"' % user_info['user_name']
        pure_result = db.query(sql)

        if len(pure_result) == 0:
            return_msg['fail'] = 'No such user'
            return return_msg

        hashed_passwd = pure_result[0][0].encode('utf-8')
        if bcrypt.checkpw(user_info['user_password'].encode('utf-8'),hashed_passwd):
            return_msg['success'] = 'Hello %s' % user_info['user_name']
        else:
            return_msg['fail'] = 'Wrong password'

        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

def get_upload_meta_data(handler):
    meta_data = {}
    user_name = handler.get_current_user().decode('utf-8')

    meta_data["server_dir"] = os.path.dirname(__file__)
    meta_data["file_type"] = tornado.escape.xhtml_escape(handler.get_argument("data_type"))
    meta_data["start_date"] = tornado.escape.xhtml_escape(handler.get_argument("start_date"))
    meta_data["end_date"] = tornado.escape.xhtml_escape(handler.get_argument("end_date"))
    meta_data["start_time"] = tornado.escape.xhtml_escape(handler.get_argument("start_time"))
    meta_data["end_time"] = tornado.escape.xhtml_escape(handler.get_argument("end_time"))
    meta_data["display_time"] = tornado.escape.xhtml_escape(handler.get_argument("display_time"))
    meta_data["user_id"] = get_user_id(user_name)

    return meta_data

def get_upload_text_data(handler):
    text_file = {}

    text_file['con'] = tornado.escape.xhtml_escape(handler.get_argument('con')).replace('&amp;nbsp','&nbsp').replace('&lt;br&gt;','<br>')
    text_file['title1'] = tornado.escape.xhtml_escape(handler.get_argument('title1')).replace('&amp;nbsp','&nbsp').replace('&lt;br&gt;','<br>')
    text_file['title2'] = tornado.escape.xhtml_escape(handler.get_argument('title2')).replace('&amp;nbsp','&nbsp').replace('&lt;br&gt;','<br>')
    text_file['description'] = tornado.escape.xhtml_escape(handler.get_argument('description')).replace('&lt;br&gt;','<br>').replace('&amp;nbsp','&nbsp')
    text_file['year'] = tornado.escape.xhtml_escape(handler.get_argument('year'))
    text_file['month'] = tornado.escape.xhtml_escape(handler.get_argument('month'))
    text_file['background_color'] = tornado.escape.xhtml_escape(handler.get_argument('background_color'))

    return text_file

def store_image(filepath,file_content):
    with open(filepath,'wb') as fp:
        fp.write(file_content)
    
def store_thumbnail_image(file_path,thumbnail_path):
    img = Image.open(file_path)
    img.thumbnail((100,100))
    img.save(thumbnail_path)

def get_img_meta(img_id):
    try:
        db = mysql()
        db.connect()
        sql = 'select * from image_data where img_is_delete = 0 and img_id = "%s"' % img_id
        return db.query(sql)[0]
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

def get_text_meta(text_id):
    try:
        db = mysql()
        db.connect()
        sql = 'select * from text_data where text_is_delete = 0 and text_id = "%s"' % text_id
        return db.query(sql)[0]
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

def check_user_level(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        user_id = 0
        user_level = 0
        compare_level = []
        compare_ans = []
        try:
            user_id = json_obj["user_id"]
            compare_level = json_obj["compare_level"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        #connect to mysql
        db = mysql()
        db.connect()
        
        #check user level
        sql = "SELECT user_level FROM user WHERE user_id=" + str(user_id)
                
        pure_result = db.query(sql)
        try:
            user_level = int(pure_result[0][0])
        except:
            db.close()
            return_msg["error"] = "no such user id : " + str(user_id)
            return return_msg

        for num1 in range(len(compare_level)):
            if int(compare_level[num1]) >= user_level:
                compare_ans.append("pass")
            else :
                compare_ans.append("fail")

        db.close()

        return_msg["compare_ans"] = compare_ans
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

#
def upload_image_insert_db(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        try:
            server_dir = json_obj["server_dir"]
            type_id = json_obj["file_type"]
            img_file_dir = json_obj["file_dir"]
            img_start_date = json_obj["start_date"]
            img_end_date = json_obj["end_date"]
            img_start_time = json_obj["start_time"]
            img_end_time = json_obj["end_time"]
            img_display_time = json_obj["display_time"]
            user_id = json_obj["user_id"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        img_id = ""
        img_file_name = os.path.split(img_file_dir)[1]
        img_new_file_dir = ""
        user_level_low_bound = 100
        #default
        if len(img_start_time)==0:
            img_start_time = "00:00:00"
        if len(img_end_time)==0:
            img_end_time = "23:59:59"

        #connect to mysql
        db = mysql()
        db.connect()
        
        #check user level
        sql = ("SELECT user_level FROM user WHERE user_id=" + str(user_id))
        pure_result = db.query(sql)
        try: 
            if pure_result[0][0] < user_level_low_bound:
                db.close()
                return_msg["error"] = "user right is too low"
                return return_msg
        except:
            db.close()
            return_msg["error"] = "no such user id : " + str(user_id)
            return return_msg
        
        #get new file place
        sql = ("SELECT type_dir FROM data_type WHERE type_id=" + str(type_id))
        pure_result = db.query(sql)
        try:
            img_new_file_dir = os.path.join(server_dir, "static/"+str(pure_result[0][0]))
        except:
            db.close()
            return_msg["error"] = "no such type id : " + str(type_id)
            return return_msg
        
        
        #generate new id
        sql = ("SELECT img_id FROM image_data ORDER BY img_upload_time DESC LIMIT 1")
        pure_result = db.query(sql)
        try:
            img_id =  int(pure_result[0][0][4:]) + 1
            img_id = "imge" + "{0:010d}".format(img_id)
        except:
            img_id = "imge0000000001"
            #db.close()
            #return_msg["error"] = "no basic image"
            #return return_msg
        

        img_system_name = img_id + os.path.splitext(img_file_name)[1]
        img_thumbnail_name = "thumbnail_" + img_system_name
        img_system_dir = os.path.join(img_new_file_dir, img_system_name)
        try:
            copyfile(img_file_dir, img_system_dir)
            if os.path.isfile(img_file_dir) and os.path.isfile(img_system_dir):
                os.remove(img_file_dir)
        except:
            try:
                if os.path.isfile(img_file_dir) and os.path.isfile(img_system_dir):
                    os.remove(img_system_dir)
            except:
                "DO NOTHING"
            db.close()
            return_msg["error"] = "copy or remove file error"
            return return_msg
        
        
        #insert images data to mysql
        sql = "INSERT image_data " \
                +" (`img_id`, `type_id`, `img_system_name`, `img_thumbnail_name`, `img_file_name`, `img_start_date`, `img_end_date`, `img_start_time`, `img_end_time`, `img_display_time`, `user_id`) " \
                +" VALUE " \
                +" ( \"" + img_id + "\", " \
                + str(type_id) + ", " \
                + "\"" + img_system_name + "\", " \
                + "\"" + img_thumbnail_name + "\", " \
                + "\"" + img_file_name + "\", " \
                + "\"" + img_start_date + "\", " \
                + "\"" + img_end_date + "\", " \
                + "\"" + img_start_time + "\", " \
                + "\"" + img_end_time + "\", " \
                + str(img_display_time) + ", " \
                + str(user_id) + " ) " 
        try:
            db.cmd(sql)
        except DB_Exception as e:
            return_msg["error"] = "insert mysql error please check file system " + img_system_dir
            try:
                copyfile(img_system_dir, img_file_dir)
                if os.path.isfile(img_file_dir) and os.path.isfile(img_system_dir):
                    os.remove(img_system_dir)
                return_msg["error"] = "insert mysql error please check file system " + img_file_dir
            except:
                "DO NOTHING"
            db.close()
            return return_msg
        
        db.close()

        return_msg["img_id"] = img_id
        return_msg["img_system_dir"] = img_system_dir
        return_msg["img_thumbnail_name"] = img_thumbnail_name
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg
    
    
#
def edit_image_data(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        try:
            server_dir = json_obj["server_dir"]
            img_id = json_obj["img_id"]
            type_id = json_obj["file_type"]
            img_start_date = json_obj["start_date"]
            img_end_date = json_obj["end_date"]
            img_start_time = json_obj["start_time"]
            img_end_time = json_obj["end_time"]
            img_display_time = json_obj["display_time"]
            user_id = json_obj["user_id"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        user_level_low_bound = 100
        user_level_high_bound = 10000
        img_type_id = 0
        
        #connect to mysql
        db = mysql()
        db.connect()
        
        #check user level
        sql = ("SELECT user_level FROM user WHERE user_id=" + str(user_id))
        pure_result = db.query(sql)
        try: 
            user_level = pure_result[0][0]
            if user_level < user_level_low_bound:
                db.close()
                return_msg["error"] = "user right is too low"
                return return_msg
            #check self image
            sql = ("SELECT user_id, type_id FROM image_data WHERE img_id=\"" + img_id + "\"")
            pure_result = db.query(sql)
            try:
                if pure_result[0][0] != user_id and user_level < user_level_high_bound:
                    db.close()
                    return_msg["error"] = "can not modify other user image "
                    return return_msg
                img_type_id = pure_result[0][1]
            except:
                db.close()
                return_msg["error"] = "no such image id : " + img_id
                return return_msg
        except:
            db.close()
            return_msg["error"] = "no such user id : " + str(user_id)
            return return_msg
        
        
        #check if we need to move the file
        old_dir = ""
        new_dir = ""
        if img_type_id == type_id:
            "DO NOTHING"
        else :
            #get img_system_name
            sql = ("SELECT img_system_name FROM image_data WHERE img_id=\"" + img_id + "\"")
            pure_result = db.query(sql)
            try: 
                old_dir = pure_result[0][0]
                new_dir = pure_result[0][0]
            except:
                db.close()
                return_msg["error"] = "no such image id : " + img_id
                return return_msg
            
            #get old image type dir
            sql = ("SELECT type_dir FROM data_type WHERE type_id=" + str(img_type_id))
            pure_result = db.query(sql)
            try: 
                old_dir = pure_result[0][0] + old_dir
            except:
                db.close()
                return_msg["error"] = "no such image type : " + str(img_type_id)
                return return_msg
                    
            #get new image type dir     
            sql = ("SELECT type_dir FROM data_type WHERE type_id=" + str(type_id))
            pure_result = db.query(sql)
            try: 
                new_dir = pure_result[0][0] + new_dir
            except:
                db.close()
                return_msg["error"] = "no such image type : " + str(type_id)
                return return_msg
            
            #check if we need to move the file
            if old_dir == new_dir:
                "DO NOTHING"
            else :
                try:
                    old_dir = os.path.join(server_dir,"static/"+old_dir)
                    new_dir = os.path.join(server_dir,"static/"+new_dir)
                    copyfile(old_dir, new_dir)
                    if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                        os.remove(old_dir)
                except:
                    try:
                        if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                            os.remove(new_dir)
                    except:
                        "DO NOTHING"
                    db.close()
                    return_msg["error"] = "move file error : " + old_dir
                    return return_msg
        
        #start to modify mysql
        sql = ("UPDATE image_data " \
                +" SET type_id=" + str(type_id) + ", " \
                +" img_start_date=\"" + img_start_date + "\", " \
                +" img_end_date=\"" + img_end_date + "\", " \
                +" img_start_time=\"" + img_start_time + "\", " \
                +" img_end_time=\"" + img_end_time + "\", " \
                +" img_display_time=" + str(img_display_time) + ", " \
                +" img_last_edit_user_id=\"" + str(user_id) + "\" " \
                +" WHERE img_id=\"" + img_id + "\"")
        try:
            db.cmd(sql)
        except DB_Exception as e:
            try:
                copyfile(new_dir, old_dir)
                if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                    os.remove(new_dir)
            except:
                try:
                    if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                        os.remove(old_dir)
                except:
                    db.close()
                    return_msg["error"] = "move file error : duplicate files : " + old_dir
                    return return_msg
                db.close()
                return_msg["error"] = "move file error : " + new_dir
                return return_msg
            db.close()
            return_msg["error"] = "update mysql error"
            return return_msg

        db.close()
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg


#never debug this function
def upload_text_insert_db(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        server_dir = ""
        type_id = 1
        text_start_date = ""
        text_end_date = ""
        text_start_time = ""
        text_end_time = ""
        text_display_time = 5
        user_id = ""
        try:
            server_dir = json_obj["server_dir"]
            type_id = json_obj["file_type"]
            text_start_date = json_obj["start_date"]
            text_end_date = json_obj["end_date"]
            text_start_time = json_obj["start_time"]
            text_end_time = json_obj["end_time"]
            text_display_time = json_obj["display_time"]
            user_id = json_obj["user_id"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        text_id = ""
        system_file_dir = ""
        text_system_name = ""
        user_level_low_bound = 100
        #default
        if len(text_start_time)==0:
            text_start_time = "00:00:00"
        if len(text_end_time)==0:
            text_end_time = "23:59:59"

        #connect to mysql
        db = mysql()
        db.connect()
        
        #check user level
        sql = ("SELECT user_level FROM user WHERE user_id=" + str(user_id))
        pure_result = db.query(sql)
        try: 
            if int(pure_result[0][0]) < user_level_low_bound:
                db.close()
                return_msg["error"] = "user right is too low"
                return return_msg
        except:
            db.close()
            return_msg["error"] = "no such user id : " + str(user_id)
            return return_msg

        #generate new id
        sql = ("SELECT text_id FROM text_data ORDER BY text_upload_time DESC LIMIT 1")
        pure_result = db.query(sql)
        try:
            text_id =  int(pure_result[0][0][4:]) + 1
            text_id = "text" + "{0:010d}".format(text_id)
        except:
            text_id = "text0000000001"
            #db.close()
            #return_msg["error"] = "no basic image"
            #return return_msg

        if "invisible_title" in json_obj:
            invisible_title = json_obj["invisible_title"]
        else:
            invisible_title = text_id
        
        #get file place
        sql = ("SELECT type_dir FROM data_type WHERE type_id=" + str(type_id))
        pure_result = db.query(sql)
        try:
            text_system_name = text_id + ".txt"
            system_file_dir = os.path.join(server_dir, "static/"+str(pure_result[0][0]))
            system_file_dir = os.path.join(system_file_dir, text_system_name)
        except:
            db.close()
            return_msg["error"] = "no such type id : " + str(type_id)
            return return_msg
        
        #insert images data to mysql
        sql = "INSERT text_data " \
                +" (`text_id`, `type_id`, `text_system_name`, `text_invisible_title`, `text_start_date`, `text_end_date`, `text_start_time`, `text_end_time`, `text_display_time`, `user_id`) " \
                +" VALUE " \
                +" ( \"" + text_id + "\", " \
                + str(type_id) + ", " \
                + "\"" + text_system_name + "\", " \
                + "\"" + invisible_title + "\", " \
                + "\"" + text_start_date + "\", " \
                + "\"" + text_end_date + "\", " \
                + "\"" + text_start_time + "\", " \
                + "\"" + text_end_time + "\", " \
                + str(text_display_time) + ", " \
                + str(user_id) + " ) " 

        db.cmd(sql)
        
        db.close()

        return_msg["text_id"] = text_id
        return_msg["text_system_dir"] = system_file_dir
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg    

#
def edit_text_data(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        server_dir = ""
        text_id = ""
        invisible_title = ""
        type_id = 0
        text_start_date = ""
        text_end_date = ""
        text_start_time = ""
        text_end_time = ""
        text_display_time = 5
        user_id = ""
        try:
            server_dir = json_obj["server_dir"]
            text_id = json_obj["text_id"]
            invisible_title = json_obj["invisible_title"]
            type_id = json_obj["file_type"]
            text_start_date = json_obj["start_date"]
            text_end_date = json_obj["end_date"]
            text_start_time = json_obj["start_time"]
            text_end_time = json_obj["end_time"]
            text_display_time = json_obj["display_time"]
            user_id = json_obj["user_id"]
            text_file = json_obj["text_file"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        user_level_low_bound = 100
        user_level_high_bound = 10000
        text_type_id = 0
        
        #connect to mysql
        db = mysql()
        db.connect()
        
        #check user level
        sql = ("SELECT user_level FROM user WHERE user_id=" + str(user_id))
        pure_result = db.query(sql)
        try: 
            user_level = int(pure_result[0][0])
            if user_level < user_level_low_bound:
                db.close()
                return_msg["error"] = "user right is too low"
                return return_msg
            #check self text
            sql = ("SELECT user_id, type_id FROM text_data WHERE text_id='" + text_id + "'")
            pure_result = db.query(sql)
            try:
                if pure_result[0][0] != user_id and user_level < user_level_high_bound:
                    db.close()
                    return_msg["error"] = "can not modify other user text"
                    return return_msg
                text_type_id = int(pure_result[0][1])
            except:
                db.close()
                return_msg["error"] = "no such text id : " + text_id
                return return_msg
        except:
            db.close()
            return_msg["error"] = "no such user id : " + str(user_id)
            return return_msg
        
        
        
        old_dir = ""
        new_dir = ""
        #get text_system_name
        sql = ("SELECT text_system_name FROM text_data WHERE text_id='" + text_id + "'")
        pure_result = db.query(sql)
        try: 
            old_dir = pure_result[0][0]
            new_dir = pure_result[0][0]
        except:
            db.close()
            return_msg["error"] = "no such text id : " + text_id
            return return_msg
        
        #get old text type dir
        sql = ("SELECT type_dir FROM data_type WHERE type_id=" + str(text_type_id))
        pure_result = db.query(sql)
        try: 
            old_dir = pure_result[0][0] + old_dir
        except:
            db.close()
            return_msg["error"] = "no such text type : " + str(text_type_id)
            return return_msg

        #check if we need to move the file
        if text_type_id == type_id:
            old_dir = os.path.join(server_dir,"static/"+old_dir)
            new_dir = old_dir
        else :  
            #get new text type dir      
            sql = ("SELECT type_dir FROM data_type WHERE type_id=" + str(type_id))
            pure_result = db.query(sql)
            try: 
                new_dir = pure_result[0][0] + new_dir
            except:
                db.close()
                return_msg["error"] = "no such text type : " + str(type_id)
                return return_msg

            #check if we need to move the file
            if old_dir == new_dir:
                new_dir = 'static/'+new_dir
            else :
                try:
                    old_dir = os.path.join(server_dir,"static/"+old_dir)
                    new_dir = os.path.join(server_dir,"static/"+new_dir)
                    copyfile(old_dir, new_dir)
                    if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                        os.remove(old_dir)
                except:
                    try:
                        if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                            os.remove(new_dir)
                    except:
                        "DO NOTHING"
                    db.close()
                    return_msg["error"] = "move file error : " + old_dir
                    return return_msg
            with open(new_dir,'w') as fp:
                print(json.dumps(text_file),file=fp)
        
        #start to modify mysql
        sql = ("UPDATE text_data " \
                +" SET type_id=" + str(type_id) + ", " \
                +" text_invisible_title='" + invisible_title + "', "\
                +" text_start_date=\"" + text_start_date + "\", " \
                +" text_end_date=\"" + text_end_date + "\", " \
                +" text_start_time=\"" + text_start_time + "\", " \
                +" text_end_time=\"" + text_end_time + "\", " \
                +" text_display_time=" + str(text_display_time) + ", " \
                +" text_last_edit_user_id=\"" + str(user_id) + "\" " \
                +" WHERE text_id=\"" + text_id + "\"")
        try:
            db.cmd(sql)
        except DB_Exception as e:
            try:
                copyfile(new_dir, old_dir)
                if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                    os.remove(new_dir)
            except:
                try:
                    if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                        os.remove(old_dir)
                except:
                    db.close()
                    return_msg["error"] = "move file error : duplicate files : " + old_dir
                    return return_msg
                db.close()
                return_msg["error"] = "move file error : " + new_dir
                return return_msg
            db.close()
            return_msg["error"] = "update mysql error"
            return return_msg

        db.close()
        return_msg["result"] = "success"
        return_msg["text_system_dir"] = new_dir
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg  


#
def delete_image_or_text_data(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        server_dir = ""
        target_id = ""
        user_id = ""
        target_dir = ""
        trash_dir = ""
        target_type_id = 0
        user_level_low_bound = 100
        user_level_high_bound = 10000
        try:
            server_dir = json_obj["server_dir"]
            target_id = json_obj["target_id"]
            user_id = json_obj["user_id"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        #connect to mysql
        db = mysql()
        db.connect()
        
        #check user level
        sql = ("SELECT user_level FROM user WHERE user_id=" + str(user_id))
        pure_result = db.query(sql)
        try: 
            user_level = int(pure_result[0][0])
            if user_level < user_level_low_bound:
                db.close()
                return_msg["error"] = "user right is too low"
                return return_msg
            #check self data and get type_id
            if target_id[0:4] == "imge":
                sql = "SELECT type_id, img_system_name, user_id FROM image_data WHERE img_id='" + target_id + "'"
            elif target_id[0:4] == "text":
                sql = "SELECT type_id, text_system_name, user_id FROM text_data WHERE text_id='" + target_id + "'"
            else :
                db.close()
                return_msg["error"] = "target id type error"
                return return_msg
            pure_result = db.query(sql)
            try:
                if pure_result[0][2] != user_id and user_level < user_level_high_bound:
                    db.close()
                    return_msg["error"] = "can not modify other user image or text"
                    return return_msg
                target_type_id =  int(pure_result[0][0])
                target_dir = pure_result[0][1]
            except:
                db.close()
                return_msg["error"] = "no such target id : " + str(target_id)
                return return_msg
        except:
            db.close()
            return_msg["error"] = "no such user id : " + str(user_id)
            return return_msg
        
        #get file place
        sql = "SELECT type_dir FROM data_type WHERE type_id=" + str(target_type_id)
        pure_result = db.query(sql)
        try:
            trash_dir = os.path.join(server_dir, "static/trash_data/"+target_dir)
            system_file_dir = os.path.join(server_dir, "static/"+str(pure_result[0][0]))
            target_dir = os.path.join(system_file_dir, target_dir)
        except:
            db.close()
            return_msg["error"] = "no such type id : " + str(type_id)
            return return_msg

        #check trash_data 
        if not os.path.exists(os.path.split(trash_dir)[0]):
            try:
                os.makedirs(os.path.split(trash_dir)[0])
            except:
                db.close()
                return_msg["error"] = "no trash_data folder"
                return return_msg

        #move to trash
        if os.path.isfile(target_dir):
            try:
                shutil.move(target_dir, trash_dir)
            except:
                db.close()
                return_msg["error"] = "move fail"
                return return_msg

        if target_id[0:4] == "imge":
            sql = "UPDATE image_data SET img_is_delete=1, img_last_edit_user_id="+str(user_id)+" WHERE img_id='"+ target_id + "'"
        elif target_id[0:4] == "text":
            sql = "UPDATE text_data SET text_is_delete=1, text_last_edit_user_id="+str(user_id)+" WHERE text_id='"+target_id+"'"
        else :
            sql = ""
        db.cmd(sql)

        
        db.close()

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg  
    

def add_new_data_type(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        type_name = json_obj['type_name']
        db = mysql()
        db.connect()

        sql = "SELECT count(*) FROM data_type WHERE type_name = \""+type_name+"\""
        if db.query(sql)[0][0] >= 1:
            return_msg["error"] = "Type name has existed"
            return return_msg

        sql = "INSERT INTO data_type (type_name,type_dir) VALUES (\"" \
            +type_name+"\",\"" \
            +type_name+"/\")"
        db.cmd(sql)

        db.close()

        if not os.path.exists("static/"+type_name):
            os.makedirs("static/"+type_name)

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg  


#
def change_password(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        user_id = 0
        old_password = ""
        new_password = ""
        try:
            user_name = json_obj["user_name"]
            old_password = json_obj["old_password"]
            new_password = json_obj["new_password"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        #connect to mysql
        db = mysql()
        db.connect()
        
        #get user_id 
        sql = "SELECT user_id FROM user WHERE user_name = \""+user_name.decode("utf-8")+"\""
        pure_result = db.query(sql)
        try:
            user_id = pure_result[0][0]
        except:
            db.close()
            return_msg["error"] = "no such user name"
            return return_msg
            

        #check user
        sql = "SELECT user_password FROM user WHERE user_id=" + str(user_id)
        pure_result = db.query(sql)
        hashed_key = ""
        try:
            hashed_key = pure_result[0][0].encode('utf-8')
            if bcrypt.checkpw(old_password.encode('utf-8'),hashed_key):
                # old password correct
                hashed_key = bcrypt.hashpw(new_password.encode('utf-8'),bcrypt.gensalt())
                sql = "UPDATE user SET user_password=" + str(hashed_key)[1:] + " WHERE user_id=" + str(user_id)
                db.cmd(sql)
            else:
                db.close()
                return_msg["error"] = "old password incorrect"
                return return_msg
        except:
            db.close()
            return_msg["error"] = "no such user id : " + str(user_id)
            return return_msg
        
        db.close()

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg


def read_text_data(text_id):
    try:
        return_msg = {}
        db = mysql()
        db.connect()
                
        sql = 'SELECT text_system_name,type_id FROM text_data WHERE text_id = "%s"' % text_id
        pure_result = db.query(sql)
        text_file_name = pure_result[0][0]
        type_id = pure_result[0][1]

        sql = 'SELECT type_dir FROM data_type WHERE type_id = %d' % type_id
        pure_result = db.query(sql)
        type_dir = pure_result[0][0]
        
        filename = 'static/' + type_dir + text_file_name
        with open(filename,'r') as fp:
            text_content = json.load(fp)

        for key in text_content:
            text_content[key] = text_content[key].replace('<br/>','\n').replace('&nbsp',' ').replace('<br>','\n')

        return text_content
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

# for google api
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly','https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'
redirect_url = 'http://localhost:3000/googleapi'

def get_credentials(handler=None):
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
        'google-api-quickstart.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(filename=CLIENT_SECRET_FILE,scope=SCOPES,redirect_uri=redirect_url)
        url = flow.step1_get_authorize_url()
        if handler:
            handler.redirect(url)
        else:
            return None
    return credentials

def exchange_code_and_store_credentials(code):
    flow = client.flow_from_clientsecrets(filename=CLIENT_SECRET_FILE,scope=SCOPES,redirect_uri=redirect_url)
    credentials = flow.step2_exchange(code)

    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
        'google-api-quickstart.json')
    store = Storage(credential_path)
    store.put(credentials)
    credentials.set_store(store)
    return credentials

def get_upcoming_events(credentials):
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    eventsResult = service.events().list(calendarId='nctupac@gmail.com',maxResults=10,timeMin=now).execute()
    return eventsResult
