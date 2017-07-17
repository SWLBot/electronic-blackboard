from mysql import *

class DefaultDao():
    def __init__(self):
        self.db = mysql()
        self.db.connect()

    def __del__(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()

    def queryOneValue(self,sql):
        ret = self.db.query(sql)
        if len(ret):
            return ret[0][0]
        else:
            #TODO raise exception
            return None

class UserDao(DefaultDao):
    def getUserId(self,userName=None,bluetoothId=None):
        sql = 'SELECT user_id FROM user WHERE '
        if userName:
            sql += 'user_name = "{userName}"'.format(userName=userName)
        elif bluetoothId:
            sql += 'user_bluetooth_id = "{bluetoothId}"'.format(bluetoothId=bluetoothId)

        return self.queryOneValue(sql)

    def getUserLevel(self,userId):
        sql = 'SELECT user_level FROM user WHERE user_id  = {userId}'.format(userId=userId)
        return self.queryOneValue(sql)

    def getUserBirthday(self,userId):
        sql = 'select user_birthday from user where user_id = {userId}'.format(userId=userId)
        return self.queryOneValue(sql)

    def checkBluetoothIdUsed(self,bluetoothId):
        sql = 'SELECT count(*) FROM user WHERE user_bluetooth_id="{bluetoothId}"'.format(bluetoothId=bluetoothId)
        return self.queryOneValue(sql)

    def getUserNickname(self,userId):
        sql = 'select user_nickname from user where user_id = {userId}'.format(userId=userId)
        return self.queryOneValue(sql)

class ScheduleDao(DefaultDao):
    def getDisplayingSchedule(self):
        sql = 'SELECT sche_sn FROM schedule WHERE sche_is_used=0 ORDER BY sche_sn ASC LIMIT 1'
        return self.queryOneValue(sql)

    def markExpiredSchedule(self,scheSn=None,targetId=None):
        if scheSn:
            sql = 'UPDATE schedule SET sche_is_used=1 WHERE sche_sn={scheSn}'.format(scheSn=scheSn)
        elif targetId:
            sql = 'UPDATE schedule SET sche_is_used=1 '\
                    +'WHERE sche_is_used=0 and sche_is_artificial_edit=0 and sche_target_id="{targetId}"'.format(targetId=targetId)
        self.db.cmd(sql)

    def getNextSchedule(self):
        sql = 'SELECT sche_id, sche_target_id, sche_display_time, sche_is_artificial_edit, sche_sn '\
                +"FROM schedule WHERE sche_is_used=0 ORDER BY sche_sn ASC LIMIT 1"
        ret = self.db.query(sql)
        if len(ret):
            scheduleInfo = {}
            scheduleInfo['schedule_id'] = ret[0][0]
            scheduleInfo['sche_target_id'] = ret[0][1]
            scheduleInfo['display_time'] = ret[0][2]
            scheduleInfo['no_need_check_time'] = ret[0][3]
            scheduleInfo['target_sn'] = ret[0][4]
            return scheduleInfo
        else:
            #TODO raise exception
            return None

    def countUndisplaySchedule(self):
        sql = 'SELECT count(sche_sn) FROM schedule WHERE sche_is_used=0'
        return self.queryOneValue(sql)

    def updateEditSchedule(self,targetId,displayTime,modeSn,scheSn):
        sql = "UPDATE schedule SET sche_target_id='{targetId}', ".format(targetId=targetId)\
            +"sche_display_time={displayTime}, ".format(displayTime=displayTime)\
            +"sche_arrange_time=now(), "\
            +"sche_arrange_mode={modeSn}, ".format(modeSn=modeSn)\
            +"sche_is_used=0, sche_is_artificial_edit=0 "\
            +" WHERE sche_sn={scheSn}".format(scheSn=scheSn)
        self.db.cmd(sql)

    def cleanSchedule(self):
        sql = 'DELETE FROM schedule WHERE sche_is_used=0'
        self.db.cmd(sql)

class ImageDao(DefaultDao):
    def getExpiredIds(self):
        sql = 'SELECT img_id FROM image_data '\
                +'WHERE img_is_delete=0 and img_is_expire=0 and (TO_DAYS(NOW())>TO_DAYS(img_end_date) '\
                +'or (TO_DAYS(NOW())=TO_DAYS(img_end_date) and TIME_TO_SEC(DATE_FORMAT(NOW(), "%H:%i:%s"))>TIME_TO_SEC(img_end_time)))'
        Ids = self.db.query(sql)
        return Ids

    def markExpired(self,imgId):
        sql = 'UPDATE image_data SET img_is_expire=1 WHERE img_id="{imgId}"'.format(imgId=imgId)
        self.db.cmd(sql)
    def getImgData(self,imgId):
        sql = 'select * from image_data where img_is_delete = 0 and img_id = "{imgId}"'.format(imgId=imgId)
        ret = self.db.query(sql)
        if len(ret):
            return ret[0]
        else:
            #TODO raise exception
            return None

    def getFileInfo(self,imgId):
        sql = 'SELECT type_id, img_system_name FROM image_data WHERE img_id="{imgId}"'.format(imgId=imgId)
        ret = self.db.query(sql)
        if len(ret) and isinstance(ret[0],tuple) and len(ret[0]) == 2:
            fileInfo = dict(typeId=ret[0][0],systemFileName=ret[0][1])
            return fileInfo
        else:
            #TODO raise exception
            return None

class TextDao(DefaultDao):
    def getExpiredIds(self):
        sql = ("SELECT text_id FROM text_data "\
                +"WHERE text_is_delete=0 and text_is_expire=0 and ( TO_DAYS(NOW())>TO_DAYS(text_end_date) "\
                +"or (TO_DAYS(NOW())=TO_DAYS(text_end_date) and TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s'))>TIME_TO_SEC(text_end_time)))") 
        expiredIds = self.db.query(sql)
        return expiredIds

    def getFileInfo(self,textId):
        sql = 'SELECT type_id, text_system_name FROM text_data WHERE text_id="{textId}"'.format(textId=textId)
        ret = self.db.query(sql)
        if len(ret) and isinstance(ret[0],tuple) and len(ret[0]) == 2:
            fileInfo = dict(typeId=ret[0][0],systemFileName=ret[0][1])
            return fileInfo
        else:
            #TODO raise exception
            return None

class UserPreferDao(DefaultDao):
    def generateNewId(self):
        sql ='SELECT pref_id FROM user_prefer ORDER BY pref_set_time DESC LIMIT 1'
        res = self.db.query(sql)
        if len(res):
            return "pref{0:010d}".format(int(res[0][0][4:]) + 1)
        else:
            return "pref0000000001"

class DataTypeDao(DefaultDao):
    def getTypeDir(self,typeId):
        sql = 'SELECT type_dir FROM data_type WHERE type_id={typeId}'.format(typeId=typeId)
        return self.queryOneValue(sql)

    def getTypeId(self,typeName):
        sql = 'SELECT type_id FROM data_type WHERE type_name="{typeName}"'.format(typeName=typeName)
        return self.queryOneValue(sql)

class ArrangeModeDao(DefaultDao):
    def getArrangeMode(self):
        sql = 'SELECT armd_sn, armd_mode, armd_condition FROM arrange_mode WHERE armd_is_delete=0 and armd_is_expire=0 and '\
                +'(TIME_TO_SEC(DATE_FORMAT(NOW(), "%H:%i:%s")) between TIME_TO_SEC(armd_start_time) and TIME_TO_SEC(armd_end_time))'\
                +' ORDER BY armd_set_time DESC LIMIT 1'
        ret = self.db.query(sql)
        if len(ret):
            arrangeMode = {}
            arrangeMode['arrange_sn'] = int(ret[0][0])
            arrangeMode['arrange_mode'] = int(ret[0][1])
            arrangeMode['condition'] = []

            if len(ret[0]) > 2 and ret[0][2] is not None:
                conditionStr = ret[0][2].split(' ')
                for condition in conditionStr:
                    arrangeMode.append(int(condition))

            return arrangeMode
        else:
            #TODO check need to raise exception or not
            return None

