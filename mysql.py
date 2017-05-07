import os.path
import pymysql
class DB_Exception(Exception):
    pass

class mysql:
    def __init__(self, db=None, cursor=None):
        self.db = db;
        self.cursor = cursor;

    def __enter__(self):
        return self

    #file dir where file store host\n user\n password\n dbname\n
    def connect(self):
        file_name = "mysql_auth.txt"
        if not os.path.isfile(file_name) :
            raise DB_Exception(-1, "Mysql connect fail")
            return -1

        try:
            file_pointer = open(file_name,"r")
        except:
            raise DB_Exception(-1, "Mysql auth file open failed")
            return -1
        host_str = file_pointer.readline().rstrip('\n').strip(' ')
        user_str = file_pointer.readline().rstrip('\n').strip(' ')
        token_str = file_pointer.readline().rstrip('\n').strip(' ')
        dbname_str = file_pointer.readline().rstrip('\n').strip(' ')
        file_pointer.close()

        try:
            self.db = pymysql.connect(host_str, user_str, token_str, dbname_str, use_unicode=True, charset="utf8")
            self.cursor = self.db.cursor()
            #cursor.execute('SET NAMES utf8;')
            #cursor.execute('SET CHARACTER SET utf8;')
            #cursor.execute('SET character_set_connection=utf8;')
        except:
            raise DB_Exception(-1, "Mysql connect fail")
            return -1

        return 1

    #drop old table if exist!! be careful when using it!!
    def create_table(self, sql, table_name):
        try:
            drop_sql = "DROP TABLE IF EXISTS " + table_name
            self.cursor.execute(drop_sql)
            self.cursor.execute(sql)
        except:
            raise DB_Exception(-1, "Mysql create table fail")
            return -1
        return 1

    #insert, update, delete query
    def cmd(self, sql):
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except:
            self.db.rollback()
            raise DB_Exception(-1, "Mysql cmd fail")
            return -1
        return 1

    #find query
    def query(self, sql):
        try:
            self.cursor.execute(sql)
            result = self.cursor.fetchall()
        except:
            raise DB_Exception(-1, "Mysql query fail")
            result = -1
        return result

    def close(self):
        try:
            self.db.close()
        except:
            "Do Nothing"

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            self.db.close()
        except:
            "Do Nothing"
