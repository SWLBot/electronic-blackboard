import tornado.ioloop
import tornado.web
import os.path
import bcrypt
from datetime import datetime
from PIL import Image
from mysql import mysql
from server_api import upload_image_insert_db
from server_api import edit_image_data
from server_api import edit_text_data
from server_api import upload_text_insert_db
from server_api import add_new_data_type
from server_api import delete_image_or_text_data
from display_api import display_image
from display_api import display_text
from pprint import pprint

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    
    def get(self):
        user = self.get_current_user()
        if user:
            imgs = display_image(user.decode("utf-8"))
            texts = display_text(user.decode("utf-8"))
            self.render("index.html",user = user,imgs=imgs,texts=texts)
        else:
            self.redirect("/signin")

class SignupHandler(BaseHandler):
    def get(self):
        if self.get_current_user().decode('utf-8') == 'admin':
            self.render('signup.html',flash=None)
        else:
            self.redirect('/')

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
            self.set_secure_cookie("incorrect","0")
            client.close()
            self.redirect(self.reverse_url("signup"))
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
            person_name = tornado.escape.xhtml_escape(self.get_argument('person_name'))
            reward = tornado.escape.xhtml_escape(self.get_argument('reward'))
            description = tornado.escape.xhtml_escape(self.get_argument('description'))
            year = tornado.escape.xhtml_escape(self.get_argument('year'))
            month = tornado.escape.xhtml_escape(self.get_argument('month'))
            client = mysql()
            client.connect()
            with open(receive_msg["text_system_dir"],"w") as fp:
                print(person_name,file=fp)
                print(reward,file=fp)
                print(description,file=fp)
                print(year,file=fp)
                print(month,file=fp)

            sql = "select type_id,type_name from data_type"
            data_types = client.query(sql)
            client.close()
            self.render("upload.html",flash="Upload finish!",data_types=data_types)

class EditHandler(BaseHandler):
    def get(self):
        img = None
        text = None
        client = mysql()
        client.connect()
        img_id = self.get_argument("img_id",default=None)
        if img_id:
            img = client.query("select * from image_data where img_is_delete = 0 and img_id = \""+img_id+"\"")[0]
        else:
            text_id = self.get_argument("text_id")
            text = client.query("select * from text_data where text_is_delete = 0 and text_id = \""+text_id+"\"")[0]
        client.close()
        self.render("edit.html",img=img,text=text,flash=None)

    def post(self):
        img = None
        text = None
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
            receive_msg = edit_text_data(send_msg)
            if receive_msg["result"] == "success":
                flash = "Edit "+self.get_argument("text_id")+" successed "
            else:
                flash = "Edit "+self.get_argument("text_id")+" failed "
            text = client.query("select * from text_data where text_id = \""+self.get_argument("text_id")+"\"")[0]
        client.close()
        self.render("edit.html",img=img,text=text,flash=flash)

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
            tornado.web.url(r"/edit",EditHandler,name="edit"),
            tornado.web.url(r"/delete",DeleteHandler,name="delete"),
            tornado.web.url(r"/addType",addTypeHandler,name="addType")
        ],**settings)

def main():
    Application().listen(3000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
