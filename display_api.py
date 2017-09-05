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
        
        user_id = get_user_id(user_name)

        #check whether level is 10000
        with UserDao() as userDao:
            current_user_level = userDao.getUserLevel(user_id)
        if not current_user_level:
            return_msg['error'] = 'No user "{user_name}"'.format(user_name=user_name)
            return return_msg

        #display image data from the same user
        if current_user_level >= 10000:
            with ImageDao() as imageDao:
                imgs = imageDao.getDisplayImgs()
        else:
            with ImageDao() as imageDao:
                imgs = imageDao.getDisplayImgs(userId=user_id)

        #restruct results of query
        for result_row in imgs:
            return_msg_list.append(dict(
                                img_id=result_row[0],
                                img_upload_time=result_row[1],
                                img_start_time=result_row[2],
                                img_end_time=result_row[3],
                                img_start_date=result_row[4],
                                img_end_date=result_row[5],
                                type_id=result_row[6],
                                img_thumbnail_name=result_row[7],
                                img_display_time=result_row[8],
                                img_display_count=result_row[9]))
        return return_msg_list
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg


#connect mysql and list all upload texts' information
def display_text(argu_user):
    try:
        user_name = argu_user
        current_user_level = 0
        return_msg = {}
        return_msg_list = []

        user_id = get_user_id(user_name)

        #check whether level is 10000
        with UserDao() as userDao:
            current_user_level = userDao.getUserLevel(user_id)
        if not current_user_level:
            return_msg['error'] = 'No user "{user_name}"'.format(user_name=user_name)
            return return_msg

        #display text data from the same user
        if current_user_level >= 10000:
            with TextDao() as textDao:
                texts = textDao.getDisplayTexts()
        else:
            with TextDao() as textDao:
                texts = textDao.getDisplayTexts(userId=user_id)

        #restruct results of query
        for result_row in texts:
            return_msg_list.append([result_row[0],result_row[1],result_row[2],result_row[3],result_row[4],result_row[5],result_row[6],result_row[7],result_row[8]])
            #text_id, type_id, text_upload_time, text_start_date, text_end_date, text_start_time, text_end_time, text_display_time, text_display_count
        
        return return_msg_list
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def display_data_type(type_id=None, type_name=None, type_dir=None, type_weight=None):
    try:
        info = {}
        info["current_type_id"] = type_id
        info["current_type_name"] = type_name
        info["current_type_dir"] = type_dir
        info["current_type_weight"] = type_weight

        return_msg = {}
        return_msg_list = []

        with DataTypeDao() as dataTypeDao:
            data_type = dataTypeDao.getDisplayDataType(info=info)
        if data_type == None:
            return_msg["error"] = "Error type select"
            return return_msg

        if info["current_type_weight"]:
            for result_row in data_type:
                return_msg_list.append([result_row[0],result_row[1],result_row[2],result_row[3]])
        else:
            for result_row in data_type:
                return_msg_list.extend([result_row[0],result_row[1],result_row[2],result_row[3]])
                #                       id           ,name         ,dir          ,weight

        return return_msg_list
    except DB_Exception as e:
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
