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
    def getUserId(self,userName):
        sql = 'SELECT user_id FROM user WHERE user_name = "{userName}"'.format(userName=userName)
        ret = self.db.query(sql)
        if len(ret):
            return ret[0][0]
        else:
            #TODO raise exception
            return None

