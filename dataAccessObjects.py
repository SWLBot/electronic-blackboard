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
            return int(ret[0][0])
        else:
            #TODO raise exception
            return None
