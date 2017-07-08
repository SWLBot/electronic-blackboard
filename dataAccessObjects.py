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

class UserDao(DefaultDao):
    def getUserId(self,userName=None,bluetoothId=None):
        sql = 'SELECT user_id FROM user WHERE '
        if userName:
            sql += 'user_name = "{userName}"'.format(userName=userName)
        elif bluetoothId:
            sql += 'user_bluetooth_id = "{bluetoothId}"'.format(bluetoothId=bluetoothId)

        ret = self.db.query(sql)
        if len(ret):
            return ret[0][0]
        else:
            #TODO raise exception
            return None

    def getUserLevel(self,userId):
        sql = 'SELECT user_level FROM user WHERE user_id  = {userId}'.format(userId=userId)
        ret = self.db.query(sql)
        if len(ret):
            return int(ret[0][0])
        else:
            #TODO raise exception
            return None

    def getUserBirthday(self,userId):
        sql = 'select user_birthday from user where user_id = {userId}'.format(userId=userId)
        ret = self.db.query(sql)
        if len(ret):
            return ret[0][0]
        else:
            #TODO raise exception
            return None

class ScheduleDao(DefaultDao):
    def getDisplayingSchedule(self):
        sql = 'SELECT sche_sn FROM schedule WHERE sche_is_used=0 ORDER BY sche_sn ASC LIMIT 1'
        ret = self.db.query(sql)
        if len(ret):
            return int(ret[0][0])
        else:
            #TODO raise exception
            return None

    def markExpiredSchedule(self,scheSn=None):
        sql = 'UPDATE schedule SET sche_is_used=1 WHERE sche_sn={scheSn}'.format(scheSn)
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
