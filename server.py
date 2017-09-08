import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
from tornado.options import define, options, parse_command_line
import os.path
import bcrypt
from PIL import Image
from mysql import mysql
from mysql import DB_Exception
from server_api import *
from display_api import *
import json
import config.settings

import httplib2

from apiclient import discovery
from pprint import pprint
import datetime

define('port',default=3000,help='run the server on the given port',type=int)
define('log_file_prefix',default='server.log',help='log file name',type=str)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    
    def get(self):
        user = self.get_current_user()
        if user:
            imgs = display_image(user.decode("utf-8"))
            texts = display_text(user.decode("utf-8"))
            data_types = display_data_types()
            self.render("index.html",user = user,imgs=imgs,data_types=data_types,texts=texts)
        else:
            self.redirect("/signin")

class DisplayHandler(BaseHandler):
    def get(self):
        user = self.get_current_user().decode('utf-8')
        data_type = self.get_argument('type')
        page = self.get_argument('page')
        if data_type == 'image':
            data = display_image(user)
        elif data_type == 'text':
            data = display_text(user)
        data_types = display_data_types()
        transform_date_string(data)
        convert_img_file_path(self,data,data_types)
        self.write(dict(type=data_type,data=data,data_types=data_types,page=page))

class SignupHandler(BaseHandler):
    def get(self):
        if self.get_current_user().decode('utf-8') == 'admin':
            self.render('signup.html',flash=None)
        else:
            self.redirect('/')

    def post(self):
        userArgUtil = UserArgumentsUtil(self)
        user_info = userArgUtil.getArguments()
        ret = check_user_existed_or_signup(user_info)
        if 'error' in ret:
            self.render('signup.html',flash=ret['error'])
        else:
            self.render('signup.html',flash=ret['flash'])

class LoginHandler(BaseHandler):
    def get(self):
        incorrect = self.get_secure_cookie("incorrect")
        if incorrect and int(incorrect) > 20:
            self.write('<center>Blocked</center>')
            return
        self.render('signin.html',flash=None)
    def post(self):
        incorrect = self.get_secure_cookie("incorrect")
        if incorrect and int(incorrect) > 20:
            self.write('<center>Blocked</center>')
            return

        userArgUtil = UserArgumentsUtil(self)
        user_info = userArgUtil.getArguments()
        ret = check_user_password(user_info)

        if 'success' in ret:
            self.set_secure_cookie("user",self.get_argument("username"))
            self.set_secure_cookie("incorrect","0")
            self.redirect(self.reverse_url("main"))
        elif 'fail' in ret:
            incorrect = self.get_secure_cookie("incorrect") or 0
            increased = str(int(incorrect)+1)
            self.set_secure_cookie("incorrect",increased)
            self.render('signin.html',flash=[ret['fail'],"You can still try"+str(20-int(increased))+" times"])
            
class ChangePasswdHandler(BaseHandler):
    def get(self):
        self.render("changepasswd.html",flash=None)

    def post(self):
        userEditArgUtil = UserEditArgumentsUtil(self)
        send_msg = userEditArgUtil.getArguments()
        receive_msg = change_password(send_msg)
        if receive_msg['result'] == "success":
            flash = "Change password success"
        else:
            flash = "Change password failed "+receive_msg['error']
        self.render("changepasswd.html",flash=flash)

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next",self.reverse_url("main")))

class UploadHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        data_types = display_data_types()
        if user:
            self.render("upload.html",flash=None,data_types=data_types)
        else:
            self.redirect("/signin")

    def post(self):
        send_msg = {}
        receive_msg = {}
        upload_path = os.path.join(os.path.dirname(__file__),"static/img")
        thumbnail_path = os.path.join(os.path.dirname(__file__),"static/thumbnail")
        send_msg = get_upload_meta_data(self) 
        send_msg["file_dir"] = upload_path
        if self.get_argument('type') == 'image':
            try:
                file_metas=self.request.files['file']
                for meta in file_metas:
                    filename=meta['filename']
                    filepath=os.path.join(upload_path,filename)
                    send_msg["file_dir"] = filepath
                    store_image(filepath,meta['body'])
                    receive_msg = upload_image_insert_db(send_msg)

                    filepath = receive_msg["img_system_dir"]
                    thumbnail_path=os.path.join(thumbnail_path,receive_msg["img_thumbnail_name"])
                    store_thumbnail_image(filepath,thumbnail_path)

                data_types = display_data_types()
                self.render("upload.html",flash="Upload finish!",data_types=data_types)
            except:
                self.redirect("/upload")
        else:
            receive_msg = upload_text_insert_db(send_msg)
            text_file = get_upload_text_data(self)

            if text_file['result'] == 'success':
                text_file.pop('result')
                with open(receive_msg["text_system_dir"],"w") as fp:
                    print(json.dumps(text_file),file=fp)

            data_types = display_data_types()
            self.render("upload.html",flash="Upload finish!",data_types=data_types)

class EditHandler(BaseHandler):
    def get(self):
        img = None
        text = None
        text_content = None
        data_types = display_data_types()
        img_id = self.get_argument("img_id",default=None)
        if img_id:
            img = get_img_meta(img_id)
        else:
            text_id = self.get_argument("text_id")
            text_content = read_text_data(text_id)
            text = get_text_meta(text_id)
        self.render("edit.html",img=img,text=text,data_types=data_types,flash=None,text_content=text_content)

    def post(self):
        img = None
        text = None
        text_content = None
        send_msg = {}
        receive_msg = {}
        send_msg = get_upload_meta_data(self)
        if self.get_argument("type") == "image":
            send_msg["img_id"] = tornado.escape.xhtml_escape(self.get_argument("img_id"))
            receive_msg = edit_image_data(send_msg)
            if receive_msg["result"] == "success":
                flash = "Edit "+self.get_argument("img_id")+" successed "
            else:
                flash = "Edit "+self.get_argument("img_id")+" failed "
            img = get_img_meta(self.get_argument("img_id"))
        else:
            send_msg["text_id"] = tornado.escape.xhtml_escape(self.get_argument("text_id"))
            send_msg["invisible_title"] = send_msg["text_id"]
            send_msg["text_file"] = get_upload_text_data(self)
            receive_msg = edit_text_data(send_msg)
            if receive_msg["result"] == "success":
                flash = "Edit "+self.get_argument("text_id")+" successed "
            else:
                flash = "Edit "+self.get_argument("text_id")+" failed "
            text = get_text_meta(self.get_argument("text_id"))
            text_content = read_text_data(send_msg["text_id"])
        data_types = display_data_types()
        self.render("edit.html",img=img,text=text,data_types=data_types,flash=flash,text_content=text_content)

class DeleteHandler(BaseHandler):
    def get(self):
        send_msg = {}
        user_name = self.get_current_user().decode("utf-8")
        send_msg["server_dir"] = os.path.dirname(__file__)
        send_msg["target_id"] = tornado.escape.xhtml_escape(self.get_argument("target_id"))
        send_msg["user_id"] = get_user_id(user_name)
        receive_msg = delete_image_or_text_data(send_msg)
        if receive_msg["result"] == "success":
            flash = "delete "+send_msg["target_id"]+" success!"
        else:
            flash = receive_msg["error"]
        self.redirect("/")

class addTypeHandler(BaseHandler):
    def get(self):
        self.render("add_type.html",flash=None)

    def post(self):
        send_msg = {}
        send_msg["type_name"] = tornado.escape.xhtml_escape(self.get_argument('type_name'))
        receive_msg = add_new_data_type(send_msg)
        if receive_msg["result"] == "success":
            flash = 'ADD TYPE SUCCESS!'
        else:
            flash = 'ADD TYPE FAILED! '+receive_msg["error"]
        self.render('add_type.html',flash=flash)

class googleApiHandler(BaseHandler):
    def get(self):
        if self.get_argument('code',default=None):
            code = self.get_argument('code')
            credentials = exchange_code_and_store_credentials(code)
        else:
            credentials = get_credentials(self)
        self.redirect('/')
        
class BluetoothHandler(BaseHandler):
    def get(self):
        bluetooth_id = self.get_argument("bluetooth_id", default='')
        #self.write("Hello, {}!".format(bluetooth_id))
        receive_msg = {}
        receive_msg = deal_with_bluetooth_id(bluetooth_id)
        if receive_msg["result"] == "success":
            self.write("success {}".format(bluetooth_id))
        else :
            self.write("fail {}".format(bluetooth_id))

class SendlikeHandler(BaseHandler):
    def get(self):
        receive_msg = {}
        receive_msg = add_now_like_count()
        if receive_msg["result"] == "success":
            self.write("success")
        else :
            self.write("fail")
#
class AppRegisterHandler(BaseHandler):
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        receive_msg = {}
        receive_msg = add_account_and_prefer(data)
        if receive_msg["result"] == "success":
            self.write("success")
        else :
            msg = "fail - " + receive_msg["error"]
            self.write(msg)

def main():
    parse_command_line()

    base_dir = os.path.dirname(__file__)
    settings = {
        "cookie_secret": config.settings.server['cookie_secret'],
        "template_path":os.path.join(base_dir,"template"),
        "static_path":os.path.join(base_dir,"static"),
        "debug":True,
        "autoreload":True
    }
    application = tornado.web.Application([
        tornado.web.url(r"/",MainHandler,name="main"),
        tornado.web.url(r"/signin",LoginHandler,name="signin"),
        tornado.web.url(r"/signup",SignupHandler,name="signup"),
        tornado.web.url(r"/changepw",ChangePasswdHandler,name="changepw"),
        tornado.web.url(r"/signout",LogoutHandler,name="signout"),
        tornado.web.url(r"/upload",UploadHandler,name="upload"),
        tornado.web.url(r"/edit",EditHandler,name="edit"),
        tornado.web.url(r"/delete",DeleteHandler,name="delete"),
        tornado.web.url(r"/addType",addTypeHandler,name="addType"),
        tornado.web.url(r"/googleapi",googleApiHandler,name="googleapi"),
        tornado.web.url(r"/bluetooth",BluetoothHandler,name="bluetooth"),
        tornado.web.url(r"/sendlike",SendlikeHandler,name="sendlike"),
        tornado.web.url(r"/appregister",AppRegisterHandler,name="appregister"),
        tornado.web.url(r"/display",DisplayHandler,name="display"),
    ],**settings)
    http_server = tornado.httpserver.HTTPServer(application)

    http_server.listen(options.port)

    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
