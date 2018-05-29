from mysql import *
from display_object import *

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

class DataManipulateDao(DefaultDao):
    #TODO handle if derived class not assign dataName
    def addDisplayCount(self,targetId):
        sql = 'UPDATE {tableName} SET {dataName}_display_count={dataName}_display_count+1 WHERE {dataName}_id="{targetId}"'.format(
                dataName=self.dataName,targetId=targetId,tableName=self.tableName)
        self.db.cmd(sql)

    def markExpired(self,target=None):
        target_list = None
        if not target:
            sql = 'SELECT {dataName}_id FROM {tableName} '\
                +'WHERE {dataName}_is_delete=0 and {dataName}_is_expire=0 and (TO_DAYS(NOW())>TO_DAYS({dataName}_end_date) '\
                +'or (TO_DAYS(NOW())=TO_DAYS({dataName}_end_date) and TIME_TO_SEC(DATE_FORMAT(NOW(), "%H:%i:%s"))>TIME_TO_SEC({dataName}_end_time)))'
            sql = sql.format(dataName=self.dataName,tableName=self.tableName)
            target_list = to_list(self.db.query(sql))
        elif not isinstance(target,list):
            target_list = [target]
        else:
            target_list = target

        sql_template = 'UPDATE {tableName} SET {dataName}_is_expire=1 WHERE {dataName}_id="{targetId}"'
        for targetId in target_list:
            sql = sql_template.format(dataName=self.dataName,targetId=targetId,tableName=self.tableName)
            self.db.cmd(sql)

        return target_list

    def markDeleted(self,targetId,userId):
        sql = 'UPDATE {tableName} SET {dataName}_is_delete=1,{dataName}_last_edit_user_id={userId} WHERE {dataName}_id="{targetId}"'.format(
                dataName=self.dataName,targetId=targetId,userId=userId,tableName=self.tableName)
        self.db.cmd(sql)

    def findActivities(self,conditionAssigned,orderById,arrangeMode,arrangeCondition=None):
        if conditionAssigned:
            type_condition = ''
            for idx,type_id in enumerate(arrangeCondition):
                if idx == 0:
                    type_condition += " type_id={type_id} ".format(type_id=type_id)
                else:
                    type_condition += " or type_id={type_id} ".format(type_id=type_id)
        if arrangeMode in range(6):
            sql = "SELECT {dataName}_id, {dataName}_display_time," \
                +" {dataName}_end_date,{dataName}_end_time FROM {tableName}" \
                +" WHERE {dataName}_is_delete=0 and {dataName}_is_expire=0 "\
                +" and (TO_DAYS(NOW()) between TO_DAYS({dataName}_start_date) and TO_DAYS({dataName}_end_date)) " \
                +" and (TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC({dataName}_start_time) and TIME_TO_SEC({dataName}_end_time))"
            if conditionAssigned:
                sql += " and ({type_condition}) ".format(type_condition=type_condition)
            if orderById:
                sql += " ORDER BY {dataName}_id ASC".format(dataName=self.dataName)

        sql = sql.format(dataName=self.dataName,tableName=self.tableName)
        ret = self.db.query(sql)
        return ret

    def generateNewId(self):
        sql = 'SELECT {dataName}_id FROM {tableName} ORDER BY {dataName}_upload_time DESC, {dataName}_id DESC LIMIT 1'.format(
                dataName=self.dataName,tableName=self.tableName)
        Id = self.db.query(sql)
        if len(Id):
            return "{prefix}{num:010d}".format(prefix=self.prefix,num=(int(Id[0][0][4:]) + 1))
        else:
            return "{prefix}0000000001".format(prefix=self.prefix)
    
    def updateEditedData(self,display_object):
        sql = 'UPDATE {tableName} '
        update = 'SET type_id={display_object.type_id}, {dataName}_start_date="{display_object.start_date}", ' \
            + '{dataName}_end_date="{display_object.end_date}", {dataName}_start_time="{display_object.start_time}", ' \
            + '{dataName}_end_time="{display_object.end_time}", {dataName}_display_time={display_object.display_time}, ' \
            + '{dataName}_last_edit_user_id="{display_object.user_id}"'
        if self.tableName == "text_data":
            update += ', text_invisible_title="{display_object.invisible_title}"'
        sql += update
        sql += ' WHERE {dataName}_id="{display_object.id}"'
        sql = sql.format(tableName=self.tableName,dataName=self.dataName,display_object=display_object)
        self.db.cmd(sql)

    def getIdSysName(self,Id):
        sql = 'SELECT user_id, type_id, {dataName}_system_name, {dataName}_like_count FROM {tableName} WHERE {dataName}_id="{Id}"'.format(
                tableName=self.tableName,dataName=self.dataName,Id=Id)
        ret = self.db.query(sql)
        if len(ret) and len(ret[0]) == 4:
            info = dict(userId=ret[0][0],typeId=ret[0][1],systemName=ret[0][2],likeCount=ret[0][3])
            return info
        else:
            #TODO raise exception
            return None

    def insertData(self,display_object):
        sql = 'INSERT INTO {tableName} ' \
            + '({dataName}_id, type_id, {dataName}_system_name, ' \
            + '{column}, {dataName}_start_date, ' \
            + '{dataName}_end_date, {dataName}_start_time, {dataName}_end_time, ' \
            + '{dataName}_display_time, user_id)' \
            + ' VALUES ' \
            + '("{display_object.id}", {display_object.type_id}, "{display_object.system_name}", {value}, "{display_object.start_date}",' \
            + ' "{display_object.end_date}", "{display_object.start_time}", "{display_object.end_time}", {display_object.display_time}, {display_object.user_id})'
        if self.tableName == "image_data":
            column = "img_thumbnail_name, img_file_name"
            value = '"{display_image.thumbnail_name}", "{display_image.file_name}"'.format(display_image=display_object)
        elif self.tableName == "text_data":
            column = "text_invisible_title"
            value = '"{display_text.invisible_title}"'.format(display_text=display_object)
        
        sql = sql.format(column=column, value=value, dataName=self.dataName, tableName=self.tableName, display_object=display_object)
        self.db.cmd(sql)

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

    def updateUserData(self,userInfo):
        sql = "UPDATE user SET "
        if "bluetooth_id" in userInfo and userInfo["bluetooth_id"] is not None:
            sql = sql + 'user_bluetooth_id="{id}", '.format(id=str(userInfo["bluetooth_id"]))
        if "nickName" in userInfo and userInfo["nickName"] is not None:
            sql = sql + 'user_nickname="{nickname}", '.format(nickname=str(userInfo["nickName"]))
        if "birthday" in userInfo and userInfo["birthday"] is not None:
            sql = sql + 'user_birthday="{birthday}", '.format(birthday=str(userInfo["birthday"]))
        if "occupation" in userInfo and userInfo["occupation"] is not None:
            sql = sql + "user_profession="
            if userInfo["occupation"]=="bachelor":
                sql = sql + "1, "
            elif userInfo["occupation"]=="masterDr":
                sql = sql + "2, "
            elif userInfo["occupation"]=="faculty":
                sql = sql + "3, "
            else:
                sql = sql + "0, "
        sql = sql + 'user_level=50 WHERE user_name="{userName}"'.format(userName=str(userInfo["bluetooth_id"]))
        self.db.cmd(sql)

    def updatePassword(self,hashedKey,userId):
        sql = 'UPDATE user SET user_password="{hashedKey}" WHERE user_id={userId}'.format(
                hashedKey=hashedKey,userId=userId)
        self.db.cmd(sql)

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

    def getUsedSchedule(self,limitCount):
        sql = "SELECT * FROM schedule WHERE sche_is_used=1 ORDER BY sche_sn ASC LIMIT {limitCount}".format(
            limitCount=limitCount)
        return self.db.query(sql)

    def cleanSchedule(self,scheSn=None):
        if scheSn:
            sql = "DELETE FROM schedule WHERE sche_sn={scheSn}".format(scheSn=scheSn)
        else:
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

    def getUndecidedScheduleSn(self):
        sql = "SELECT sche_sn FROM schedule WHERE sche_id='sche0undecided' ORDER BY sche_sn ASC LIMIT 1"
        return self.queryOneValue(sql)

    def getEditScheSn(self,scheSn):
        sql = 'SELECT sche_sn FROM schedule WHERE sche_sn={scheSn} and sche_id != "sche0undecided"'.format(scheSn=scheSn)
        return self.queryOneValue(sql)

    def insertUndecidedSchedule(self,targetId,displayTime,arrangeModeSn):
        sql = "INSERT INTO schedule (sche_id, sche_target_id, sche_display_time, sche_arrange_mode)"\
            +" VALUES ('sche0undecided','{targetId}',{displayTime},{arrangeModeSn})".format(
            targetId=targetId,displayTime=displayTime,arrangeModeSn=arrangeModeSn)
        self.db.cmd(sql)

    def updateNewIdSchedule(self,scheNewId,scheSn):
        sql = "UPDATE schedule SET sche_id='{scheId}' WHERE sche_sn={scheSn}".format(scheId=scheNewId,scheSn=scheSn)
        self.db.cmd(sql)
    
    def getDisplayTime(self,scheSn):
        sql = "SELECT sche_display_time FROM schedule WHERE sche_sn={scheSn}".format(scheSn=scheSn)
        return self.queryOneValue(sql)

class ImageDao(DataManipulateDao):
    dataName = 'img'
    tableName = 'image_data'
    prefix = 'imge'
    def checkExisted(self,typeId,fileName):
        sql = 'SELECT COUNT(*) FROM image_data WHERE img_is_expire=0 and img_is_delete=0 '\
                +'and type_id={typeId} and img_file_name="{fileName}"'.format(typeId=typeId,fileName=fileName)
        return self.queryOneValue(sql)

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
            raw_img = ret[0]
            img = dict(img_id=raw_img[0],
                        type_id=raw_img[1],
                        img_file_name=raw_img[2],
                        img_thumbnail_name=raw_img[3],
                        img_upload_name=raw_img[4],
                        img_upload_time=raw_img[5],
                        img_start_date=raw_img[6],
                        img_end_date=raw_img[7],
                        img_start_time=raw_img[8],
                        img_end_time=raw_img[9],
                        img_display_count=raw_img[10],
                        img_display_time=raw_img[11])
            return img
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
        self.db.cmd(sql)

    def getCwbImgIds(self):
        sql = "SELECT img_id FROM image_data WHERE img_is_delete=0 and img_file_name like 'CV1_TW_3600_%'"
        Ids = to_list(self.db.query(sql))
        return Ids

    def getDisplayImgs(self,userId=None):
        sql = "SELECT img_id, img_upload_time, img_system_name, img_start_time, img_end_time, img_start_date, img_end_date, type_id, img_thumbnail_name, img_display_time, img_display_count " \
                + "FROM image_data WHERE img_is_delete=0 AND img_is_expire=0"
        if userId:
            sql += " AND user_id={userId}".format(userId=userId)
        sql += " ORDER BY img_id DESC"
        ret = self.db.query(sql)
        return ret

class TextDao(DataManipulateDao):
    dataName = 'text'
    tableName = 'text_data'
    prefix = 'text'
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

    def checkExisted(self,eventId):
        sql = 'SELECT COUNT(*) from text_data where text_invisible_title="{eventId}"'.format(
            eventId=eventId)
        return self.queryOneValue(sql)

    def addLikeCount(self,targetId):
        sql = 'UPDATE text_data SET text_like_count=text_like_count+1 WHERE text_id="{targetId}"'.format(targetId=str(targetId))
        self.db.cmd(sql)

    def getTextMeta(self,textId):
        sql = 'select * from text_data where text_is_delete = 0 and text_id = "{textId}"'.format(textId=textId)
        ret = self.db.query(sql)
        return ret[0]

    def getDisplayTexts(self,userId=None):
        sql = "SELECT text_id, type_id, text_upload_time, text_start_date, text_end_date, text_start_time, text_end_time, text_display_time, text_display_count " \
                + "FROM text_data WHERE text_is_delete=0 AND text_is_expire=0"
        if userId:
            sql += " AND user_id={userId}".format(userId=userId)
        sql += " ORDER BY text_id DESC"
        ret = self.db.query(sql)
        return ret

    def expireAllNews(self):
        sql = 'UPDATE text_data SET text_is_expire=1 WHERE text_is_expire=0 and text_invisible_title="news"'
        self.db.cmd(sql)

class UserPreferDao(DefaultDao):
    def generateNewId(self):
        sql ='SELECT pref_id FROM user_prefer ORDER BY pref_set_time DESC, pref_id DESC LIMIT 1'
        res = self.db.query(sql)
        if len(res):
            return "pref{0:010d}".format(int(res[0][0][4:]) + 1)
        else:
            return "pref0000000001"

    def getNowUserPrefer(self,dataType,UserId):
        sql = 'SELECT pref_data_type_{dataType}'.format(dataType=dataType) \
            + ' FROM user_prefer WHERE pref_is_delete=0 and user_id="{UserId}"'.format(UserId=str(UserId)) \
            + ' ORDER BY pref_set_time DESC LIMIT 1'
        return self.queryOneValue(sql)

    def insertUserPrefer(self,prefId,userId,prefStr):
        sql = 'INSERT INTO user_prefer' \
            +'(pref_id,user_id,pref_data_type_01,pref_data_type_02,pref_data_type_03,pref_data_type_04,pref_data_type_05) VALUES (' \
            +'"{prefId}",{userId},"{prefStr}","{prefStr}","{prefStr}","{prefStr}","{prefStr}")'\
            .format(prefId=prefId,userId=str(userId),prefStr=prefStr)
        self.db.cmd(sql)

class DataTypeDao(DefaultDao):
    def getTypeDir(self,typeId=None,typeName=None):
        sql = 'SELECT type_dir FROM data_type WHERE {condition}'
        if typeId:
            condition = 'type_id={typeId}'.format(typeId=typeId)
        elif typeName:
            condition = 'type_name={typeName}'.format(typeName=typeName)
        sql = sql.format(condition=condition)
        return self.queryOneValue(sql)

    def getTypeName(self,typeId):
        sql = 'SELECT type_name FROM data_type WHERE type_id={typeId}'.format(typeId=typeId)
        return self.queryOneValue(sql)

    def getTypeId(self,typeName):
        sql = 'SELECT type_id FROM data_type WHERE type_name="{typeName}"'.format(typeName=typeName)
        return self.queryOneValue(sql)

    def checkTypeExisted(self,typeName):
        sql = 'SELECT COUNT(*) FROM data_type WHERE type_name="{typeName}"'.format(typeName=typeName)
        return self.queryOneValue(sql)

    def insertType(self,typeName):
        sql = 'INSERT INTO data_type (type_name,type_dir) VALUES ("{typeName}","{typeName}/")'.format(typeName=typeName)
        self.db.cmd(sql)

    def getTypeData(self):
        sql = 'select type_id,type_name,type_dir from data_type'
        ret = self.db.query(sql)
        if len(ret):
            return ret
        else:
            #TODO check need to raise exception or not
            return None

    def getDisplayDataType(self,info):
        if info["current_type_id"] :
            sql = 'SELECT * FROM data_type WHERE type_id ="{typeId}"'.format(typeId=str(info["current_type_id"]))
        elif info["current_type_name"] :
            sql = 'SELECT * FROM data_type WHERE type_name ="{typeName}"'.format(typeName=info["current_type_name"])
        elif info["current_type_dir"] :
            sql = 'SELECT * FROM data_type WHERE type_dir ="{typeDir}"'.format(typeDir=info["current_type_dir"])
        elif info["current_type_weight"] :
            sql = 'SELECT * FROM data_type WHERE type_weight ="{typeWeight}"'.format(typeWeight=str(info["current_type_weight"]))
        else:
            #TODO check need to raise exception or not
            return None
        ret = self.db.query(sql)
        if len(ret):
            return ret
        else:
            #TODO check need to raise exception or not
            return None

    def getDataType(self, typeId=None, typeName=None):
        sql = 'SELECT type_id, type_name, type_dir FROM data_type WHERE {condition}'
        if typeId:
            condition = 'type_id = {typeId}'.format(typeId=typeId)
        elif typeName:
            condition = 'type_name = "{typeName}"'.format(typeName=typeName)
        sql = sql.format(condition=condition)
        ret = self.db.query(sql)
        dataType = dict(typeId=ret[0][0],typeName=ret[0][1],typeDir=ret[0][2])
        return dataType

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

    def insertFortune(self,date,constellation,overall,love,career,wealth):
        sql = 'INSERT INTO fortune '\
            +' (`fortune_date`, `constellation`, `overall`, `love`, `career`, `wealth`)'\
            +' VALUES ("{date}","{constellation}","{overall}","{love}","{career}","{wealth}")'.format(
            date=date,constellation=constellation,overall=overall,love=love,career=career,wealth=wealth)
        self.db.cmd(sql)
        
    def checkFortuneExisted(self,date,constellation):
        sql = 'SELECT COUNT(*) FROM fortune WHERE fortune_date="{date}" AND constellation="{constellation}"'.format(
                date=date,constellation=constellation)
        return self.queryOneValue(sql)

class DatabaseDao(DefaultDao):
    def checkTableExisted(self,tableName):
        sql = 'SELECT count(*) FROM information_schema.tables '\
                +'WHERE table_schema = "broadcast" '\
                +'AND table_name ="{tableName}"'.format(tableName=tableName)
        existed = self.queryOneValue(sql)
        return True if existed else False

    def createTable(self,tableName,fields):
        fieldSql = ''
        for idx,(name,attr) in enumerate(fields.items()):
            if idx == 0:
                fieldSql += '{name} {attr}'
            else:
                fieldSql += ',{name} {attr}'
            fieldSql = fieldSql.format(name=name,attr=attr)
        sql = 'CREATE TABLE {tableName} ({fieldSql})'.format(tableName=tableName,fieldSql=fieldSql)
        self.db.cmd(sql)

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

    def getNewsByTime(self,hours,limit):
        sql = 'SELECT title, serial_number, data_type ' \
            + 'FROM news_QR_code where is_delete=0 and serial_number != "-1" ' \
            + 'and upload_time >= DATE_SUB(NOW(), INTERVAL {hours} HOUR) '.format(hours=hours) \
            + 'ORDER BY RAND() LIMIT {limitNumber}'.format(limitNumber=limit)
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

    def checkNewsExisted(self,serialNumber):
        sql = "SELECT COUNT(*) FROM news_QR_code WHERE serial_number = '{serialNumber}'".format(serialNumber=serialNumber)
        return self.queryOneValue(sql)
