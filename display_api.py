from mysql import mysql
from datetime import date
from datetime import datetime
from datetime import timedelta
from dataAccessObjects import *
import os.path

def get_user_id(user_name):
    """
    Get user id from database by user name
    """
    return_msg = {}
    result = ""

    with UserDao() as userDao:
        user_id = userDao.getUserId(user_name) 
    if user_id:
        return user_id
    else:
        return_msg['error'] = 'No such user'
        return return_msg

#connect mysql and list all upload images' information
def display_image(argu_user):
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
                            img_file_name=result_row[2],
                            img_start_time=result_row[3],
                            img_end_time=result_row[4],
                            img_start_date=result_row[5],
                            img_end_date=result_row[6],
                            type_id=result_row[7],
                            img_thumbnail_name=result_row[8],
                            img_display_time=result_row[9],
                            img_display_count=result_row[10]))
    return return_msg_list


#connect mysql and list all upload texts' information
def display_text(argu_user):
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

def display_data_type(type_id=None, type_name=None, type_dir=None, type_weight=None):
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

def display_data_types():
    with DataTypeDao() as dataTypeDao:
        data_types = dataTypeDao.getTypeData()
    return data_types

def transform_date_string(data_list):
    for data in data_list:
        if isinstance(data, dict):
            for key,value in data.items():
                if isinstance(value, date):
                    data[key] = value.isoformat()
                if isinstance(value, timedelta):
                    data[key] = str(value)
        elif isinstance(data, list):
            for idx,value in enumerate(data):
                if isinstance(value, date):
                    data[idx] = value.isoformat()
                if isinstance(value, timedelta):
                    data[idx] = str(value)

def convert_img_file_path(handler,data_list,data_types):
    for data in data_list:
        if isinstance(data ,dict):
            for type in data_types:
                if type[0] == data['type_id']:
                    target_type = type
                    break
            data.update(dict(img_url=handler.static_url(target_type[2]+data['img_file_name'])))
