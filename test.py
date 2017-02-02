from broadcast_api import load_schedule
from broadcast_api import edit_schedule
from broadcast_api import arrange_schedule
from server_api import upload_image_insert_db
from server_api import edit_image_data
from mysql_class import mysql
from pprint import pprint
import os.path
import json

json_obj = {}
'''
json_obj["server_dir"] = '/home/tim/Desktop/electronic-blackboard/'
json_obj["file_type"] = 4
json_obj["file_dir"] = '/home/tim/Desktop/electronic-blackboard/static/img/3.jpg'
json_obj["start_date"] = '2017-1-17'
json_obj["end_date"] = '2027-1-20'
json_obj["start_time"] = '00:00:01'
json_obj["end_time"] = '23:59:58'
json_obj["display_time"] = 3
json_obj["user_id"] = 1

a = upload_image_insert_db(json_obj)
pprint(a)
'''

json_obj["server_dir"] = '/home/tim/Desktop/electronic-blackboard/'
json_obj["img_id"] = 'imge0000000006'
json_obj["file_type"] = 1
json_obj["start_date"] = '2017-1-17'
json_obj["end_date"] = '2027-1-20'
json_obj["start_time"] = '00:00:01'
json_obj["end_time"] = '23:59:58'
json_obj["display_time"] = 1
json_obj["user_id"] = 1

a = edit_image_data(json_obj)
pprint(a)

