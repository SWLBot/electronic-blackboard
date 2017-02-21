import pymysql
import subprocess
import bcrypt
import os

with open("mysql_auth.txt","r") as fp:
    host = fp.readline().rstrip()
    user = fp.readline().rstrip()
    passwd = fp.readline().rstrip()
    dbname = fp.readline().rstrip()


print("Connect to MySQL server")
try:
    client = pymysql.connect(host,user,passwd,use_unicode=True,charset="utf8")
    cursor = client.cursor()
except:
    print("Connect failed")
    exit(1)

print("Dropping database \"%s\" if existed" % dbname)
cursor.execute("DROP DATABASE IF EXISTS "+dbname)
print("Creating database \"%s\"" % dbname)
cursor.execute("CREATE DATABASE %s character set utf8" % dbname)

with open("create_tables.sql","r") as file:
    subprocess.call(["mysql","-u",user,"-p"+passwd],stdin=file)

client.close()

client = pymysql.connect(host,user,passwd,dbname,use_unicode=True,charset='utf8')
cursor = client.cursor()

print("create user \"admin\"")
user_name = 'admin'
user_hashed_passwd = bcrypt.hashpw('admin'.encode('utf-8'),bcrypt.gensalt())
ret = cursor.execute("insert into `user` (`user_name`,`user_password`) values (%s,%s)", (user_name,user_hashed_passwd))

print("create data_type \"圖片\"")
ret = cursor.execute('insert into `data_type` (`type_name`,`type_dir`) values ("圖片","圖片/")')
if not os.path.exists("static/圖片"):
    print("create dir \"圖片\"")
    os.makedirs("static/圖片")


client.commit()
client.close()
