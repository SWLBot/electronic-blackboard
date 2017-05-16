import requests
import re
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
                        link = post.a["href"]
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

def save_db_data(serial_number, title, datatype):
    send_obj={}
    db = mysql()
    db.connect()
    #get data type
    sql = "SELECT type_id FROM data_type WHERE type_name='" + datatype + "'"
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
        sql =   'create table news_QR_code ( \
                id int NOT NULL unique key auto_increment, \
                data_type int NOT NULL, \
                serial_number varchar(40) not NULL, \
                title varchar(255) not NULL, \
                upload_time datetime default now(), \
                is_delete bit(1) default 0 \
                )'
        print(sql)
        client.cmd(sql)
        return dict(result='success')
    except DB_Exception as e:
        return dict(error=e.args[1])

#create data_types for all websites crawler grabbed
def create_news_data_types():
    create_data_type('inside')
    create_data_type('techOrange')
    create_data_type('pttjoke')
    create_data_type('pttStupidClown')
    create_data_type('pttBeauty')
