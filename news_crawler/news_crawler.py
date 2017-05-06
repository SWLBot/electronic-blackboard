import requests
from .qrcode import make_qrcode_image
from bs4 import BeautifulSoup as bs
from mysql import mysql,DB_Exception
from env_init import create_data_type

def grab_inside_articles():
    url = 'https://www.inside.com.tw/category/trend'

    trend_page = requests.get(url).text
    soup = bs(trend_page,'html.parser')
    posts = soup.select('h3.post_title a.js-auto_break_title')
    for post in posts:
        link = post['href']
        title = post.text
        #TODO add path in make_qrcode_image
        serial_number = make_qrcode_image(link)

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
