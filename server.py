import tornado.ioloop
import tornado.web
import tornado.options
import tornado.httpserver
import os.path
import bcrypt
from PIL import Image
from mysql import mysql
from server_api import *
from display_api import display_image
from display_api import display_text
import argparse
import json
import config.settings

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    
    def get(self):
        user = self.get_current_user()
        if user:
            imgs = display_image(user.decode("utf-8"))
            texts = display_text(user.decode("utf-8"))
            client = mysql()
            client.connect()
            sql = "select type_id,type_name from data_type"
            data_types = client.query(sql)
            self.render("index.html",user = user,imgs=imgs,data_types=data_types,texts=texts)
        else:
            self.redirect("/signin")

class SignupHandler(BaseHandler):
    def get(self):
        if self.get_current_user().decode('utf-8') == 'admin':
            self.render('signup.html',flash=None)
        else:
            self.redirect('/')

    def post(self):
        user_info = get_user_name_and_password(self)
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

        client = mysql()
        client.connect()
        cursor = client.cursor
        getusername = tornado.escape.xhtml_escape(self.get_argument("username"))
        getpassword = tornado.escape.xhtml_escape(self.get_argument("password"))
        ret = cursor.execute("select `user_password` from user where `user_name` = %s",(getusername,))
        if ret != 0:
            hashed = cursor.fetchone()[0].encode('utf-8')
            if bcrypt.checkpw(getpassword.encode('utf-8'),hashed):
                self.set_secure_cookie("user",self.get_argument("username"))
                self.set_secure_cookie("incorrect","0")
                self.redirect(self.reverse_url("main"))
            else:
                incorrect = self.get_secure_cookie("incorrect") or 0
                increased = str(int(incorrect)+1)
                self.set_secure_cookie("incorrect",increased)
                self.render("signin.html",flash=["wrong password","You can still try "+str(20-int(increased))+" times"])                
        else:
            incorrect = self.get_secure_cookie("incorrect") or 0
            increased = str(int(incorrect)+1)
            self.set_secure_cookie("incorrect",increased)
            self.render("signin.html",flash=["No such user","You can still try "+str(20-int(increased))+" times"])
            
class ChangePasswdHandler(BaseHandler):
    def get(self):
        self.render("changepasswd.html",flash=None)

    def post(self):
        send_msg = {}
        send_msg['user_name'] = self.get_current_user()
        send_msg['old_password'] = self.get_argument('old_password')
        send_msg['new_password'] = self.get_argument('new_password')
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
        sql = "select type_id,type_name from data_type"
        client = mysql()
        client.connect()
        data_types = client.query(sql)
        client.close()
        if user:
            self.render("upload.html",flash=None,data_types=data_types)
        else:
            self.redirect("/signin")

    def post(self):
        send_msg = {}
        receive_msg = {}
        upload_path = os.path.join(os.path.dirname(__file__),"static/img")
        thumbnail_path = os.path.join(os.path.dirname(__file__),"static/thumbnail")
        user = self.get_current_user()
        client = mysql()
        client.connect()
        send_msg["server_dir"] = os.path.dirname(__file__)
        send_msg["file_type"] = tornado.escape.xhtml_escape(self.get_argument("file_type"))
        send_msg["file_dir"] = upload_path
        send_msg["start_date"] = tornado.escape.xhtml_escape(self.get_argument("start_date"))
        send_msg["end_date"] = tornado.escape.xhtml_escape(self.get_argument("end_date"))
        send_msg["start_time"] = tornado.escape.xhtml_escape(self.get_argument("start_time"))
        send_msg["end_time"] = tornado.escape.xhtml_escape(self.get_argument("end_time"))
        send_msg["display_time"] = tornado.escape.xhtml_escape(self.get_argument("display_time"))
        send_msg["user_id"] = client.query("select `user_id` from `user` where user_name = \""+user.decode("utf-8")+"\"")[0][0]
        client.close()
        if self.get_argument('type') == 'image':
            try:
                file_metas=self.request.files['file']
                for meta in file_metas:
                    filename=meta['filename']
                    filepath=os.path.join(upload_path,filename)
                    send_msg["file_dir"] = filepath
                    with open(filepath,"wb") as up:
                        up.write(meta['body'])
                    receive_msg = upload_image_insert_db(send_msg)

                    filepath = receive_msg["img_system_dir"]
                    thumbnail_path=os.path.join(thumbnail_path,receive_msg["img_thumbnail_name"])
                    im = Image.open(filepath)
                    im.thumbnail((100,100))
                    im.save(thumbnail_path) 

                sql = "select type_id,type_name from data_type"
                client = mysql()
                client.connect()
                data_types = client.query(sql)
                client.close()
                self.render("upload.html",flash="Upload finish!",data_types=data_types)
            except:
                self.redirect("/upload")
        else:
            receive_msg = upload_text_insert_db(send_msg)
            text_file = {} 
            text_file['title1'] = tornado.escape.xhtml_escape(self.get_argument('title1')).replace('&amp;nbsp','&nbsp').replace('&lt;br&gt;','<br>')
            text_file['title2'] = tornado.escape.xhtml_escape(self.get_argument('title2')).replace('&amp;nbsp','&nbsp').replace('&lt;br&gt;','<br>')
            text_file['description'] = tornado.escape.xhtml_escape(self.get_argument('description')).replace('&lt;br&gt;','<br>').replace('&amp;nbsp','&nbsp')
            text_file['year'] = tornado.escape.xhtml_escape(self.get_argument('year'))
            text_file['month'] = tornado.escape.xhtml_escape(self.get_argument('month'))
            client = mysql()
            client.connect()
            
            with open(receive_msg["text_system_dir"],"w") as fp:
                print(json.dumps(text_file),file=fp)

            sql = "select type_id,type_name from data_type"
            data_types = client.query(sql)
            client.close()
            self.render("upload.html",flash="Upload finish!",data_types=data_types)

class EditHandler(BaseHandler):
    def get(self):
        img = None
        text = None
        text_content = None
        client = mysql()
        client.connect()
        sql = "select type_id,type_name from data_type"
        data_types = client.query(sql)
        img_id = self.get_argument("img_id",default=None)
        if img_id:
            img = client.query("select * from image_data where img_is_delete = 0 and img_id = \""+img_id+"\"")[0]
        else:
            text_id = self.get_argument("text_id")
            text_content = read_text_data(text_id)
            text = client.query("select * from text_data where text_is_delete = 0 and text_id = \""+text_id+"\"")[0]
        client.close()
        self.render("edit.html",img=img,text=text,data_types=data_types,flash=None,text_content=text_content)

    def post(self):
        img = None
        text = None
        text_content = None
        send_msg = {}
        receive_msg = {}
        client = mysql()
        client.connect()
        user = self.get_current_user()
        send_msg["server_dir"] = os.path.dirname(__file__)
        send_msg["file_type"] = tornado.escape.xhtml_escape(self.get_argument("data_type"))
        send_msg["start_date"] = tornado.escape.xhtml_escape(self.get_argument("start_date"))
        send_msg["end_date"] = tornado.escape.xhtml_escape(self.get_argument("end_date"))
        send_msg["start_time"] = tornado.escape.xhtml_escape(self.get_argument("start_time"))
        send_msg["end_time"] = tornado.escape.xhtml_escape(self.get_argument("end_time"))
        send_msg["display_time"] = tornado.escape.xhtml_escape(self.get_argument("display_time"))
        send_msg["user_id"] = client.query("select `user_id` from `user` where user_name = \""+user.decode("utf-8")+"\"")[0][0]
        if self.get_argument("type") == "image":
            send_msg["img_id"] = tornado.escape.xhtml_escape(self.get_argument("img_id"))
            receive_msg = edit_image_data(send_msg)
            if receive_msg["result"] == "success":
                flash = "Edit "+self.get_argument("img_id")+" successed "
            else:
                flash = "Edit "+self.get_argument("img_id")+" failed "
            img = client.query("select * from image_data where img_id = \""+self.get_argument("img_id")+"\"")[0]
        else:
            send_msg["text_id"] = tornado.escape.xhtml_escape(self.get_argument("text_id"))
            send_msg["invisible_title"] = send_msg["text_id"]
            send_msg["text_file"] = {}
            send_msg["text_file"]['title1'] = tornado.escape.xhtml_escape(self.get_argument('title1'))
            send_msg["text_file"]['title2'] = tornado.escape.xhtml_escape(self.get_argument('title2'))
            send_msg["text_file"]['description'] = tornado.escape.xhtml_escape(self.get_argument('description'))
            send_msg["text_file"]['year'] = tornado.escape.xhtml_escape(self.get_argument('year'))
            send_msg["text_file"]['month'] = tornado.escape.xhtml_escape(self.get_argument('month'))
            receive_msg = edit_text_data(send_msg)
            if receive_msg["result"] == "success":
                flash = "Edit "+self.get_argument("text_id")+" successed "
            else:
                flash = "Edit "+self.get_argument("text_id")+" failed "
            text = client.query("select * from text_data where text_id = \""+self.get_argument("text_id")+"\"")[0]
            text_content = read_text_data(send_msg["text_id"])
        sql = "select type_id,type_name from data_type"
        data_types = client.query(sql)
        client.close()
        self.render("edit.html",img=img,text=text,data_types=data_types,flash=flash,text_content=text_content)

class DeleteHandler(BaseHandler):
    def get(self):
        send_msg = {}
        client = mysql()
        client.connect()
        user_name = self.get_current_user().decode("utf-8")
        user_id = client.query("select user_id from user where user_name = \""+user_name+"\"")[0][0]
        send_msg["server_dir"] = os.path.dirname(__file__)
        send_msg["target_id"] = tornado.escape.xhtml_escape(self.get_argument("target_id"))
        send_msg["user_id"] = user_id
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

def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port",help="The port for backend sever")
    args = parser.parse_args()

    base_dir = os.path.dirname(__file__)
    settings = {
        "cookie_secret": config.settings.server['cookie_secret'],
        "template_path":os.path.join(base_dir,"template"),
        "static_path":os.path.join(base_dir,"static"),
        "debug":True,
        "xsrf_cookies":True,
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
        tornado.web.url(r"/addType",addTypeHandler,name="addType")
    ],**settings)
    http_server = tornado.httpserver.HTTPServer(application)
    if args.port:
        http_server.listen(args.port)
    else:
        http_server.listen(3000)

    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
