from mysql import mysql
from mysql import DB_Exception
from datetime import date
from datetime import datetime
from datetime import timedelta
from dataAccessObjects import *
import os.path
#
def get_user_id(user_name):
    try:
        return_msg = {}
        result = ""

        with UserDao() as userDao:
            user_id = userDao.getUserId(user_name) 
        if user_id:
            return user_id
        else:
            return_msg['error'] = 'No such user'
            return return_msg

    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

#connect mysql and list all upload images' information
def display_image(argu_user):
    try:
        user_name = argu_user
        current_user_level = 0
        return_msg = {}
        return_msg_list = []
        
        #connect to mysql
        db = mysql()
        db.connect()

        user_id = get_user_id(user_name)

        #check whether level is 10000
        with UserDao() as userDao:
            current_user_level = userDao.getUserLevel(user_id)
        if not current_user_level:
            return_msg['error'] = 'No user "{user_name}"'.format(user_name=user_name)
            return return_msg

        #display image data from the same user
        if current_user_level == 10000:
            sql = "SELECT img_id, img_upload_time, img_file_name, img_start_time, img_end_time, img_start_date, img_end_date, type_id, img_thumbnail_name, img_display_time, img_display_count " \
                    + "FROM image_data WHERE img_is_delete=0"
        else:
            sql = "SELECT img_id, img_upload_time, img_file_name, img_start_time, img_end_time, img_start_date, img_end_date, type_id, img_thumbnail_name, img_display_time, img_display_count " \
                    + "FROM image_data WHERE user_id  = %d AND img_is_delete=0" % (user_id)


        pure_result = db.query(sql)
        #restruct results of query
        for result_row in pure_result:
            return_msg_list.append([result_row[0],result_row[1],result_row[2],result_row[3],result_row[4],result_row[5],result_row[6],result_row[7],result_row[8],result_row[9],result_row[10]])
            #                   img_id, img_upload_time, img_file_name, img_start_time, img_end_time, img_start_date, img_end_date, type_id, img_thumbnail_name, img_display_time, img_display_count
        
        db.close()

        return return_msg_list
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg


#connect mysql and list all upload texts' information
def display_text(argu_user):
    try:
        user_name = argu_user
        current_user_level = 0
        return_msg = {}
        return_msg_list = []

        #connect to mysql
        db = mysql()
        db.connect()

        user_id = get_user_id(user_name)

        #check whether level is 10000
        with UserDao() as userDao:
            current_user_level = userDao.getUserLevel(user_id)
        if not current_user_level:
            return_msg['error'] = 'No user "{user_name}"'.format(user_name=user_name)
            return return_msg

        #display text data from the same user
        if current_user_level == 10000:
            sql = "SELECT text_id, type_id, text_upload_time, text_start_date, text_end_date, text_start_time, text_end_time, text_display_time, text_display_count " \
                    + "FROM text_data WHERE text_is_delete=0"
        else:
            sql = "SELECT text_id, type_id, text_upload_time, text_start_date, text_end_date, text_start_time, text_end_time, text_display_time, text_display_count " \
                    + "FROM text_data WHERE user_id = %d AND text_is_delete=0" % (user_id)

        pure_result = db.query(sql)
        #restruct results of query
        for result_row in pure_result:
            return_msg_list.append([result_row[0],result_row[1],result_row[2],result_row[3],result_row[4],result_row[5],result_row[6],result_row[7],result_row[8]])
            #text_id, type_id, text_upload_time, text_start_date, text_end_date, text_start_time, text_end_time, text_display_time, text_display_count
        
        db.close()
        return return_msg_list
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg



def display_data_type(type_id=None, type_name=None, type_dir=None, type_weight=None):
    try:
        current_type_id = type_id
        current_type_name = type_name
        current_type_dir = type_dir
        current_type_weight = type_weight

        return_msg = {}
        return_msg_list = []

        deal_result = []

        #connect to mysql
        db = mysql()
        db.connect()

        if current_type_id :
            sql = "SELECT * FROM data_type WHERE type_id = \""+str(current_type_id)+"\""
        elif current_type_name :
            sql = "SELECT * FROM data_type WHERE type_name = \""+current_type_name+"\""
        elif current_type_dir :
            sql = "SELECT * FROM data_type WHERE type_dir = \""+current_type_dir+"\""
        elif current_type_weight :
            sql = "SELECT * FROM data_type WHERE type_weight = \""+str(current_type_weight)+"\""
        else:
            return_msg["error"] = "Error type select"
            return return_msg

        pure_result = db.query(sql)
        if current_type_weight:
            for result_row in pure_result:
                return_msg_list.append([result_row[0],result_row[1],result_row[2],result_row[3]])
        else:
            for result_row in pure_result:
                return_msg_list.extend([result_row[0],result_row[1],result_row[2],result_row[3]])
                #                       id           ,name         ,dir          ,weight

        db.close()
        return return_msg_list
    except DB_Exception as e:
        db.close()
        return_msg["error"] = e.args[1]
        return return_msg

def display_data_types():
    try:
        with DataTypeDao() as dataTypeDao:
            data_types = dataTypeDao.getTypeData()
        return data_types
    except DB_Exception as e:
        return_msg={}
        return_msg["error"] = e.args[1]
        return return_msg
