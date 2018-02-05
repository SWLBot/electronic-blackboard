from mysql import *
from server_api import *
from worker import *
from dataAccessObjects import *
from random import sample
from datetime import date
from time import sleep
from PIL import Image
from urllib import request
from apiclient.http import MediaIoBaseDownload
from apiclient import discovery
from news_crawler.news_crawler import *
from util import switch
from modeUtil import ModeUtil
from news_crawler import qrcode
import urllib
import httplib2
import io
import datetime
import signal
import time
import os.path
import json
import sys
import config.settings as setting

class loadScheduleError(Exception):
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return repr(self.value)

def gen_error_msg(msg=''):
    caller = sys._getframe(1).f_code.co_name
    return '[{caller}] : {msg}'.format(caller=caller,msg=msg)

def mark_now_activity():
    """
    Find out displaying schedule, then mark it expired
    """
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
        return_msg["error"] = gen_error_msg(e.args[1])
        return return_msg

def find_next_schedule():
    """
    Find out the next undisplayed schedule
    """
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
        return_msg["error"] = gen_error_msg(e.args[1])
        return return_msg

def get_candidates(arrange_mode_attr):
    """
    According current `arrange_mode` and `condition`, to find out
    candidates data returns to caller

    return candidates for displaying

    Variables:
    arrange_mode: Different mode has different method to select candidates
    arrange_condition: The type_id list of data_type will be used by some
        arrange_mode
    orderById: According to arrange_mode, the candidates should sort by id
        or not
    conditionAssigned: According to arrange_mode, the candidates should in
    arrange_condition or not.
    """
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        deal_result = []
        try:
            arrange_mode = arrange_mode_attr["arrange_mode"]
            arrange_condition = arrange_mode_attr.get('condition',[])
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        orderById = ModeUtil.checkOrderById(arrange_mode)

        conditionAssigned = ModeUtil.checkConditionAssigned(arrange_mode)

        with TextDao() as textDao:
            test_candidates= textDao.findActivities(conditionAssigned,orderById,arrange_mode,arrangeCondition=arrange_condition)
        
        with ImageDao() as imageDao:
            image_candidates= imageDao.findActivities(conditionAssigned,orderById,arrange_mode,arrangeCondition=arrange_condition)

        candidates = list(test_candidates) + list(image_candidates)

        for result_row in candidates:
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
        return_msg["error"] = gen_error_msg(e.args[1])
        return return_msg

def mix_image_and_text(arrange_mode,deal_obj):
    if arrange_mode in [0,3]:
        "DO NOTHING"
    elif arrange_mode in [1,4]:
        deal_obj = sample(deal_obj, len(deal_obj))
    elif arrange_mode in [2,5]:
        if len(deal_obj)>20:
            deal_obj = sample(deal_obj, 20)
    return deal_obj

def find_activity(json_obj):
    """
    According to the input arrange_mode setting, check the arrange mode consistence,
    and find out the text and image can be add into schedule, return the candidates
    """
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

    if arrange_mode in [3,4,5] and len(arrange_condition) == 0:
        return_msg["error"] = 'Then arrange mode {mode} need to assgin condition'.format(mode=arrange_mode)
        return return_msg

    receive_obj = get_candidates(json_obj)
    deal_obj = receive_obj['ans_list']
    
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

def expire_data_check():
    """
    Check text and image data has expired, and if it is in schedule,
    mark it expired, too.
    """
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        deal_result = []

        with ImageDao() as imageDao:
            pure_result = imageDao.getExpiredIds()

        #update expire data
        for expired_image_id in pure_result:
            deal_result.append(expired_image_id[0])
            with ImageDao() as imageDao:
                imageDao.markExpired(expired_image_id[0])

        #find expire text data
        with TextDao() as textDao:
            pure_result = textDao.getExpiredIds()

        #update expire data
        for expired_text_id in pure_result:
            deal_result.append(expired_text_id[0])
            with TextDao() as textDao:
                textDao.markExpired(expired_text_id[0])

        for target_id in deal_result:
            with ScheduleDao() as scheduleDao:
                scheduleDao.markExpiredSchedule(targetId=target_id)

        return_msg["result"] = "success"
        return return_msg
    except DB_Exception as e:
        return_msg["error"] = gen_error_msg(e.args[1])
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
        return_msg["error"] = gen_error_msg(e.args[1])
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
        return_msg["error"] = gen_error_msg(e.args[1])
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
        return_msg["error"] = gen_error_msg(e.args[1])
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
        return_msg["error"] = gen_error_msg(e.args[1])
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
        return_msg["error"] = gen_error_msg(e.args[1])
        return return_msg

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
        try:
            server_dir = json_obj["server_dir"]
            user_id = json_obj["user_id"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg
        now_time = time.time()
        send_obj = {}
        receive_obj = {}

        with DataTypeDao() as dataTypeDao:
            weather_data_type = dataTypeDao.getDataType(typeName='氣像雲圖')

        if weather_data_type is None:
            #TODO create cwb data_type
            return_msg["error"] = "no cwb img data type"
            return return_msg

        for num1 in range(60):
            target_img = 'CV1_TW_3600_{timeStamp}.png'.format(timeStamp=time.strftime("%Y%m%d%H%M", time.localtime(now_time)))
            url = 'http://www.cwb.gov.tw/V7/observe/radar/Data/HD_Radar/' + target_img
            try:
                target_img = os.path.join('static',weather_data_type["typeDir"],target_img)
                request.urlretrieve(url, target_img)
            except:
                now_time -= 60
                continue

            error_list_id = delete_old_cwb_img(server_dir,user_id)

            mark_old_cwb_img(error_list_id)

            #upload new file
            send_obj["server_dir"] = server_dir
            send_obj["file_type"] = weather_data_type["typeId"]
            send_obj["filepath"] = target_img
            send_obj["start_date"] = time.strftime("%Y-%m-%d", time.localtime(time.time()))
            send_obj["end_date"] = time.strftime("%Y-%m-%d", time.localtime(time.time()+86400))
            send_obj["start_time"] = "00:00:00"
            send_obj["end_time"] = "23:59:59"
            send_obj["display_time"] = 5
            send_obj["user_id"] = user_id
            receive_obj = upload_image_insert_db(send_obj)
            try:
                if receive_obj["result"] == "success":
                    filepath = receive_obj["img_system_filepath"]
                    thumbnail_path = "static/thumbnail/"
                    thumbnail_path = os.path.join(thumbnail_path,receive_obj["img_thumbnail_name"])
                    im = Image.open(filepath)
                    im.thumbnail((100,100))
                    im.save(thumbnail_path)
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
        return_msg["error"] = gen_error_msg(e.args[1])
        return return_msg

def google_calendar_text():
    """
    Get google api credential, and grab calendar's upcoming events,
    then check existed or insert into DB
    """
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        credentials = get_credentials()
        if not credentials:
            return_msg["error"] = "No credential file"
            return return_msg
        else:
            events = get_upcoming_events(credentials)
            for calendar, events_value in events.items():
                for event in events_value:
                    check_event_exist_or_insert(event, calendar)
                    sleep(1.5)
            return_msg["result"] = "success"
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

def check_event_exist_or_insert(event, calendar_name=None):
    event_id = event['id']
    with TextDao() as textDao:
        existed = textDao.checkExisted(event_id)
    #display days
    if calendar_name == "Holidays":
        display_days = 3
    elif calendar_name == "Department" or calendar_name == "School":
        display_days = 7
    elif calendar_name == "Activities" or calendar_name == "Speechs":
        display_days = 14
    else:
        display_days = 3

    if existed:
        # event existed
        # do nothing
        return
    else:
        send_msg = {}
        send_msg["server_dir"] = os.path.dirname(__file__)
        send_msg["file_type"] = 6
        if 'date' in event['start'].keys():
            send_msg["start_date"] = datetime.datetime.strftime(datetime.datetime.strptime(event['start']['date'],'%Y-%m-%d') - datetime.timedelta(display_days),'%Y-%m-%d')
            send_msg["end_date"] = event['start']['date']
        elif 'dateTime' in event['start'].keys():
            event_start_date = event['start']['dateTime'].split('T')[0]
            event_start_time = event['start']['dateTime'].split('T')[1][:5]
            event_end_date = event['end']['dateTime'].split('T')[0]
            event_end_time = event['end']['dateTime'].split('T')[1][:5]
            send_msg["start_date"] = datetime.datetime.strftime(datetime.datetime.strptime(event['start']['dateTime'].split('T')[0],'%Y-%m-%d') - datetime.timedelta(display_days),'%Y-%m-%d')
            send_msg["end_date"] = event_start_date
        else:
            print("no date and dateTime")
            return
        send_msg["start_time"] = ""
        send_msg["end_time"] = ""
        send_msg["display_time"] = 10
        send_msg["user_id"] = 1
        send_msg["invisible_title"] = event_id
        receive_msg = upload_text_insert_db(send_msg)
        addition_msg = rule_base_agent(event)
        event_file_path = os.path.join('static','calendar_event','{name}.png'.format(name=event_id))
        description = event.get('description',addition_msg['description'])
        location = event.get('location','')

        if 'dateTime' in event['start'].keys() and event_start_date == event_end_date:
            detailtime = "{start} - {end}".format(start=event_start_time, end=event_end_time)
        else:
            detailtime = ""

        text_file = {   "con" : send_msg["end_date"],
                        "title1" : addition_msg['title1'],
                        "title2" : addition_msg['title2'],
                        "description": description,
                        "location" : location,
                        "detailtime": detailtime,
                        "background_color" : "#984B4B",
                        "event_id" : event_file_path
        }
        with open(receive_msg["text_system_dir"],"w") as fp:
            print(json.dumps(text_file),file=fp)
        add_event_by_qrcode(event)

def add_event_by_qrcode(eventInfo):
    target_dir = os.path.join('static','calendar_event')
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    startTime = '0000'
    endTime = '0000'
    location = ""
    description = ""
    if 'date' in eventInfo['start'] and 'date' in eventInfo['end']:
        startDate = datetime.datetime.strptime(eventInfo['start']['date'], '%Y-%m-%d').strftime('%Y%m%d')
        endDate = datetime.datetime.strptime(eventInfo['end']['date'], '%Y-%m-%d').strftime('%Y%m%d')
    elif 'dateTime' in eventInfo['start'] and 'dateTime' in eventInfo['end']:
        startDate = datetime.datetime.strptime(eventInfo['start']['dateTime'].split('T')[0], '%Y-%m-%d').strftime('%Y%m%d')
        startTime = datetime.datetime.strptime(eventInfo['start']['dateTime'].split('T')[1][:8], '%H:%M:%S').strftime('%H%M%S')
        endDate = datetime.datetime.strptime(eventInfo['end']['dateTime'].split('T')[0], '%Y-%m-%d').strftime('%Y%m%d')
        endTime = datetime.datetime.strptime(eventInfo['end']['dateTime'].split('T')[1][:8], '%H:%M:%S').strftime('%H%M%S')
    if 'location' in eventInfo:
        location = eventInfo['location']
    if 'description' in eventInfo:
        description = eventInfo['description']
    summary = urllib.parse.quote(eventInfo['summary'])
    location = urllib.parse.quote(location)
    description = urllib.parse.quote(description)
    link = 'https://www.google.com/calendar/render?'\
        +'action=TEMPLATE&hl=zh_TW&ctz=Asia/Taipei&sf=true&output=xml'\
        +'&text={summary}&dates={startDate}T{startTime}Z/{endDate}T{endTime}Z&location={location}&details={detail}'\
        .format(summary=summary,startDate=startDate,startTime=startTime,endDate=endDate,endTime=endTime,location=location,detail=description)
    qrcode.make_qrcode_image(link,target_dir,event=eventInfo['id'])

def search_google_drive_folder(service):
    g_sql = "(name='1day' or name='3day' or name='7day' or name='14day')"
    results = service.files().list(
        q="mimeType='application/vnd.google-apps.folder' and trashed=false and " + g_sql, 
        fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    return items

def search_google_drive_file(service):
    """
    Search images which is modified or uploaded in last 12 hours on google drive
    """
    now_time = time.time()
    start_time = time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime(now_time-43200))
    results = service.files().list(
        q="modifiedTime > '{start_time}' and mimeType contains 'image/'".format(start_time=start_time),
        fields="nextPageToken, files(id, name, parents)").execute()
    files = results.get('files', [])
    return files
    
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
            send_obj["filepath"] = 'static/img/' + file_name
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
                    filepath = receive_obj["img_system_filepath"]
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
        try:
            server_dir = json_obj["server_dir"]
            user_id = json_obj["user_id"]
        except:
            return_msg["error"] = "input parameter missing"
            return return_msg

        with DataTypeDao() as dataTypeDao:
            googel_drive_type_id = dataTypeDao.getTypeId(typeName='google_drive_image')

        if googel_drive_type_id:
            json_obj['data_type'] = googel_drive_type_id
        else:
            return_msg["error"] = "No such data_type: {}".format('google_drive_image')
            return return_msg
        
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
        return_msg["error"] = gen_error_msg(e.args[1])
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
        return_msg["error"] = gen_error_msg(e.args[1])
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
        return_msg["error"] = gen_error_msg(e.args[1])
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

def add_news_text(typeId, textFile):
    now_time = time.time()
    send_msg = {}
    send_msg["server_dir"] = os.path.dirname(__file__)
    send_msg["file_type"] = typeId
    send_msg["start_date"] = time.strftime("%Y-%m-%d", time.localtime(now_time))
    send_msg["end_date"] = time.strftime("%Y-%m-%d", time.localtime(now_time))
    send_msg["start_time"] = ""
    send_msg["end_time"] = ""
    send_msg["display_time"] = 5
    send_msg["user_id"] = 1
    send_msg["invisible_title"] = "news"
    receive_msg = upload_text_insert_db(send_msg)
    with open(receive_msg["text_system_dir"],"w") as fp:
        print(json.dumps(textFile),file=fp)

def news2text(text_count):
    try:
        return_msg = {}
        return_msg["result"] = "fail"
        
        #get type id
        with DataTypeDao() as dataTypeDao:
            typeId = dataTypeDao.getTypeId('新聞')
        #get news
        with NewsQRCodeDao() as newsQRCodeDao:
            news = newsQRCodeDao.getNewsByTime(3,text_count*2)
        #mark old news text to expired
        with TextDao() as textDao:
            textDao.expireAllNews()
            
        #pack news to text
        if news is not None:
            text_count = int(len(news)/2)
            for counts in range(text_count):
                with DataTypeDao() as dataTypeDao:
                    type_dir1 = dataTypeDao.getTypeDir(typeId=news[counts][2])
                    type_dir2 = dataTypeDao.getTypeDir(typeId=news[counts+text_count][2])
                    type_name1 = dataTypeDao.getTypeName(typeId=news[counts][2])
                    type_name2 = dataTypeDao.getTypeName(typeId=news[counts+text_count][2])
                QR1 = os.path.join('static',type_dir1,'{name}.png'.format(name=news[counts][1]))
                QR2 = os.path.join('static',type_dir2,'{name}.png'.format(name=news[counts+text_count][1]))
                textFile = {   "text_type" : "news",
                                "forum_name1" : type_name1,
                                "title1" : news[counts][0],
                                "QR1": QR1,
                                "forum_name2" : type_name2,
                                "title2" : news[counts+text_count][0],
                                "QR2": QR2
                                }
                add_news_text(typeId, textFile)
        
        return_msg["result"] = "success"
        return return_msg
    except Exception as e:
        return_msg["error"] = str(e)
        return return_msg

def auto_text_generator():
    try:
        return_msg = {}
        return_msg["result"] = "fail"

        with DataTypeDao() as dataTypeDao:
            existed = dataTypeDao.checkTypeExisted("文字")
        if not existed:
            create_data_type("文字")

        #generate news text from db news_QR_code table
        with DataTypeDao() as dataTypeDao:
            existed = dataTypeDao.checkTypeExisted("新聞")
        if not existed:
            create_data_type("新聞","文字")
        
        receive_msg = news2text(10)
        if receive_msg["result"] == "fail":
            return receive_msg
        
        return_msg["result"] = "success"
        return return_msg
    except Exception as e:
        return_msg["error"] = str(e)
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

def set_system_log(json_obj):
    """
    Print error message and write to log file
    """
    return_msg = {}
    return_msg["result"] = "fail"
    file_name = "static/log/impossible_error.txt"

    if "result" not in json_obj:
        return_msg["error"] = "set_system_log failed no `result` in input parameter"
        return return_msg

    if json_obj["result"] == "fail":
        if "error" not in json_obj:
            return_msg["result"] = "success"
            return return_msg

        print("#error : " + json_obj["error"])
        mode = "a" if os.path.isfile(file_name) else "w"
        with open(file_name,mode) as fp:
            fp.write("{timestamp} fail: {err_msg}\n".format(
                timestamp=time.time(),err_msg=json_obj["error"])
            )

    return_msg["result"] = "success"
    return return_msg
        
def do_expire_data_check():
    receive_obj = expire_data_check()
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

def do_auto_text_generator():
    receive_obj = auto_text_generator()
    if receive_obj["result"] == "success":
        "DO NOTHING"
    else :
        receive_obj["error"] = "auto_text_generator : " + receive_obj["error"]
        set_system_log(receive_obj)

def fork_time_management(raw_time,now_time,alarm,worker,fail_time,success_time):
    if raw_time >= alarm:
        fork_failed = worker.do(timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time))
        if fork_failed:
            alarm += fail_time
        else:
            alarm += success_time
    return alarm

board_py_dir = ""
shutdown = 0
max_db_log = 100
min_db_activity = 10

def main():
    arrange_mode_change = 0
    arrange_sn = 0
    arrange_mode = 0
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
    alarm_check_remain_schedule = raw_time
    alarm_add_schedule = 1960380833.0
    alarm_crawler_cwb_img = raw_time + 7.0
    alarm_google_calendar_text = raw_time + 5.0
    alarm_crawler_google_drive_img = raw_time + 13.0
    alarm_crawler_functions = raw_time + 15.0
    alarm_auto_text_generator = raw_time + 97.0

    check_expire_data_worker = Worker(job=do_expire_data_check,name='Check expired data')
    set_schedule_log_worker = Worker(job=do_set_schedule_log,name='Set schedule log')
    cwb_crawler_worker = Worker(job=do_cwb_crawler,name='Crawler for cwb image')
    google_calendar_worker = Worker(job=do_google_calendar,name='Grab Google calendar event')
    google_drive_worker = Worker(job=do_google_drive,name='Grab Google drive image')
    crawler_schedule_worker = Worker(job=do_crawler_schedule,name='Crawler for news')
    auto_text_generator_worker = Worker(job=do_auto_text_generator,name='Generator news text')

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
        alarm_expire_data_check = fork_time_management(raw_time,now_time,
            alarm_expire_data_check,check_expire_data_worker,3.0,1800.0)
        #set_schedule_log
        alarm_set_schedule_log = fork_time_management(raw_time,now_time,
            alarm_set_schedule_log,set_schedule_log_worker,3.0,1800.0)

        if raw_time >= alarm_check_remain_schedule:
            print("[{timestamp}] Check remain schedule count".format(timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',now_time)))

            ret = mark_now_activity()
            if "error" in ret:
                set_system_log(ret)

            with ScheduleDao() as scheduleDao:
                remain_schedules = scheduleDao.countUndisplaySchedule()
            if remain_schedules < min_db_activity:
                alarm_add_schedule = raw_time

            alarm_check_remain_schedule += 3

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
            except Exception as e:
                receive_obj["result"] = "fail"
                receive_obj["error"] = "fork3 error"
                set_system_log(receive_obj)
                arrange_mode_change = 0
                alarm_add_schedule = raw_time + 3
        
        #crawl cwb radar image
        alarm_crawler_cwb_img = fork_time_management(raw_time,now_time,
            alarm_crawler_cwb_img,cwb_crawler_worker,600.0,3600.0)
        #google calendar add to text data
        alarm_google_calendar_text = fork_time_management(raw_time,now_time,
            alarm_google_calendar_text,google_calendar_worker,10.0,43200.0)
        #google drive add to text data
        alarm_crawler_google_drive_img = fork_time_management(raw_time,now_time,
            alarm_crawler_google_drive_img,google_drive_worker,600.0,3600.0)
        #crawler
        alarm_crawler_functions = fork_time_management(raw_time,now_time,
            alarm_crawler_functions,crawler_schedule_worker,600.0,3600.0)
        #auto make news text
        alarm_auto_text_generator = fork_time_management(raw_time,now_time,
            alarm_auto_text_generator,auto_text_generator_worker,600.0,3600.0)

        #delay
        sleep(0.1)
    print("arrange_schedule shutdown")
    sleep(10)
    return 1

if __name__ == "__main__":
    main()


