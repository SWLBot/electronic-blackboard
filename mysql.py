import pymysql

class mysql:
    def connect():
        with open("mysql.txt","r") as file:
            host = file.readline().rstrip('\n')
            user = file.readline().rstrip('\n')
            passwd = file.readline().rstrip('\n')
            dbname = file.readline().rstrip('\n')
        try:
            self.db = pymysql.connect(host,ueser,passwd,dbname,use_unicode=True, charset="utf8")
            self.cursor = self.db.cursor()
        except:
            return 1
        return 0
    def close():
        self.db.close()


