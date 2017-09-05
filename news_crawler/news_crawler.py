import requests
import re
from .qrcode import make_qrcode_image
from bs4 import BeautifulSoup as bs
from mysql import mysql,DB_Exception
from env_init import create_data_type
from server_api import *
from dataAccessObjects import *
from collections import OrderedDict
import os
import datetime

def grab_inside_articles():
    url = 'https://www.inside.com.tw/category/trend'

    trend_page = requests.get(url).text
    soup = bs(trend_page,'html.parser')
    posts = soup.select('h3.post_title a.js-auto_break_title')
    path = "static/inside/"

    for post in posts:
        link = post['href']
        title = post.text
        serial_number = make_qrcode_image(link,path)
        send_obj = save_db_data(serial_number, title, "inside")
        news_insert_db(send_obj)

def grab_techorange_articles():
    url = 'https://buzzorange.com/techorange/'

    techorange = requests.get(url).text
    soup = bs(techorange, "html.parser")
    posts = soup.find_all('h4', attrs={'class' : 'entry-title'})
    path = "static/techOrange/"

    #top 9 articles without page down    
    for post in posts[:9]:   
        link = post.a["href"]
        title = post.a.text
        serial_number = make_qrcode_image(link,path)
        send_obj = save_db_data(serial_number, title, "techorange")
        news_insert_db(send_obj)

def grab_ptt_articles(boards):
    for board in boards:
        #get index page
        page = get_ptt_index_page(board)
        path = "static/ptt" + board +"/"
        #grab 10 hot articles 
        collect = 0
        while (collect<10):
            res = requests.get(
                url='https://www.ptt.cc/bbs/' + board + '/index' + str(page) + '.html',
                cookies={'over18': '1'}
            ).text
            soup = bs(res, 'html.parser')
            posts = soup.find_all("div", "r-ent")
            for post in posts:
                try:
                    push = post.find("span", attrs={'class':'f1'})
                    if push is not None:
                        collect = collect + 1
                        link = 'https://www.ptt.cc'+post.a["href"]
                        title = post.a.text
                        serial_number = make_qrcode_image(link,path)
                        send_obj = save_db_data(serial_number, title, "ptt"+board)
                        news_insert_db(send_obj)
                except TypeError:
                    pass
            page = page - 1

def get_ptt_index_page(board):
    print(board)
    content = requests.get(
        url= 'https://www.ptt.cc/bbs/' + board + '/index.html',
        cookies={'over18': '1'}
    ).content.decode('utf-8')
    first_page = re.search(r'href="/bbs/' + board + '/index(\d+).html">&lsaquo;', content)
    if first_page is None:
        return 1
    page = int(first_page.group(1)) + 1
    return page

def grab_medium_articles():
    url = 'https://medium.com/topic/technology'

    medium = requests.get(url).text
    soup = bs(medium, "html.parser")
    posts = soup.find_all('div', attrs={'class' : 'u-flex0 u-sizeFullWidth'})
    path = "static/medium/"
 
    for post in posts:   
        link = post.a["href"]
        title = post.a.text
        serial_number = make_qrcode_image(link,path)
        send_obj = save_db_data(serial_number, title, "medium")
        news_insert_db(send_obj)

def save_db_data(serial_number, title, type_name):
    send_obj={}
    with DataTypeDao() as dataTypeDao:
        data_type = dataTypeDao.getTypeId(typeName=type_name)

    send_obj["data_type"] = data_type
    send_obj["serial_number"] = serial_number
    send_obj["title"] = title

    return send_obj

def create_news_table():
    try:
        fields = OrderedDict()
        fields['id'] = 'int NOT NULL unique key auto_increment'
        fields['data_type'] = 'int NOT NULL'
        fields['serial_number'] = 'varchar(40) not NULL'
        fields['title'] = 'varchar(255) not NULL'
        fields['upload_time'] = 'datetime default now()'
        fields['is_delete'] = 'bit(1) default 0'
        with DatabaseDao() as databaseDao:
            databaseDao.createTable(tableName='news_QR_code',fields=fields)
        return dict(result='success')
    except DB_Exception as e:
        return dict(error=e.args[1],result='fail')

#create data_types for all websites crawler grabbed
def create_news_data_types():
    create_data_type('inside')
    create_data_type('techOrange')
    create_data_type('medium')
    create_data_type('pttjoke')
    create_data_type('pttStupidClown')
    create_data_type('pttBeauty')

#constellation fortune
def grab_constellation_fortune():
    date=str(datetime.date.today())
    constellation_list=['牡羊座','金牛座','雙子座','巨蟹座','獅子座','處女座','天秤座','天蝎座','射手座','摩羯座','水瓶座','雙鱼座']
    for i in range(12):
        send_obj={}
        res = requests.get('http://astro.click108.com.tw/daily_'+str(i)+'.php?iAcDay='+date+'&iAstro='+str(i))
        soup = bs(res.content, "html.parser")
        send_obj["overall"] = soup.find('span', {'class': 'txt_green'}).text[4:9]
        send_obj["love"] = soup.find('span', {'class': 'txt_pink'}).text[4:9]
        send_obj["career"] = soup.find('span', {'class': 'txt_blue'}).text[4:9]
        send_obj["wealth"] = soup.find('span', {'class': 'txt_orange'}).text[4:9]
        send_obj["constellation"]=constellation_list[i]
        fortune_insert_db(send_obj)

def create_fortune_table():
    try:
        fields = OrderedDict()
        fields['fortune_date'] = 'datetime'
        fields['constellation'] = 'varchar(20) not NULL'
        fields['overall'] = 'varchar(20) not NULL'
        fields['love'] = 'varchar(20) not NULL'
        fields['career'] = 'varchar(20) not NULL'
        fields['wealth'] = 'varchar(20) not NULL'
        with DatabaseDao() as databaseDao:
            databaseDao.createTable(tableName='fortune',fields=fields)
        return dict(result='success')
    except DB_Exception as e:
        return dict(error=e.args[1],result='fail')
