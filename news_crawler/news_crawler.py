import requests
from .qrcode import make_qrcode_image
from bs4 import BeautifulSoup as bs
from mysql import mysql,DB_Exception
from env_init import create_data_type
from server_api import *
import os

def grab_inside_articles():
    url = 'https://www.inside.com.tw/category/trend'

    trend_page = requests.get(url).text
    soup = bs(trend_page,'html.parser')
    posts = soup.select('h3.post_title a.js-auto_break_title')
    if not os.path.exists("static/inside/"):
        os.makedirs("static/inside/")
    path = "static/inside/"

    for post in posts:
        link = post['href']
        title = post.text
        serial_number = make_qrcode_image(link,path)
        send_obj = save_inside_db_data(serial_number, title)
        news_insert_db(send_obj)
            
def save_inside_db_data(serial_number, title):
    send_obj={}
    db = mysql()
    db.connect()
    #get INSIDE data type
    sql = "SELECT type_id FROM data_type WHERE type_name='inside'"
    pure_result = db.query(sql)
    data_type = int(pure_result[0][0])

    send_obj["data_type"] = data_type
    send_obj["serial_number"] = serial_number
    send_obj["title"] = title

    db.close()   
    return send_obj

def create_news_table():
    try:
        client = mysql()
        client.connect()
        sql =   'create table news ( \
                id int NOT NULL unique key auto_increment, \
                data_type int NOT NULL, \
                serial_number varchar(40) not NULL, \
                title varchar(255) not NULL \
                )'
        print(sql)
        client.cmd(sql)
        return dict(result='success')
    except DB_Exception as e:
        return dict(error=e.args[1])

#create data_types for all websites crawler grabbed
def create_news_data_types():
    create_data_type('inside')
