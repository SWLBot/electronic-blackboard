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
from util import switch
import config.settings as setting
from dataAccessObjects import *
from modeUtil import ModeUtil
from worker import *

#make now activity to is used
def mark_now_activity():
    try:
        return_msg = {}
        return_msg["result"] = "fail"
    
        #find schedule
        with ScheduleDao() as scheduleDao:
            target_sn = scheduleDao.getDisplayingSchedule()
        if not target_sn:
            #no schedule to mark
            return_msg["result"] = "success"
            return return_msg
    
        #mark target
        with ScheduleDao() as scheduleDao:
            scheduleDao.markExpiredSchedule(target_sn)
    
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg
        
#child function of load_next_schedule
def find_next_schedule():
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        with ScheduleDao() as scheduleDao:
            ret = scheduleDao.getNextSchedule()

        if ret:
            return_msg.update(ret)
        else:
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
        
        while True:
            #find schedule
            receive_msg = {}
            receive_msg = find_next_schedule()
            if receive_msg["result"]=="fail":
                return_msg["error"] = receive_msg["error"]
                return return_msg
            
            return_msg["schedule_id"] = receive_msg["schedule_id"]
            sche_target_id = receive_msg["sche_target_id"]
            return_msg["display_time"] = receive_msg["display_time"]
            no_need_check_time = receive_msg["no_need_check_time"]
            target_sn = receive_msg["target_sn"]
    
            #find the file
            if sche_target_id[0:4]=="imge":
                with ImageDao() as imageDao:
                    file_info= imageDao.getFileInfo(sche_target_id)
                return_msg["file_type"] = "image" 
            elif sche_target_id[0:4]=="text":
                with TextDao() as textDao:
                    file_info = textDao.getFileInfo(sche_target_id)
                return_msg["file_type"] = "text"
            else :
                if target_sn != 0:
                    with ScheduleDao() as scheduleDao:
                        scheduleDao.markExpiredSchedule(target_sn)
                    target_sn = 0
                continue

            if file_info:
                type_id = file_info['typeId']
                system_file_name = file_info['systemFileName']
            else:
                if target_sn != 0:
                    with ScheduleDao() as scheduleDao:
                        scheduleDao.markExpiredSchedule(target_sn)
                    target_sn = 0
                continue
    
            # check display target expired
            if no_need_check_time == b'\x00':
                if return_msg["file_type"]=="image":
                    with ImageDao() as imageDao:
                        expired = imageDao.checkExpired(sche_target_id)
                elif return_msg["file_type"]=="text":
                    with TextDao() as textDao:
                        expired = textDao.checkExpired(sche_target_id)
                else:
                    "impossible"

                if expired:
                    if target_sn != 0:
                        with ScheduleDao() as scheduleDao:
                            scheduleDao.markExpiredSchedule(target_sn)
                        target_sn = 0
                    continue
            
            #find type dir
            check_target_dir = ""
            with DataTypeDao() as dataTypeDao:
                type_dir = dataTypeDao.getTypeDir(type_id)
            if type_dir:
                check_target_dir = os.path.join(target_dir,'static',
                                        type_dir,system_file_name)
            else:
                # mark activity is used
                if target_sn != 0:
                    with ScheduleDao() as scheduleDao:
                        scheduleDao.markExpiredSchedule(scheSn=target_sn)
                    target_sn = 0
                continue
    
            #if text read file
            if not os.path.isfile(check_target_dir) :
                if target_sn != 0:
                    with ScheduleDao() as scheduleDao:
                        scheduleDao.markExpiredSchedule(target_sn)
                    target_sn = 0
                continue
            else :
                return_msg["file"] = check_target_dir
                break
        
        #check less activity number
        with ScheduleDao() as scheduleDao:
            return_msg['last_activity'] = scheduleDao.countUndisplaySchedule()
        if not return_msg['last_activity']:
            return_msg["error"] = "sql error"
            return return_msg

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
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

        #find texts that may be schedule
        orderById = ModeUtil.checkOrderById(arrange_mode)

        conditionAssigned = ModeUtil.checkConditionAssigned(arrange_mode)

        with TextDao() as textDao:
            pure_result= textDao.findActivities(conditionAssigned,orderById,arrange_mode,arrangeCondition=arrange_condition)
        #restruct results of query
        for result_row in pure_result:
            if len(result_row)==2:
                deal_result.append([result_row[0], int(result_row[1])])
            elif len(result_row)==3:
                deal_result.append([result_row[0], int(result_row[1]), float(result_row[2])])
            else:
                "DO NOTHING"
        
        candidates = ModeUtil.selectDisplayCandidates(arrange_mode,deal_result)

        return_msg["ans_list"] = candidates
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
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
        
        #find images that may be schedule
        orderById = ModeUtil.checkOrderById(arrange_mode)

        conditionAssigned = ModeUtil.checkConditionAssigned(arrange_mode)

        with ImageDao() as imageDao:
            pure_result= imageDao.findActivities(conditionAssigned,orderById,arrange_mode,arrangeCondition=arrange_condition)
        #restruct results of query
        for result_row in pure_result:
            if len(result_row)==2:
                deal_result.append([result_row[0], int(result_row[1])])
            elif len(result_row)==3:
                deal_result.append([result_row[0], int(result_row[1]), float(result_row[2])])
            else:
                "DO NOTHING"
         
        candidates = ModeUtil.selectDisplayCandidates(arrange_mode,deal_result)

        return_msg["ans_list"] = candidates
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def mix_image_and_text(arrange_mode,deal_obj):
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
    return deal_obj

#The API connect mysql and find image data that can be scheduled
def find_activity(json_obj):
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

    if arrange_mode in [3,4,5,7] and len(arrange_condition) == 0:
        return_msg["error"] = 'Then arrange mode {mode} need to assgin condition'.format(mode=arrange_mode)
        return return_msg
    
    #get text activity
    receive_obj = find_text_acticity(json_obj)
    if receive_obj["result"] == "success":
        for text_data in receive_obj['ans_list']:
            deal_obj.append(text_data)
    
    #get image activity
    receive_obj = find_image_acticity(json_obj)
    if receive_obj["result"] == "success":
        for image_data in receive_obj['ans_list']:
            deal_obj.append(image_data)
    
    deal_obj = mix_image_and_text(arrange_mode,deal_obj)

    #reshape data
    content_id = ""
    content_time = 5
    return_msg["target_id"] = []
    return_msg["display_time"] = []
    for display_data in deal_obj:
        try:
            content_id = str(display_data[0])
            content_time = int(display_data[1])
        except:
            continue
        return_msg["target_id"].append(content_id)
        return_msg["display_time"].append(content_time)

    return_msg["result"] = "success"
    return return_msg

#The API connect mysql and clean expire data
def expire_data_check_():
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        deal_result = []

        with ImageDao() as imageDao:
            pure_result = imageDao.getExpiredIds()

        #update expire data
        for expired_image_id in pure_result:
            deal_result.append(expired_image_id[0])
            try:
                with ImageDao() as imageDao:
                    imageDao.markExpired(expired_image_id[0])
            except DB_Exception as e:
                return_msg["error"] = e.args[1]
                
        if "error" in return_msg:
            return return_msg

        #find expire text data
        with TextDao() as textDao:
            pure_result = textDao.getExpiredIds()

        #update expire data
        for expired_text_id in pure_result:
            deal_result.append(expired_text_id[0])
            try:
                with TextDao() as textDao:
                    textDao.markExpired(expired_text_id[0])
            except DB_Exception as e:
                return_msg["error"] = e.args[1]
                
        if "error" in return_msg:
            return return_msg
        
        for target_id in deal_result:
            try:
                with ScheduleDao() as scheduleDao:
                    scheduleDao.markExpiredSchedule(targetId=target_id)
            except DB_Exception as e:
                return_msg["error"] = e.args[1]
                
        if "error" in return_msg:
            return return_msg

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

#The API connect mysql and add activity to schedule
def edit_schedule(json_obj):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        sn_offset = 0
        target_id_list = []
        display_time_list = []
        target_id = ""
        display_time = 5
        arrange_mode_sn = 1
        try:
            sn_offset = json_obj["sn_offset"]
            target_id_list = json_obj["target_id"]
            display_time_list = json_obj["display_time"]
            arrange_mode_sn = json_obj["arrange_sn"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        for num0 in range(len(display_time_list)):
            target_id = target_id_list[num0]
            display_time = int(display_time_list[num0])
            
            #get now sn
            with ScheduleDao() as scheduleDao:
                target_sn = scheduleDao.getDisplayingSchedule()
            if target_sn:
                #check use update or insert
                with ScheduleDao() as scheduleDao:
                    sche_sn = scheduleDao.getEditScheSn(scheSn=target_sn+sn_offset)
                if sche_sn:
                    with ScheduleDao() as scheduleDao:
                        scheduleDao.updateEditSchedule(target_id,display_time,arrange_mode_sn,sche_sn)
                else:
                    with ScheduleDao() as scheduleDao:
                        scheduleDao.insertUndecidedSchedule(target_id,display_time,arrange_mode_sn)
                        sche_sn = scheduleDao.getUndecidedScheduleSn()
                    if sche_sn:
                        new_id = "sche" + "{0:010d}".format(int(sche_sn))
                        with ScheduleDao() as scheduleDao:
                            scheduleDao.updateNewIdSchedule(new_id,sche_sn)
                    else :
                        return_msg["error"] = "may be another arrange.exe is working"
                        return return_msg
            else :
                with ScheduleDao() as scheduleDao:
                    scheduleDao.insertUndecidedSchedule(target_id,display_time,arrange_mode_sn)
                    sche_sn = scheduleDao.getUndecidedScheduleSn()
                if sche_sn:
                    new_id = "sche" + "{0:010d}".format(int(sche_sn))
                    with ScheduleDao() as scheduleDao:
                        scheduleDao.updateNewIdSchedule(new_id,sche_sn)
                else :
                    return_msg["error"] = "may be another arrange.exe is working"
                    return return_msg
            sn_offset += 1

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
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

        for num0 in range(len(display_time_list)):
            target_id = target_id_list[num0]
            display_time = int(display_time_list[num0])
            
            #insert
            with ScheduleDao() as scheduleDao:
                scheduleDao.insertUndecidedSchedule(target_id,display_time,arrange_mode_sn)
                sche_sn = scheduleDao.getUndecidedScheduleSn()
            if sche_sn:
                new_id = "sche" + "{0:010d}".format(int(sche_sn))
                with ScheduleDao() as scheduleDao:
                    scheduleDao.updateNewIdSchedule(new_id,sche_sn)
            else :
                return_msg["error"] = "may be another arrange.exe is working"
                return return_msg

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

#The API connect mysql and clean non used schedule
def clean_schedule():
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        with ScheduleDao() as scheduleDao:
            scheduleDao.cleanSchedule()

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
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
        
        with ScheduleDao() as scheduleDao:
            is_used_count = scheduleDao.countUsedSchedule()
        
        #if log > max_is_used then clean up
        if is_used_count > max_is_used:
            #get schedule
            with ScheduleDao() as scheduleDao:
                schedules = scheduleDao.getUsedSchedule(limitCount=str(is_used_count - max_is_used))

            #generate log
            date_now = date.today()
            schedule_file = 'schedule_{year}_{month}_{day}.txt'.format(year=date_now.year,month=date_now.month,day=date_now.day)
            schedule_file = os.path.join(log_dir,'static','log',schedule_file)
            try:
                if not os.path.isfile(schedule_file) :
                    file_pointer = open(schedule_file, "w")
                else :
                    file_pointer = open(schedule_file, "a")

                for schedule in schedules:
                    write_str = ""
                    for attr in schedule:
                        write_str = write_str + str(attr) + " "
                    write_str = write_str + "\n"
                    file_pointer.write(write_str)
                file_pointer.close()
            except:
                return_msg["error"] = "Error occurred when writing to log file"
                return return_msg
            
            #delete schedule
            for schedule in schedules:
                with ScheduleDao() as scheduleDao:
                    scheduleDao.cleanSchedule(scheSn=schedule[0])
        
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

#future can write to log.txt. now just print it
def read_system_setting():
    return_msg = {}
    return_msg["result"] = "fail"
    
    try:
        return_msg["board_py_dir"] = setting.arrange_setting['board_py_dir']
        return_msg["shutdown"] = setting.arrange_setting['shutdown']
        return_msg["max_db_log"] = setting.arrange_setting['max_db_log']
        return_msg["min_db_activity"] = setting.arrange_setting['min_db_activity']
    except Exception as e:
        return_msg["error"] = str(e)
        return return_msg

    return_msg["result"] = "success"
    return return_msg

#future can write to log.txt. now just print it
def read_arrange_mode():
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        with ArrangeModeDao() as arrangeModeDao:
            arrange_mode = arrangeModeDao.getArrangeMode()

        if arrange_mode:
            return_msg.update(arrange_mode)
        else:
            return_msg["error"] = "no match schedule mode"
            return return_msg

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def find_cwb_type_id():
    return_msg = {}
    with DataTypeDao() as dataTypeDao:
        typeId = dataTypeDao.getTypeId('氣像雲圖')
    if typeId != None:
        return typeId
    else:
        return -1

def delete_old_cwb_img(server_dir,user_id):
    send_obj = {}
    error_list_id = []
    with ImageDao() as imageDao:
        Ids=imageDao.getCwbImgIds()
    for num2 in range(len(Ids)):
        try:
            send_obj["server_dir"] = server_dir
            send_obj["target_id"] = str(Ids[num2][0])
            send_obj["user_id"] = user_id
            receive_obj = delete_image_or_text_data(send_obj)
            if receive_obj["result"] == "fail":
                error_list_id.append(send_obj["target_id"])
        except:
            error_list_id.append(send_obj["target_id"])
            continue
    return error_list_id

def mark_old_cwb_img(error_list_id):
    for error_id in error_list_id:
        with ImageDao() as imageDao:
            imageDao.markExpired(targetId=error_id,markOldData=True)

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

        data_type = find_cwb_type_id()
        if data_type == -1:
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

            error_list_id = delete_old_cwb_img(server_dir,user_id)

            mark_old_cwb_img(error_list_id)

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
                    return_msg = receive_obj
                    return return_msg
            except:
                return_msg["error"] = "save thumbnail image fail"
                return return_msg
                
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def google_calendar_text():
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        credentials = get_credentials()
        if not credentials:
            return_msg["error"] = "No credential file"
            return return_msg
        else:
            try:
                events = get_upcoming_events(credentials)
                for e in events:
                    check_event_exist_or_insert(e)
                    sleep(1.5)
                return_msg["result"] = "success"
                return return_msg
            except DB_Exception as e:
                return_msg["error"] = e.arg[1]
                return return_msg
    except Exception as e:
        return_msg["error"] = str(e)
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
    with TextDao() as textDao:
        existed = textDao.checkExisted(event_id)
    if existed:
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

def find_drive_data_type():
    return_msg = {}
    with DataTypeDao() as dataTypeDao:
        typeId = dataTypeDao.getTypeId('google_drive_image')
    if typeId != None:
        return_msg['data_type'] = int(typeId)
        return_msg['result'] = 'success'
        return return_msg
    else:
        return_msg['error'] = "no google_drive_image data type"
        return_msg['result'] = 'fail'
        return return_msg

def search_google_drive_folder(service):
    g_sql = "(name='1day' or name='3day' or name='7day' or name='14day')"
    results = service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and trashed=false and " + g_sql, 
        fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    return items

def search_google_drive_file(service):
    #set time
    now_time = time.time()
    start_time = time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime(now_time-43200))
    results = service.files().list(
        q="modifiedTime > '" + start_time + "' and mimeType contains 'image/'", 
        fields="nextPageToken, files(id, name, parents)").execute()
    items = results.get('files', [])
    return items
    
def merge_files_and_days(days_limit, drive_file):
    for num1 in range(len(drive_file)):
        drive_file[num1]['time'] = 86400*7
        for item in days_limit:
            if item['id'] in drive_file[num1]['parents']:
                drive_file[num1]['time'] = 86400 * int(item['name'][:-3])
                break
    return drive_file

def check_drive_img_exist(data_type, file_name):
    with ImageDao() as imageDao:
        return imageDao.checkExisted(typeId=data_type,fileName=file_name)

def save_google_drive_file(service, json_obj):
    try:
        return_msg={}
        return_msg['result'] = 'fail'
        for item in json_obj['files']:
            file_name = item['id'] + os.path.splitext(item['name'])[1]
            download_file_place = os.path.join(json_obj['server_dir'],'static','img',file_name)
            
            #check if file is existed
            if check_drive_img_exist(json_obj['data_type'], file_name):
                continue
            
            #download files
            request = service.files().get_media(fileId=item['id'])
            fh = io.FileIO(download_file_place, mode='wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            #upload new file
            send_obj = {}
            send_obj["server_dir"] = json_obj['server_dir']
            send_obj["file_type"] = json_obj['data_type']
            send_obj["file_dir"] = 'static/img/' + file_name
            send_obj["start_date"] = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            send_obj["end_date"] = time.strftime("%Y-%m-%d", time.localtime(time.time()+item['time']))
            send_obj["start_time"] = "00:00:00"
            send_obj["end_time"] = "23:59:59"
            send_obj["display_time"] = 3
            send_obj["user_id"] = json_obj['user_id']
            receive_obj = upload_image_insert_db(send_obj)

            #save thumbnail image
            try:
                if receive_obj["result"] == "success":
                    filepath = receive_obj["img_system_dir"]
                    thumbnail_path = "static/thumbnail/"
                    thumbnail_path = os.path.join(thumbnail_path,receive_obj["img_thumbnail_name"])
                    im = Image.open(filepath)
                    im.thumbnail((100,100))
                    im.save(thumbnail_path)
                else:
                    return_msg = receive_obj
                    return return_msg
            except:
                return_msg["error"] = "save thumbnail image fail"
                return return_msg
        return_msg['result'] = 'success'
        return return_msg
    except Exception as e:
        return_msg["error"] = str(e)
        return return_msg

def search_google_drive(service):
    # find folder
    days_limit = search_google_drive_folder(service)

    # find file
    drive_file = search_google_drive_file(service)

    # merge files and days limit
    receive_msg = merge_files_and_days(days_limit, drive_file)

    return receive_msg

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
        receive_obj = {}

        #find google_drive_image type id 
        receive_msg = find_drive_data_type()
        if receive_msg['result']=='fail':
            return receive_msg
        else:
            json_obj['data_type'] = receive_msg['data_type']
        
        #get google credentials
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('drive', 'v3', http=http)

        #search_google_drive
        json_obj['files'] = search_google_drive(service)

        #deal with files
        receive_msg = save_google_drive_file(service, json_obj)
        if receive_msg['result']=='fail':
            return receive_msg

        return_msg["result"] = "success"
        return return_msg
    except Exception as e:
        return_msg["error"] = str(e)
        return return_msg 

def crawler_news(website):
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        #check if table 'news_QR_code' exists
        check_table(news=True)

        with DataTypeDao() as dataTypeDao:
            existed = dataTypeDao.checkTypeExisted(website)
        if not existed:
            create_data_type(website)

        for case in switch(website):
            if case('inside'):
                #start grab INSIDE info
                try:
                    grab_inside_articles()
                except:
                    return_msg["error"] = "ERROR occurs in INSIDE crawler. Please check the correction of news_crawler"
                    return return_msg
                break
            if case('techOrange'):
                #start grab TECHORANGE info
                try:
                    grab_techorange_articles()
                except:
                    return_msg["error"] = "ERROR occurs in TECHORANGE crawler. Please check the correction of news_crawler"
                    return return_msg
                break
            if case('medium'):
                #start grab MEDIUM info
                try:
                    grab_medium_articles()
                except:
                    return_msg["error"] = "ERROR occurs in MEDIUM crawler. Please check the correction of news_crawler"
                    return return_msg
                break
        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def crawler_ptt_news(boards):
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        #check if table 'news_QR_code' exists
        check_table(news=True)
        
        for board in boards:
            typeName = 'ptt'+board
            with DataTypeDao() as dataTypeDao:
                existed = dataTypeDao.checkTypeExisted(typeName)
            if not existed:
                create_data_type(typeName)

        #board with data_type but no crawling
        inhibit_boards = ["Beauty"]
        #start grab PTT info
        try:
            allow_boards=list(set(boards) - set(inhibit_boards))
            grab_ptt_articles(allow_boards)
        except:
            return_msg["error"] = "ERROR occurs in PTT crawler. Please check the correction of news_crawler"
            return return_msg

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def crawler_constellation_fortune():
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        #check if table 'fortune' exists
        check_table(fortune=True)
        #start grab CONSTELLATION FORTUNE info
        try:
            grab_constellation_fortune()
        except:
            return_msg["error"] = "ERROR occurs in FORTUNE crawler. Please check the correction of news_crawler"
            return return_msg

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = e.args[1]
        return return_msg

def check_table(news=False,fortune=False):
    with DatabaseDao() as databaseDao:
        if news:
            existed = databaseDao.checkTableExisted('news_QR_code')
            if not existed:
                return create_news_table()
        elif fortune:
            existed = databaseDao.checkTableExisted('fortune')
            if not existed:
                return create_fortune_table()
    return dict(result='success')

def crawler_schedule():
    try:
        boards=['joke','StupidClown','Beauty']
        return_msg = {}
        return_msg["result"] = "fail"
        
        return_inside = crawler_news('inside')
        return_techorange = crawler_news('techOrange')
        return_medium = crawler_news('medium')
        return_ptt = crawler_ptt_news(boards)
        return_fortune = crawler_constellation_fortune()
        if return_inside["result"]=="success" and return_techorange["result"]=="success" \
            and return_ptt["result"]=="success" and return_medium["result"]=="success" \
            and return_fortune["result"]=="success":
            return_msg["result"] = "success"
        else:
            return_msg['error'] = 'crawler schedule failed'
        return return_msg
    except:
        print("crawler execution fail")
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
        
def expire_data_check():
    receive_obj = expire_data_check_()
    if receive_obj["result"] == "success":
        "DO NOTHING"
    else :
        receive_obj["error"] = "expire_data_check : {errorMsg}".format(errorMsg=receive_obj["error"])
        set_system_log(receive_obj)

def do_set_schedule_log():
    global board_py_dir
    global max_db_log
    send_obj = dict(board_py_dir=board_py_dir,max_db_log=max_db_log)
    receive_obj = set_schedule_log(send_obj)
    if receive_obj["result"] == "success":
        "DO NOTHING"
    else :
        receive_obj["error"] = "set_schedule_log : " + receive_obj["error"]
        set_system_log(receive_obj)

def do_cwb_crawler():
    global board_py_dir
    send_obj = dict(server_dir=board_py_dir,user_id=1)
    receive_obj = crawler_cwb_img(send_obj)
    if receive_obj["result"] == "success":
        "DO NOTHING"
    else :
        receive_obj["error"] = "crawler_cwb_img : " + receive_obj["error"]
        set_system_log(receive_obj)

def do_google_calendar():
    receive_obj = google_calendar_text()
    if receive_obj["result"] == "success":
        "DO NOTHING"
    else:
        receive_obj["error"] = "google_calendar_text" + receive_obj["error"]
        set_system_log(receive_obj)

def do_google_drive():
    global board_py_dir
    send_obj = dict(server_dir=board_py_dir,user_id=1)
    receive_obj = crawler_google_drive_img(send_obj)
    if receive_obj["result"] == "success":
        "DO NOTHING"
    else :
        receive_obj["error"] = "crawler_google_drive_img : " + receive_obj["error"]
        set_system_log(receive_obj)

def do_crawler_schedule():
    receive_obj = crawler_schedule()
    if receive_obj["result"] == "success":
        "DO NOTHING"
    else :
        receive_obj["error"] = "crawler_news : " + receive_obj["error"]
        set_system_log(receive_obj)

board_py_dir = ""
shutdown = 0
max_db_log = 100
min_db_activity = 10

def main():
    just_startup = 1
    arrange_mode_change = 0
    arrange_sn = 0
    arrange_mode = 0
    check_file_dir = "NO_FILE"
    condition = []
    send_obj = {}
    receive_obj = {}
    global board_py_dir
    global shutdown
    global max_db_log
    global min_db_activity

    #for non blocking fork
    signal.signal(signal.SIGCHLD, CHLD_handler)

    #read initial setting
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
    alarm_crawler_functions = raw_time + 15.0

    check_expire_data_worker = Worker(job=expire_data_check,name='Check expired data')
    set_schedule_log_worker = Worker(job=do_set_schedule_log,name='Set schedule log')
    cwb_crawler_worker = Worker(job=do_cwb_crawler,name='Crawler for cwb image')
    google_calendar_worker = Worker(job=do_google_calendar,name='Grab Google calendar event')
    google_drive_worker = Worker(job=do_google_drive,name='Grab Google drive image')
    crawler_schedule_worker = Worker(job=do_crawler_schedule,name='Crawler for news')

    #start scheduling
    while shutdown == 0:
        raw_time = time.time()
        now_time = time.localtime(raw_time)
        
        #read_system_setting
        if raw_time >= alarm_read_system_setting:
            print("#1 "+ time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time))
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
            fork_failed = check_expire_data_worker.do(timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time))
            if fork_failed:
                alarm_expire_data_check += 3.0
            else:
                alarm_expire_data_check += 1800.0
        
        #set_schedule_log
        if raw_time >= alarm_set_schedule_log:
            fork_failed = set_schedule_log_worker.do(timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time))
            if fork_failed:
                alarm_expire_data_check += 3.0
            else:
                alarm_expire_data_check += 1800.0

        #load next schedule
        if not os.path.isfile(check_file_dir) or raw_time >= alarm_load_next_schedule:
            print("#4 "+ time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time))
            #mark now activity
            if just_startup == 0:
                receive_obj = mark_now_activity()
                if receive_obj["result"] == "success":
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
            print("#5 "+ time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time))
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
                    receive_obj = find_activity(send_obj)
                    if receive_obj["result"] == "success":
                        "DO NOTHING"
                    else :
                        receive_obj["error"] = "find_activity : " + receive_obj["error"]
                        set_system_log(receive_obj)
                        os._exit(0)

                    #use add or edit schedule
                    send_obj["sn_offset"] = 3
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
            fork_failed = cwb_crawler_worker.do(time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time))
            if fork_failed:
                alarm_crawler_google_drive_img += 600.0
            else:
                alarm_crawler_google_drive_img += 3600.0

        #google calendar add to text data
        if raw_time >= alarm_google_calendar_text:
            fork_failed = google_calendar_worker.do(time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time))
            if fork_failed:
                alarm_google_calendar_text += 10.0
            else:
                alarm_google_calendar_text += 43200.0
        
        #google drive add to text data
        if raw_time >= alarm_crawler_google_drive_img:
            fork_failed = google_drive_worker.do(time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time))
            if fork_failed:
                alarm_crawler_google_drive_img += 600.0
            else:
                alarm_crawler_google_drive_img += 3600.0

        #crawler
        if raw_time >= alarm_crawler_functions:
            fork_failed = crawler_schedule_worker.do(time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time))
            if fork_failed:
                alarm_crawler_functions += 600.0
            else:
                alarm_crawler_functions += 3600.0

        #delay
        sleep(0.1)
    print("arrange_schedule shutdown")
    sleep(10)
    return 1

if __name__ == "__main__":
    main()


