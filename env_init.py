import pymysql
import subprocess
import bcrypt
import os
from mysql import mysql,DB_Exception

def create_data_type(data_type_name,base_dir=None):
    try:
        client = mysql()
        client.connect()
        print('create data_type "%s"...' % data_type_name)
        path = ''
        if base_dir:
            path = base_dir + '/'
    
        path += data_type_name
        try:
            ret = client.cmd('insert into `data_type` (`type_name`,`type_dir`) values ("%s","%s/")' % (data_type_name,path))
        except:
            print("Insert type failed")

        if not os.path.exists("static/%s" % path):
            print('create dir "static/%s"' % path)
            os.makedirs('static/%s' % path)
    except DB_Exception as e:
        print(e.arg(1))

def env_init():
    try:
        with open("mysql_auth.txt","r") as fp:
            host = fp.readline().rstrip()
            user = fp.readline().rstrip()
            passwd = fp.readline().rstrip()
            dbname = fp.readline().rstrip()
    except:
        print("Open authorization file failed")
        exit(1)

    print("Connect to MySQL server...")
    try:
        client = pymysql.connect(host,user,passwd,use_unicode=True,charset="utf8")
        cursor = client.cursor()
    except:
        print("Connect failed")
        exit(1)

    print("Dropping database \"%s\" if existed..." % dbname)
    cursor.execute("DROP DATABASE IF EXISTS "+dbname)
    print("Creating database \"%s\"..." % dbname)
    cursor.execute("CREATE DATABASE %s character set utf8" % dbname)
    try:
        with mysql() as db:
            db.connect()
            with open("create_tables.sql","r") as file:
                sql_Commands = file.read()
                sql_Commands = sql_Commands.replace('\n','').split(';')
            for sql in sql_Commands[:-1]:
                db.cmd(sql)
    except:
        print("Open sql file failed")
        exit(1)
    client.close()

    try:
        client = pymysql.connect(host,user,passwd,dbname,use_unicode=True,charset='utf8')
        cursor = client.cursor()
    except:
        print("Connect failed")
        exit(1)

    print("create user \"admin\"...")
    user_name = 'admin'
    user_hashed_passwd = bcrypt.hashpw('admin'.encode('utf-8'),bcrypt.gensalt())
    try:
        ret = cursor.execute("insert into `user` (`user_name`,`user_password`,`user_level`) values (%s,%s,10000)", (user_name,user_hashed_passwd))
    except:
        print("Insert user failed")

    create_data_type("圖片")

    create_data_type("獲獎公告")

    create_data_type("活動公告")

    create_data_type("氣像雲圖","圖片")

    create_data_type("google_drive_image","圖片")

    create_data_type("google日曆")

    create_data_type("customized_text")

    print("create arrage_mode 0...")
    try:
        ret = cursor.execute('insert into `arrange_mode` (`armd_mode`) values (0)')
    except:
        print("Insert arrange mode failed")

    client.commit()
    client.close()
 
if __name__ == "__main__":
    env_init()
