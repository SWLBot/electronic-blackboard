import pyqrcode
import hashlib
import os.path

def make_qrcode_image(url,path=''):
    try:
        ID = hashlib.md5(url.encode('utf8')).hexdigest()
        qr = pyqrcode.create(url,version=15)
        file_name = os.path.join(path,'%s.png' % ID)
        qr.png(file_name,scale=4)
        return ID
    except Exception as e:
        print(str(e))
        return -1
