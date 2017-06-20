from mysql import mysql
from env_init import create_data_type
import os

def create_user_data_file():
    print("check user_data dir and file...")
    try:
        if not os.path.exists("setting"):
            print('create dir setting"')
            os.makedirs('setting')
        if not os.path.isfile("setting/server_setting.txt"):
            print('create file "setting/server_setting.txt"')
            with open("setting/server_setting.txt", "w") as fp:
                fp.write("bluetooth_enable 1")
        print("check finish")
    except Exception as e:
        print("create user_data file failed",e)

def check_column_exist_or_add(db,table,column_name,data_type):
    if len(db.query('show columns from %s like "%s"' % (table,column_name))) == 0:
        print('%s doesn\'t in table %s' %(column_name,table))
        print('add %s %s into table %s' %(column_name,data_type,table))
        db.cmd('alter table %s add column %s %s' % (table,column_name,data_type))

def check_table_exist_or_create(db,table_name,sql):
    if len(db.query('show tables like "%s"' % (table_name))) == 0:
        print('Table %s doesn\'t exist' % table_name)
        print('Create table %s' % table_name)
        db.cmd(sql)

def check_data_type_exist_or_create(db,data_type):
    if len(db.query('select * from data_type where type_name = "%s"' % data_type)) == 0:
        print("%s data_type doesn't exist" % data_type)
        create_data_type(data_type)

def check_bluetooth_DB(db):
    create_user_data_file()
    check_table_exist_or_create(db,'user_prefer','create table user_prefer ( \
                                pref_id varchar(14) unique key, \
                                user_id int default 0, \
                                pref_data_type_01 varchar(100), \
                                pref_data_type_02 varchar(100), \
                                pref_data_type_03 varchar(100), \
                                pref_data_type_04 varchar(100), \
                                pref_data_type_05 varchar(100), \
                                pref_set_time datetime default now(), \
                                pref_is_delete bit(1) default 0)')
    check_column_exist_or_add(db,'user','user_bluetooth_id','varchar(50)')
    check_column_exist_or_add(db,'user','user_profession','int default 0 not null')
    check_column_exist_or_add(db,'image_data','img_like_count','int default 0')
    check_column_exist_or_add(db,'user','user_birthday','datetime')
    check_column_exist_or_add(db,'text_data','text_like_count','int default 0')
    check_data_type_exist_or_create(db,"customized_text")

def main():
    db = mysql()
    db.connect()
    check_bluetooth_DB(db)

main()
