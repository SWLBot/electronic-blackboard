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

    def getUserPassword(self,userId=None,userName=None):
        sql = 'SELECT user_password FROM user WHERE '
        if userId:
            sql += 'user_id = "{userId}"'.format(userId=userId)
        elif userName:
            sql += 'user_name = "{userName}"'.format(userName=userName)
        return self.queryOneValue(sql)

    def checkUserExisted(self,userName):
        sql = 'SELECT count(*) FROM user ' \
            + 'WHERE user_name="{userName}"'.format(userName=userName)
        return self.queryOneValue(sql)

    def createNewUser(self,userName,userPassword):
        #TODO modify this function in the future
        cursor = self.db.cursor
        sql = 'INSERT INTO user (user_name,user_password) VALUES (%s,%s)'
        data = (userName,userPassword)
        ret = cursor.execute(sql,data)
        self.db.db.commit()

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

    def countUsedSchedule(self):
        sql = 'SELECT count(sche_sn) FROM schedule WHERE sche_is_used=1'
        ret = self.db.query(sql)
        if len(ret):
            return int(ret[0][0])
        else:
            #TODO raise exception
            return None

    def checkToUpdateUndecidedSchedule(self):
        sql = "SELECT sche_sn FROM schedule WHERE sche_id='sche0undecided' ORDER BY sche_sn ASC LIMIT 1"
        return self.queryOneValue(sql)

    def findTextActivitySchedule(self,conditionAssigned,orderById,arrangeMode,arrangeCondition=None):
        if conditionAssigned:
            type_condition = ''
            for idx,type_id in enumerate(arrangeCondition):
                if idx == 0:
                    type_condition += " type_id={type_id} ".format(type_id=type_id)
                else:
                    type_condition += " or type_id={type_id} ".format(type_id=type_id)
        if arrangeMode in range(6):
            sql = "SELECT text_id, text_display_time FROM text_data" \
                +" WHERE text_is_delete=0 and text_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time))"
            if conditionAssigned:
                sql += " and ({type_condition}) ".format(type_condition=type_condition)
            if orderById:
                sql += " ORDER BY text_id ASC"
        elif arrangeMode == 6:
            sql = "SELECT a0.text_id, a0.text_display_time, a1.type_weight FROM " \
                +" (SELECT text_id, type_id, text_display_time FROM text_data WHERE " \
                +" text_is_delete=0 and text_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time))) AS a0 "\
                +" LEFT JOIN (SELECT type_id, type_weight FROM data_type ) AS a1 "\
                +" ON a0.type_id=a1.type_id ORDER BY a1.type_weight ASC"
        elif arrangeMode == 7:
            sql = "SELECT a0.text_id, a0.text_display_time, a1.type_weight FROM " \
                +" (SELECT text_id, type_id, text_display_time FROM text_data WHERE "\
                +" ({type_condition})".format(type_condition=type_condition)\
                +" and text_is_delete=0 and text_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time))) AS a0 "\
                +" LEFT JOIN (SELECT type_id, type_weight FROM data_type WHERE "\
                +" ({type_condition})".format(type_condition=type_condition)\
                +" ) AS a1 ON a0.type_id=a1.type_id ORDER BY a1.type_weight ASC"
        ret = self.db.query(sql)
        return ret

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

    def checkExpired(self,imgId):
        sql = 'SELECT count(*) FROM image_data WHERE img_id="{imgId}"'.format(imgId=imgId)\
                +' and img_is_delete=0 and img_is_expire=0 '\
                +' and (TO_DAYS(NOW()) between TO_DAYS(img_start_date) and TO_DAYS(img_end_date)) '\
                +' and (TIME_TO_SEC(DATE_FORMAT(NOW(), "%H:%i:%s")) between TIME_TO_SEC(img_start_time) and TIME_TO_SEC(img_end_time)) '
        ret = self.db.query(sql)
        return True if ret[0][0] == 0 else False

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

    def addLikeCount(self,targetId):
        sql = 'UPDATE image_data SET img_like_count=img_like_count+1 WHERE img_id="{targetId}"'.format(targetId=str(targetId))
        ret = self.db.cmd(sql)

class TextDao(DefaultDao):
    def getExpiredIds(self):
        sql = ("SELECT text_id FROM text_data "\
                +"WHERE text_is_delete=0 and text_is_expire=0 and ( TO_DAYS(NOW())>TO_DAYS(text_end_date) "\
                +"or (TO_DAYS(NOW())=TO_DAYS(text_end_date) and TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s'))>TIME_TO_SEC(text_end_time)))") 
        expiredIds = self.db.query(sql)
        return expiredIds

    def checkExpired(self,textId):
        sql = 'SELECT count(*) FROM text_data WHERE text_id="{textId}"'.format(textId=textId)\
                +' and text_is_delete=0 and text_is_expire=0 '\
                +' and (TO_DAYS(NOW()) between TO_DAYS(text_start_date) and TO_DAYS(text_end_date)) '\
                +' and (TIME_TO_SEC(DATE_FORMAT(NOW(), "%H:%i:%s")) between TIME_TO_SEC(text_start_time) and TIME_TO_SEC(text_end_time))'
        ret = self.db.query(sql)
        return True if ret[0][0] == 0 else False

    def getFileInfo(self,textId):
        sql = 'SELECT type_id, text_system_name FROM text_data WHERE text_id="{textId}"'.format(textId=textId)
        ret = self.db.query(sql)
        if len(ret) and isinstance(ret[0],tuple) and len(ret[0]) == 2:
            fileInfo = dict(typeId=ret[0][0],systemFileName=ret[0][1])
            return fileInfo
        else:
            #TODO raise exception
            return None

    def markExpired(self,textId):
        sql = 'UPDATE text_data SET text_is_expire=1 WHERE text_id="{textId}"'.format(textId=textId)
        self.db.cmd(sql)

    def addLikeCount(self,targetId):
        sql = 'UPDATE text_data SET text_like_count=text_like_count+1 WHERE text_id="{targetId}"'.format(targetId=str(targetId))
        self.db.cmd(sql)

    def getTextMeta(self,textId):
        sql = 'select * from text_data where text_is_delete = 0 and text_id = "{textId}"'.format(textId=textId)
        ret = self.db.query(sql)
        return ret[0]

class UserPreferDao(DefaultDao):
    def generateNewId(self):
        sql ='SELECT pref_id FROM user_prefer ORDER BY pref_set_time DESC LIMIT 1'
        res = self.db.query(sql)
        if len(res):
            return "pref{0:010d}".format(int(res[0][0][4:]) + 1)
        else:
            return "pref0000000001"

    def getNowUserPrefer(self,dataType,UserId):
        sql = 'SELECT pref_data_type_{dataType}'.format(dataType=dataType) \
            + ' FROM user_prefer WHERE pref_is_delete=0 and user_id="{UserId}"'.format(UserId=str(UserId)) \
            + ' ORDER BY pref_set_time DESC LIMIT 1'
        res = self.db.query(sql)
        if len(res):
            return res
        else:
            #TODO raise exception
            return None

    def insertUserPrefer(self,prefId,UserId,prefStr):
        sql = 'INSERT INTO user_prefer' \
            +'(pref_id,user_id,pref_data_type_01,pref_data_type_02,pref_data_type_03,pref_data_type_04,pref_data_type_05) VALUES (' \
            +'{prefId},{useId},{prefStr},{prefStr},{prefStr},{prefStr},{prefStr})'\
            .format(prefId=prefId,userId=str(userId),prefStr=prefStr)
        db.cmd(sql)

class DataTypeDao(DefaultDao):
    def getTypeDir(self,typeId):
        sql = 'SELECT type_dir FROM data_type WHERE type_id={typeId}'.format(typeId=typeId)
        return self.queryOneValue(sql)

    def getTypeId(self,typeName):
        sql = 'SELECT type_id FROM data_type WHERE type_name="{typeName}"'.format(typeName=typeName)
        return self.queryOneValue(sql)

    def checkTypeExisted(self,typeName):
        sql = 'SELECT COUNT(*) FROM data_type WHERE type_name="{typeName}"'.format(typeName=typeName)
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

class FortuneDao(DefaultDao):
    def getFortune(self,today,constellation):
        sql = 'SELECT overall, love, career, wealth FROM fortune ' \
            + 'WHERE fortune_date = "{today}" AND constellation = "{constellation}"' \
            .format(today=today,constellation=constellation)
        ret = self.db.query(sql)
        if len(ret):
            return ret
        else:
            #TODO check need to raise exception or not
            return None

class DatabaseDao(DefaultDao):
    def checkTableExisted(self,tableName):
        sql = 'SELECT count(*) FROM information_schema.tables '\
                +'WHERE table_schema = "broadcast" '\
                +'AND table_name ="{tableName}"'.format(tableName=tableName)
        existed = self.queryOneValue(sql)
        return True if existed else False
class NewsQRCodeDao(DefaultDao):
    def getNews(self,preferStr):
        sql = 'SELECT * FROM ' \
            + '(SELECT title, serial_number,data_type ' \
            + 'FROM news_QR_code where is_delete=0 and data_type IN {preferStr} '.format(preferStr=preferStr) \
            + 'ORDER BY upload_time DESC LIMIT 10) as data ORDER BY RAND() LIMIT 2'
        ret = self.db.query(sql)
        if len(ret):
            return ret
        else:
            #TODO check need to raise exception or not
            return None

    def insertNews(self,dataType,serialNumber,title):
        sql = "INSERT INTO news_QR_code " \
            +" (`data_type`, `serial_number`, `title`)" \
            +" VALUES ({news_data_type},'{news_serial_number}','{news_title}')".format(
            news_data_type=dataType,news_serial_number=serialNumber,news_title=title)
        self.db.cmd(sql)
