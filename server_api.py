from mysql import mysql
from mysql import DB_Exception
from shutil import copyfile
from display_api import get_user_id
from display_api import display_data_type
from PIL import Image
import os
import os.path
import shutil
import bcrypt
import json
import tornado
import time
import random
from tornado.escape import xhtml_escape
from tornado.web import MissingArgumentError
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import httplib2
from apiclient import discovery
import datetime
from dataAccessObjects import *

class ArgumentUtil():
    def __init__(self,requestHandler):
        self.handler = requestHandler

    def getArgument(self,name):
        rawArg = self.handler.get_argument(name)
        return xhtml_escape(rawArg)

    def getArguments(self):
        raise NotImplementedError("The getArgument() is not implemented.")

class UserArgumentsUtil(ArgumentUtil):
    def __init__(self,requestHandler):
        super().__init__(requestHandler)

    def getArguments(self):
        userInfo = {}
        userInfo['user_name'] = self.getArgument('username')
        userInfo['user_password'] = self.getArgument('password')
        return userInfo

class UserEditArgumentsUtil(ArgumentUtil):
    def getCurUser(self):
        return self.handler.get_current_user()

    def getArguments(self):
        userInfo = {}
        userInfo['user_name'] = self.getCurUser()
        userInfo['old_password'] = self.getArgument('old_password')
        userInfo['new_password'] = self.getArgument('password')
        return userInfo

class UploadArgumentsUtil(ArgumentUtil):
    def getArguments(self):
        uploadData = {}
        uploadData['file_type'] = self.getArgument('data_type')
        uploadData['start_date'] = self.getArgument('start_date')
        uploadData['end_date'] = self.getArgument('end_date')
        uploadData['start_time'] = self.getArgument('start_time')
        uploadData['end_time'] = self.getArgument('end_time')
        uploadData['display_time'] = self.getArgument('display_time')
        return uploadData
#
def add_like_count(target_id):
    try:
        if target_id[0:4]=="imge":
            with ImageDao() as imageDao:
                imageDao.addLikeCount(targetId=target_id)
        elif target_id[0:4]=="text":
            with TextDao() as textDao:
                textDao.addLikeCount(targetId=target_id)
        else :
            return 0
        
        return 1
    except:
        return 0
        
#find the current displaying schedule
def find_now_schedule():
    try:
        with ScheduleDao() as scheduleDao:
            next_schedule = scheduleDao.getNextSchedule()
        # return sche_target_id
        if next_schedule != None:
            return str(next_schedule['sche_target_id'])
        else:
            return 0
    except:
        return -1
#
def add_now_like_count():
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        #find image or text id from current schedule
        target_id = find_now_schedule()
        if target_id==0:
            return_msg["error"] = "can not find current schedule"
            return return_msg
            
        #add like count
        if add_like_count(target_id)==0:
            return_msg["error"] = "can not add like count"
            return return_msg

        return_msg["result"] = "success"
        return return_msg
                
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg 
    except Exception as e:
        return_msg["error"] = e
        return return_msg
def register_preference(data):
    try:
        inside_type = str(display_data_type(type_name='inside')[0])
        techOrange_type = str(display_data_type(type_name='techOrange')[0])
        medium_type = str(display_data_type(type_name='medium')[0])
        pttBeauty_type = str(display_data_type(type_name='pttBeauty')[0])
        pttjoke_type = str(display_data_type(type_name='pttjoke')[0])
        pttStupidClown_type = str(display_data_type(type_name='pttStupidClown')[0])

        pref_str = ""
        if "all" in data["user_preference"]:
            pref_str = inside_type+" "+medium_type+" "+pttBeauty_type+" "+pttStupidClown_type+" "+pttjoke_type+" "+techOrange_type
        else:
            if "inside" in data["user_preference"]:
                pref_str = pref_str + inside_type + " "
            if "techOrange" in data["user_preference"]:
                pref_str = pref_str + techOrange_type + " "
            if "medium" in data["user_preference"]:
                pref_str = pref_str + medium_type + " "
            if "pttBeauty" in data["user_preference"]:
                pref_str = pref_str + pttBeauty_type + " "
            if "pttjoke" in data["user_preference"]:
                pref_str = pref_str + pttjoke_type + " "
            if "pttStupidClown" in data["user_preference"]:
                pref_str = pref_str + pttStupidClown_type + " "
            if len(pref_str)>0:
                pref_str = pref_str[:-1]

        #generate new id
        try:
            with UserPreferDao() as userPreferDao:
                pref_id = userPreferDao.generateNewId()
        except:
            pref_id = "pref0000000001"

        with UserDao() as userDao:
            user_id = userDao.getUserId(bluetoothId=data['bluetooth_id'])

        #insert user preference
        with UserPreferDao() as userPreferDao:
            userPreferDao.insertUserPrefer(prefId=pref_id,userId=user_id,prefStr=pref_str)

        return 1
    except:
        return 0
#
def check_bluetooth_id_exist(bluetooth_id):
    try:
        with UserDao() as userDao:
            isUsed = userDao.checkBluetoothIdUsed(bluetooth_id)
        return isUsed
    except:
        return -1
#
def check_bluetooth_mode_available():
    file_dir = "setting"
    file_name = "server_setting.txt"
    #check setting file exist
    if not os.path.exists(file_dir):
        return -1
    if not os.path.isfile(file_dir+'/'+file_name):
        return -1
    
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
    except Exception as e:
        print(str(e))
        return -1
#
def load_now_user_prefer(user_id):
    try:
        now_hour = time.localtime(time.time())[3]
        #use now time to choose preference rule
        data_type = ""
        if now_hour >= 7 and now_hour < 11:
            data_type = "01"
        elif now_hour >= 11 and now_hour < 13:
            data_type = "02"
        elif now_hour >= 13 and now_hour < 18:
            data_type = "03"
        elif now_hour >= 18 and now_hour < 22:
            data_type = "04"
        else :
            data_type = "05"
        
        with UserPreferDao() as userPreferDao:
            pure_result = userPreferDao.getNowUserPrefer(dataType=data_type,UserId=user_id)
        
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
def set_insert_customer_text_msg():
    try:
        send_msg = {}
        now_time = time.time()
        send_msg["result"] = "fail"
        send_msg["server_dir"] = ""
        send_msg["file_type"] = display_data_type(type_name='customized_text')[0]
        send_msg["start_date"] = time.strftime("%Y-%m-%d", time.localtime(now_time))
        send_msg["end_date"] = time.strftime("%Y-%m-%d", time.localtime(now_time+9))
        send_msg["start_time"] = time.strftime("%H:%M:%S", time.localtime(now_time))
        send_msg["end_time"] = time.strftime("%H:%M:%S", time.localtime(now_time+9))
        send_msg["display_time"] = 10
        send_msg["user_id"] = 1
        send_msg["result"] = "success"
        return send_msg
    except Exception as e:
        send_msg["error"] = e
        return send_msg
#
def Zodiac(month, day):
    n = (u'摩羯座',u'水瓶座',u'雙鱼座',u'白羊座',u'金牛座',u'雙子座',u'巨蟹座',u'獅子座',u'處女座',u'天秤座',u'天蝎座',u'射手座')
    d = ((1,20),(2,19),(3,21),(4,21),(5,21),(6,22),(7,23),(8,23),(9,23),(10,23),(11,23),(12,23))
    return n[len(list(filter(lambda y:y<=(month,day), d)))%12]
#
def random_constellation(user_id):
    with UserDao() as userDao:
        date = userDao.getUserBirthday(user_id)
    if date == None:
        constellation = ['摩羯座','水瓶座','雙鱼座','白羊座','金牛座','雙子座','巨蟹座','獅子座','處女座','天秤座','天蝎座','射手座']
        constellation = random.choice(constellation)
    else:
        constellation = Zodiac(date.month,date.day)

    return_msg = {}
    try:
        today=str(datetime.date.today())
        with FortuneDao() as fortuneDao:
            result = fortuneDao.getFortune(today=today,constellation=constellation)
        if result != None:
            overall_str="整體運勢" + result[0][0]
            love_str="愛情運勢" + result[0][1]
            career_str="事業運勢" + result[0][2]
            wealth_str="財運運勢" + result[0][3]
            return_msg["name"] = constellation
            return_msg["value"] = [overall_str,love_str,career_str,wealth_str]
            return return_msg
        else:
            return_msg["error"] = "Can't get fortune data."
    except:
        return_msg["error"] = "Can't get fortune data."
        return return_msg
#
def get_prefer_news(prefer_data_type):
    try:
        return_msg = []
        if len(prefer_data_type)<1:
            return return_msg

        #array to string
        prefer_str = "("
        for num1 in range(len(prefer_data_type)):
            prefer_str = prefer_str + str(prefer_data_type[num1]) + ","
        prefer_str = prefer_str[:-1]
        prefer_str = prefer_str + ")"
        #find two
        with NewsQRCodeDao() as newsQRCodeDao:
            pure_result = newsQRCodeDao.getNews(preferStr=prefer_str)
        #reshape output data
        for num2 in range(len(pure_result)):
            with DataTypeDao() as dataTypeDao:
                type_dir = dataTypeDao.getTypeDir(typeId=pure_result[num2][2])
            tmp_json = {}
            tmp_json["title"] = str(pure_result[num2][0])
            tmp_json["QR"] = '/static/{type_dir}{name}.png'.format(type_dir=type_dir,name=str(pure_result[num2][1]))
            return_msg.append(tmp_json)

        return return_msg
    except:
        return return_msg

#
def collect_user_prefer_data(user_id, prefer_data_type):
    try:
        return_msg = {}
        return_msg["preference"] = 1
        #date
        return_msg["date"] = time.strftime("%a. %Y.%m.%d", time.localtime(time.time()))
        #nickname
        with UserDao() as userDao:
            return_msg["nickname"] = userDao.getUserNickname(user_id)
        #constellation
        return_msg["constellation"] = random_constellation(user_id)
        #news
        return_msg["news"] = get_prefer_news(prefer_data_type)
        return return_msg
    except:
        return return_msg
#
def insert_customized_schedule(user_id, prefer_data_type):
    from arrange_schedule import edit_schedule

    try:
        receive_msg = {}

        #insert customer text to db
        send_msg = set_insert_customer_text_msg()
        receive_msg = upload_text_insert_db(send_msg)
        if receive_msg["result"]=="fail":
            return -1

        #collect user prefer data
        text_content = collect_user_prefer_data(user_id, prefer_data_type)

        #write to text
        with open(receive_msg["text_system_dir"],"w") as fp:
            print(json.dumps(text_content),file=fp)

        target_id = receive_msg["text_id"]
        display_time = 10

        #insert infromation to schedule
        send_msg["sn_offset"] = 1
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
        user_id=0

        #check bluetooth mode available
        if check_bluetooth_mode_available()==0:
            return_msg["error"] = "the bluetooth function is closed"
            return return_msg

        with UserDao() as userDao:
            user_id = userDao.getUserId(bluetoothId=bluetooth_id)
        if user_id == None:
            return_msg["error"] = "no such bluetooth id"
            return return_msg

        #load now user prefer
        prefer_data_type = load_now_user_prefer(user_id)
        if prefer_data_type == -1:
            return_msg["error"] = "no prefer data type"
            return return_msg

        #insert customized schedule to next schedule
        receive_result = insert_customized_schedule(user_id, prefer_data_type)
        if receive_result == -1:
            return_msg["error"] = "insert fail"
            return return_msg
    
        return_msg["result"] = "success"
        return return_msg
        
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg 
    except Exception as e:
        return_msg["error"] = e
        return return_msg

#
def check_user_existed_or_signup(user_info):
    try:
        return_msg = {}

        with UserDao() as userDao:
            is_existed = userDao.checkUserExisted(userName=user_info['user_name'])

        if is_existed:
            return_msg['flash'] = 'The name "{name}" has been used'.format(name=user_info['user_name'])
            return return_msg

        hashed_passwd = bcrypt.hashpw(user_info['user_password'].encode('utf-8'),bcrypt.gensalt())
        with UserDao() as userdao:
            userdao.createNewUser(userName=user_info['user_name'],userPassword=hashed_passwd)

        return_msg['flash'] = 'User "{name}" create success!'.format(name=user_info['user_name'])
        return return_msg
    except:
        return_msg["error"] = "Fail to check whether user is existed or create new user"
        return return_msg
#
def register_no_right_user(data):
    try:
        send_msg = {}
        send_msg["user_name"] = data["bluetooth_id"]
        send_msg["user_password"] = data["bluetooth_id"][0:6]
        check_user_existed_or_signup(send_msg)

        with UserDao() as userDao:
            existed = userDao.checkUserExisted(userName=data["bluetooth_id"])
        if not existed:
            return 0

        with UserDao() as userDao:
            userDao.updateUserData(userInfo=data)
        return 1
    except:
        return 0
#
def add_account_and_prefer(data):
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        #check bluetooth id exist or not
        if check_bluetooth_id_exist(data["bluetooth_id"])!=0:
            return_msg["error"] = "bluetooth id exist"
            return return_msg

        #register new user level 50 == lower than normal user
        if register_no_right_user(data)==0:
            return_msg["error"] = "register user fail"
            return return_msg

        #register preference
        if register_preference(data)==0:
            return_msg["error"] = "register preference fail"
            return return_msg

        return_msg["result"] = "success"
        return return_msg

    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg
    except Exception as e:
        return_msg["error"] = str(e)
        return return_msg
#
def check_user_password(user_info):
    try:
        return_msg = {}

        with UserDao() as userDao:
            password = userDao.getUserPassword(userName=user_info['user_name'])

        if password == None:
            return_msg['fail'] = 'No such user'
            return return_msg

        hashed_passwd = password.encode('utf-8')
        if bcrypt.checkpw(user_info['user_password'].encode('utf-8'),hashed_passwd):
            return_msg['success'] = 'Hello {user_name}'.format(user_name=user_info['user_name'])
        else:
            return_msg['fail'] = 'Wrong password'

        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def get_upload_meta_data(handler):
    uploadArgUtil = UploadArgumentsUtil(handler)
    user_name = handler.get_current_user().decode('utf-8')

    meta_data = uploadArgUtil.getArguments()
    meta_data["server_dir"] = os.path.dirname(__file__)
    meta_data["user_id"] = get_user_id(user_name)

    return meta_data

#get the text data from the handler
def get_upload_text_data(handler):
    try:
        text_data = {}
        text_data['result'] = 'fail'

        text_data['con'] = tornado.escape.xhtml_escape(handler.get_argument('con')).replace('&amp;nbsp','&nbsp').replace('&lt;br&gt;','<br>')
        text_data['title1'] = tornado.escape.xhtml_escape(handler.get_argument('title1')).replace('&amp;nbsp','&nbsp').replace('&lt;br&gt;','<br>')
        text_data['title2'] = tornado.escape.xhtml_escape(handler.get_argument('title2')).replace('&amp;nbsp','&nbsp').replace('&lt;br&gt;','<br>')
        text_data['description'] = tornado.escape.xhtml_escape(handler.get_argument('description')).replace('&lt;br&gt;','<br>').replace('&amp;nbsp','&nbsp')
        text_data['year'] = tornado.escape.xhtml_escape(handler.get_argument('year'))
        text_data['month'] = tornado.escape.xhtml_escape(handler.get_argument('month'))
        text_data['background_color'] = tornado.escape.xhtml_escape(handler.get_argument('background_color'))

        text_data['result'] = 'success'
        return text_data
    except Exception as e:
        print(str(e))
        return text_data


def store_image(filepath,file_content):
    with open(filepath,'wb') as fp:
        fp.write(file_content)
    
def store_thumbnail_image(file_path,thumbnail_path):
    img = Image.open(file_path)
    img.thumbnail((100,100))
    img.save(thumbnail_path)

def get_img_meta(img_id):
    try:
        with ImageDao() as imageDao:
            img_data = imageDao.getImgData(imgId=img_id)
        #TODO Caller should check return value is not None
        return img_data
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def get_text_meta(text_id):
    try:
        with TextDao() as textDao:
            ret = textDao.getTextMeta(textId=text_id)
        return ret
    except:
        return_msg["error"] = "Can't get text meta."
        return return_msg

def check_user_level(user_id):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        user_level_low_bound = 100

        #check user level
        with UserDao() as userDao:
            user_level = userDao.getUserLevel(user_id)
        if not user_level:
            return_msg['error'] = 'No user_id "{user_id}"'.format(user_id=user_id)
            return return_msg

        if user_level < user_level_low_bound:
            return_msg['error'] = 'User has permission to do this job'
            return return_msg

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
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

        receive_msg = check_user_level(str(user_id))
        if 'fail' in receive_msg:
            return_msg['result'] = receive_msg['error']
        
        #get new file place
        with DataTypeDao() as dataTypeDao:
            type_dir = dataTypeDao.getTypeDir(typeId=str(type_id))
        try:
            img_new_file_dir = os.path.join(server_dir, "static",type_dir)
        except:
            return_msg["error"] = "no such type id : " + str(type_id)
            return return_msg

        #generate new id
        with ImageDao() as imageDao:
            img_id = imageDao.generateNewId()
        
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
            return_msg["error"] = "copy or remove file error"
            return return_msg

        #insert images data to mysql
        img_data = {}
        img_data["id"] = img_id
        img_data["typeId"] = str(type_id)
        img_data["systemName"] = img_system_name
        img_data["thumbnailName"] = img_thumbnail_name
        img_data["fileName"] = img_file_name
        img_data["startDate"] = img_start_date
        img_data["endDate"] = img_end_date
        img_data["startTime"] = img_start_time
        img_data["endTime"] = img_end_time
        img_data["displayTime"] = str(img_display_time)
        img_data["userId"] = str(user_id)
        try:
            with ImageDao() as imageDao:
                imageDao.insertImgData(imgData=img_data)
        except DB_Exception as e:
            return_msg["error"] = "insert mysql error please check file system " + img_system_dir
            try:
                copyfile(img_system_dir, img_file_dir)
                if os.path.isfile(img_file_dir) and os.path.isfile(img_system_dir):
                    os.remove(img_system_dir)
                return_msg["error"] = "insert mysql error please check file system " + img_file_dir
            except:
                "DO NOTHING"
            return return_msg

        return_msg["img_id"] = img_id
        return_msg["img_system_dir"] = img_system_dir
        return_msg["img_thumbnail_name"] = img_thumbnail_name
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
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
        
        #check user level
        with UserDao() as userDao:
            user_level = userDao.getUserLevel(user_id)
        if not user_level:
            return_msg['error'] = 'No user_id "{user_id}"'.format(user_id=user_id)
            return return_msg
        else:
            if user_level < user_level_low_bound:
                return_msg["error"] = "user right is too low"
                return return_msg
            #check self image
            with ImageDao() as imageDao:
                imgInfo = imageDao.getIdSysName(Id=str(img_id))
            try:
                if imgInfo["userId"] != user_id and user_level < user_level_high_bound:
                    return_msg["error"] = "can not modify other user image "
                    return return_msg
                img_type_id = imgInfo["typeId"]
            except:
                return_msg["error"] = "no such image id : {img_id}".format(img_id=img_id)
                return return_msg    
        
        #check if we need to move the file
        old_dir = ""
        new_dir = ""
        if img_type_id == type_id:
            "DO NOTHING"
        else :
            #get img_system_name
            with ImageDao() as imageDao:
                img_info = imageDao.getIdSysName(Id=str(img_id))
                img_sys_name = img_info["systemName"]
            if img_sys_name: 
                old_dir = img_sys_name
                new_dir = img_sys_name
            else:
                return_msg["error"] = "no such image id : {img_id}".format(img_id=img_id)
                return return_msg
            
            #get old image type dir
            with DataTypeDao() as dataTypeDao:
                type_dir = dataTypeDao.getTypeDir(typeId=str(img_type_id))
            if type_dir: 
                old_dir = type_dir + old_dir
            else:
                return_msg["error"] = "no such image type : {type_id}".format(type_id=str(img_type_id))
                return return_msg
                    
            #get new image type dir
            with DataTypeDao() as dataTypeDao:
                type_dir = dataTypeDao.getTypeDir(typeId=str(type_id))
            if type_dir: 
                new_dir = type_dir + new_dir
            else:
                return_msg["error"] = "no such image type : {type_id}".format(type_id=str(type_id))
                return return_msg
            
            #check if we need to move the file
            if old_dir == new_dir:
                "DO NOTHING"
            else :
                try:
                    old_dir = os.path.join(server_dir,"static",old_dir)
                    new_dir = os.path.join(server_dir,"static",new_dir)
                    copyfile(old_dir, new_dir)
                    if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                        os.remove(old_dir)
                except:
                    try:
                        if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                            os.remove(new_dir)
                    except:
                        "DO NOTHING"
                    return_msg["error"] = "move file error : " + old_dir
                    return return_msg
        
        #start to modify mysql
        img_data = {}
        img_data["typeId"] = str(type_id)
        img_data["startDate"] = img_start_date
        img_data["endDate"] = img_end_date
        img_data["startTime"] = img_start_time
        img_data["endTime"] = img_end_time
        img_data["displayTime"] = str(img_display_time)
        img_data["editUserId"] = str(user_id)
        img_data["Id"] = img_id
        try:
            with ImageDao() as imageDao:
                imageDao.updateEditedData(data=img_data)
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
                    return_msg["error"] = "move file error : duplicate files : " + old_dir
                    return return_msg
                return_msg["error"] = "move file error : " + new_dir
                return return_msg
            return_msg["error"] = "update mysql error"
            return return_msg

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

#never debug this function
def upload_text_insert_db(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
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

        
        receive_msg = check_user_level(user_id)
        if 'fail' in receive_msg:
            return_msg['result'] = receive_msg['error']

        #generate new id
        with TextDao() as textDao:
            text_id = textDao.generateNewId()

        if "invisible_title" in json_obj:
            invisible_title = json_obj["invisible_title"]
        else:
            invisible_title = text_id
        
        #get file place
        with DataTypeDao() as dataTypeDao:
            type_dir = dataTypeDao.getTypeDir(typeId=str(type_id))
        try:
            text_system_name = text_id + ".txt"
            system_file_dir = os.path.join(server_dir, "static", type_dir)
            system_file_dir = os.path.join(system_file_dir, text_system_name)
        except:
            return_msg["error"] = "no such type id : " + str(type_id)
            return return_msg
        
        #insert text data to mysql
        text_data = {}
        text_data["id"] = text_id
        text_data["typeId"] = str(type_id)
        text_data["systemName"] = text_system_name
        text_data["invisibleTitle"] = invisible_title
        text_data["startDate"] = text_start_date
        text_data["endDate"] = text_end_date
        text_data["startTime"] = text_start_time
        text_data["endTime"] = text_end_time
        text_data["displayTime"] = str(text_display_time)
        text_data["userId"] = str(user_id)
        with TextDao() as textDao:
            textDao.insertData(data=text_data)

        return_msg["text_id"] = text_id
        return_msg["text_system_dir"] = system_file_dir
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg    

#
def edit_text_data(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
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
        
        #check user level
        with UserDao() as userDao:
            user_level = userDao.getUserLevel(user_id)
        if not user_level:
            return_msg['error'] = 'No user_id "{user_id}"'.format(user_id=user_id)
            return return_msg
        else:
            if user_level < user_level_low_bound:
                return_msg["error"] = "user right is too low"
                return return_msg
            #check self text
            with TextDao() as textDao:
                textInfo = textDao.getIdSysName(Id=str(text_id))
            try:
                if textInfo["userId"] != user_id and user_level < user_level_high_bound:
                    return_msg["error"] = "can not modify other user text"
                    return return_msg
                text_type_id = int(textInfo["typeId"])
            except:
                return_msg["error"] = "no such text id : {text_id}".format(text_id=text_id)
                return return_msg
        
        old_dir = ""
        new_dir = ""
        #get text_system_name
        with TextDao() as textDao:
            text_info = textDao.getIdSysName(Id=str(text_id))
            text_sys_name = text_info["systemName"]
        try: 
            old_dir = text_sys_name
            new_dir = text_sys_name
        except:
            return_msg["error"] = "no such text id : {text_id}".format(text_id=text_id)
            return return_msg
        
        #get old text type dir
        with DataTypeDao() as dataTypeDao:
            type_dir = dataTypeDao.getTypeDir(typeId=str(text_type_id))
        try: 
            old_dir = type_dir + old_dir
        except:
            return_msg["error"] = "no such text type : " + str(text_type_id)
            return return_msg

        #check if we need to move the file
        if text_type_id == type_id:
            old_dir = os.path.join(server_dir,"static",old_dir)
            new_dir = old_dir
        else :  
            #get new text type dir
            with DataTypeDao() as dataTypeDao:
                type_dir = dataTypeDao.getTypeDir(typeId=str(type_id))
            try: 
                new_dir = type_dir + new_dir
            except:
                return_msg["error"] = "no such text type : " + str(type_id)
                return return_msg

            #check if we need to move the file
            if old_dir == new_dir:
                new_dir = 'static/'+new_dir
            else :
                try:
                    old_dir = os.path.join(server_dir,"static",old_dir)
                    new_dir = os.path.join(server_dir,"static",new_dir)
                    copyfile(old_dir, new_dir)
                    if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                        os.remove(old_dir)
                except:
                    try:
                        if os.path.isfile(old_dir) and os.path.isfile(new_dir):
                            os.remove(new_dir)
                    except:
                        "DO NOTHING"
                    return_msg["error"] = "move file error : " + old_dir
                    return return_msg
            with open(new_dir,'w') as fp:
                print(json.dumps(text_file),file=fp)
        
        #start to modify mysql
        text_data = {}
        text_data["typeId"] = str(type_id)
        text_data["invisibleTitle"] = invisible_title
        text_data["startDate"] = text_start_date
        text_data["endDate"] = text_end_date
        text_data["startTime"] = text_start_time
        text_data["endTime"] = text_end_time
        text_data["displayTime"] = str(text_display_time)
        text_data["editUserId"] = str(user_id)
        text_data["Id"] = text_id
        try:
            with TextDao() as textDao:
                textDao.updateEditedData(data=text_data)
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
                    return_msg["error"] = "move file error : duplicate files : " + old_dir
                    return return_msg
                return_msg["error"] = "move file error : " + new_dir
                return return_msg
            return_msg["error"] = "update mysql error"
            return return_msg

        return_msg["result"] = "success"
        return_msg["text_system_dir"] = new_dir
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg  

#
def delete_image_or_text_data(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
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
        
        #check user level
        with UserDao() as userDao:
            user_level = userDao.getUserLevel(user_id)
        if not user_level:
            return_msg['error'] = 'No user_id "{user_id}"'.format(user_id=user_id)
            return return_msg
        else:
            if user_level < user_level_low_bound:
                return_msg["error"] = "user right is too low"
                return return_msg
            #check self data and get type_id
            if target_id[0:4] == "imge":
                with ImageDao() as imageDao:
                    info = imageDao.getIdSysName(Id=target_id)
            elif target_id[0:4] == "text":
                with TextDao() as textDao:
                    info = textDao.getIdSysName(Id=target_id)
            else :
                return_msg["error"] = "target id type error"
                return return_msg
            try:
                if info["userId"] != user_id and user_level < user_level_high_bound:
                    return_msg["error"] = "can not modify other user image or text"
                    return return_msg
                target_type_id =  int(info["typeId"])
                target_dir = info["systemName"]
            except:
                return_msg["error"] = "no such target id : " + str(target_id)
                return return_msg
        
        #get file place
        with DataTypeDao() as dataTypeDao:
            type_dir = dataTypeDao.getTypeDir(typeId=str(target_type_id))
        try:
            trash_dir = os.path.join(server_dir, "static", "trash_data", target_dir)
            system_file_dir = os.path.join(server_dir, "static", type_dir)
            target_dir = os.path.join(system_file_dir, target_dir)
        except:
            return_msg["error"] = "no such type id : " + str(type_id)
            return return_msg

        #check trash_data 
        if not os.path.exists(os.path.split(trash_dir)[0]):
            try:
                os.makedirs(os.path.split(trash_dir)[0])
            except:
                return_msg["error"] = "no trash_data folder"
                return return_msg

        #move to trash
        if os.path.isfile(target_dir):
            try:
                shutil.move(target_dir, trash_dir)
            except:
                return_msg["error"] = "move fail"
                return return_msg

        if target_id[0:4] == "imge":
            with ImageDao() as imageDao:
                imageDao.markDeleted(target_id,user_id)
        elif target_id[0:4] == "text":
            with TextDao() as textDao:
                textDao.markDeleted(target_id,user_id)

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg  

def add_new_data_type(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        type_name = json_obj['type_name']

        with DataTypeDao() as dataTypeDao:
            existed = dataTypeDao.checkTypeExisted(typeName=type_name)
        if existed:
            return_msg["error"] = "Type name has existed"
            return return_msg

        with DataTypeDao() as dataTypeDao:
            dataTypeDao.insertType(typeName=type_name)

        if not os.path.exists("static/"+type_name):
            os.makedirs("static/"+type_name)

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg  


#
def change_password(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        try:
            user_name = json_obj["user_name"]
            old_password = json_obj["old_password"]
            new_password = json_obj["new_password"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg
        
        #get user_id 
        user_name = user_name.decode('utf-8')
        user_id  = get_user_id(user_name)
        if type(user_id) == type(dict()):
            return_msg["error"] = "no such user name"
            return return_msg

        #check user
        with UserDao() as userDao:
            password = userDao.getUserPassword(userId=user_id)
        hashed_key = ""
        try:
            hashed_key = password.encode('utf-8')
            if bcrypt.checkpw(old_password.encode('utf-8'),hashed_key):
                # old password correct
                hashed_key = bcrypt.hashpw(new_password.encode('utf-8'),bcrypt.gensalt())
                with UserDao() as userDao:
                    userDao.updatePassword(hashed_key.decode('utf-8'),userId=str(user_id))
            else:
                return_msg["error"] = "old password incorrect"
                return return_msg
        except Exception as e:
            return_msg["error"] = str(e)
            return return_msg

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def read_text_data(text_id):
    try:
        return_msg = {}
                
        with TextDao() as textDao:
            info = textDao.getIdSysName(Id=text_id)
        text_file_name = info["systemName"]
        type_id = info["typeId"]

        with DataTypeDao() as dataTypeDao:
            type_dir = dataTypeDao.getTypeDir(typeId=str(type_id))
        
        filename = 'static/' + type_dir + text_file_name
        with open(filename,'r') as fp:
            text_content = json.load(fp)

        for key in text_content:
            text_content[key] = text_content[key].replace('<br/>','\n').replace('&nbsp',' ').replace('<br>','\n')

        return text_content
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

# for google api
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly','https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret.json'
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

#crawler handle
def news_insert_db(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        news_data_type = 1
        news_title = ""
        news_serial_number = ""

        try:
            news_data_type = json_obj["data_type"]
            news_title = json_obj["title"]
            news_serial_number = json_obj["serial_number"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        with NewsQRCodeDao() as newsQRCodeDao:
            exist = newsQRCodeDao.checkNewsExisted(news_serial_number)

        if not exist:
            with NewsQRCodeDao() as newsQRCodeDao:
                newsQRCodeDao.insertNews(news_data_type,news_serial_number,news_title)

        return_msg["result"] = "success"

    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def fortune_insert_db(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        constellation = ""
        overall = ""
        love = ""
        career = ""
        wealth = ""
        date = str(datetime.date.today())
        try:
            constellation = json_obj["constellation"]
            overall = json_obj["overall"]
            love = json_obj["love"]
            career = json_obj["career"]
            wealth = json_obj["wealth"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        #check
        with FortuneDao() as fortuneDao:
            existed = fortuneDao.checkFortuneExisted(date=date,constellation=constellation)

        if not existed:
            with FortuneDao() as fortuneDao:
                fortuneDao.insertFortune(date,constellation,overall,love,career,wealth)

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

