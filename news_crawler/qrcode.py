import pyqrcode
import hashlib
import os.path
from urllib import request, parse
from bs4 import BeautifulSoup

def shorten_url(long_url):
    url_data = parse.urlencode(dict(url=long_url))
    byte_data = str.encode(url_data)
    ret = request.urlopen("http://tinyurl.com/api-create.php", data=byte_data).read()
    result = str(ret)[2:-1]
    return result

def make_qrcode_image(url,path='',event=None):
    try:
        url = shorten_url(url)
        if event:
            ID = event
            qr = pyqrcode.create(url,version=15)
        else:
            ID = hashlib.md5(url.encode('utf8')).hexdigest()
            qr = pyqrcode.create(url,version=15)
        file_name = os.path.join(path,'%s.png' % ID)
        qr.png(file_name,scale=4)
        return ID
    except Exception as e:
        print(str(e))
        return -1
