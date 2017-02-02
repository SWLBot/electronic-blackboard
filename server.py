import tornado.ioloop
import tornado.web
import os.path
import bcrypt
from datetime import datetime
from PIL import Image
from mysql_class import mysql
from server_api import upload_image_insert_db
from server_api import edit_image_data
from pprint import pprint

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    
    def get(self):
        user = self.get_current_user()
        if user:
            client = mysql()
            client.connect()
            imgs = client.query("select * from image_data where user_id in ( select user_id from user where user_name = \""+user.decode("utf-8")+"\")")
            self.render("index.html",user = user,imgs=imgs)
        else:
            self.redirect("/signin")


    def post(self):
        self.write("Hello Tornado! post")

class SignupHandler(BaseHandler):
    def get(self):
        self.render('signup.html',flash=None)
    def post(self):
        client = mysql()
        client.connect()
        cursor = client.cursor
        getusername = tornado.escape.xhtml_escape(self.get_argument("username"))
        getpassword = tornado.escape.xhtml_escape(self.get_argument("password"))
        cursor.execute("select Count(*) from `user` where `user_name`=%s",(getusername,))
        is_existed = cursor.fetchone()[0]
        if is_existed == 0:
            hashed = bcrypt.hashpw(getpassword.encode('utf-8'),bcrypt.gensalt())
            ret = cursor.execute("insert into `user` (`user_name`,`user_password`) values (%s,%s)",(getusername,hashed))
            client.db.commit()
            self.set_secure_cookie("user",getusername)
            self.set_secure_cookie("incorrect","0")
            client.close()
            self.redirect(self.reverse_url("main"))
        else:
            client.close()
            self.render("signup.html",flash=["The name \""+getusername+"\" has been used"])


        

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
            

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect(self.get_argument("next",self.reverse_url("main")))

class UploadHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        if user:
            self.render("upload.html",flash=None)
        else:
            self.redirect("/signin")

    def post(self):
        send_msg = {}
        receive_msg = {}
        upload_path = os.path.join(os.path.dirname(__file__),"static/img")
        thumbnail_path = os.path.join(os.path.dirname(__file__),"static/thumbnail")
        file_metas=self.request.files['file']
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
            im.thumbnail((200,200))
            im.save(thumbnail_path) 
        self.render("upload.html",flash="Upload finish!")

class EditHandler(BaseHandler):
    def get(self):
        client = mysql()
        client.connect()
        img = client.query("select * from image_data where img_id = \""+self.get_argument("img_id")+"\"")[0]
        client.close()
        self.render("edit.html",img=img,flash=None)

    def post(self):
        send_msg = {}
        receive_msg = {}
        client = mysql()
        client.connect()
        user = self.get_current_user()
        send_msg["server_dir"] = os.path.dirname(__file__)
        send_msg["file_type"] = tornado.escape.xhtml_escape(self.get_argument("img_type"))
        send_msg["img_id"] = tornado.escape.xhtml_escape(self.get_argument("img_id"))
        send_msg["start_date"] = tornado.escape.xhtml_escape(self.get_argument("img_start_date"))
        send_msg["end_date"] = tornado.escape.xhtml_escape(self.get_argument("img_end_date"))
        send_msg["start_time"] = tornado.escape.xhtml_escape(self.get_argument("img_start_time"))
        send_msg["end_time"] = tornado.escape.xhtml_escape(self.get_argument("img_end_time"))
        send_msg["display_time"] = tornado.escape.xhtml_escape(self.get_argument("img_display_time"))
        send_msg["user_id"] = client.query("select `user_id` from `user` where user_name = \""+user.decode("utf-8")+"\"")[0][0]
        receive_msg = edit_image_data(send_msg)
        if 'result' in receive_msg:
            flash = "Edit "+self.get_argument("img_id")+" successed "
        else:
            flash = "Edit "+self.get_argument("img_id")+" failed "
        img = client.query("select * from image_data where img_id = \""+self.get_argument("img_id")+"\"")[0]
        client.close()
        self.render("edit.html",img=img,flash=flash)

class Application(tornado.web.Application):
    def __init__(self):
        base_dir = os.path.dirname(__file__)

        settings = {
            "cookie_secret": "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
            "signin_url": "/signin",
            "template_path":os.path.join(base_dir,"template"),
            "static_path":os.path.join(base_dir,"static"),
            "debug":True,
            "xsrf_cookies":True,
            "autoreload":True
        }
        tornado.web.Application.__init__(self,[
            tornado.web.url(r"/",MainHandler,name="main"),
            tornado.web.url(r"/signin",LoginHandler,name="signin"),
            tornado.web.url(r"/signup",SignupHandler,name="signup"),
            tornado.web.url(r"/signout",LogoutHandler,name="signout"),
            tornado.web.url(r"/upload",UploadHandler,name="upload"),
            tornado.web.url(r"/edit",EditHandler,name="edit")
        ],**settings)

def main():
    Application().listen(3000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
