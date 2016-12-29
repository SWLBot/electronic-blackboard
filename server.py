import tornado.ioloop
import tornado.web
import os.path
import bcrypt
from datetime import datetime
from PIL import Image
from mysql import MySQL

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    
    def get(self):
        user = self.get_current_user()
        if user:
            self.render("index.html",user = user)
        else:
            self.redirect("/signin")


    def post(self):
        self.write("Hello Tornado! post")

class SignupHandler(BaseHandler):
    def get(self):
        self.render('signup.html',flash=None)
    def post(self):
        client = MySQL()
        cursor = client.cursor
        getusername = tornado.escape.xhtml_escape(self.get_argument("username"))
        getpassword = tornado.escape.xhtml_escape(self.get_argument("password"))
        cursor.execute("select Count(*) from `user` where `name`=%s",(getusername,))
        is_existed = cursor.fetchone()[0]
        if is_existed == 0:
            hashed = bcrypt.hashpw(getpassword.encode('utf-8'),bcrypt.gensalt())
            now = datetime.now()
            ret = cursor.execute("insert into `user` (`name`,`password`,`create_time`) values (%s,%s,%s)",(getusername,hashed,now))
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

        client = MySQL()
        cursor = client.cursor
        getusername = tornado.escape.xhtml_escape(self.get_argument("username"))
        getpassword = tornado.escape.xhtml_escape(self.get_argument("password"))
        ret = cursor.execute("select `password` from user where `name` = %s",(getusername,))
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
        upload_path = os.path.join(os.path.dirname(__file__),"static/img")
        thumbnail_path = os.path.join(os.path.dirname(__file__),"thumbnail")
        file_metas=self.request.files['file']
        for meta in file_metas:
            filename=meta['filename']
            filepath=os.path.join(upload_path,filename)
            with open(filepath,"wb") as up:
                up.write(meta['body'])
            thumbnail_path=os.path.join(thumbnail_path,"thumbnail_"+filename)
            im = Image.open(filepath)
            im.thumbnail((200,200))
            im.save(thumbnail_path) 
        self.render("upload.html",flash="Upload finish!")

class Application(tornado.web.Application):
    def __init__(self):
        base_dir = os.path.dirname(__file__)

        settings = {
            "cookie_secret": "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
            "signin_url": "/signin",
            "template_path":os.path.join(base_dir,"template"),
            "static_path":os.path.join(base_dir,"static"),
            "thumbnail_path":os.path.join(base_dir,"thumbnail"),
            "debug":True,
            "xsrf_cookies":True,
            "autoreload":True
        }
        tornado.web.Application.__init__(self,[
            tornado.web.url(r"/",MainHandler,name="main"),
            tornado.web.url(r"/signin",LoginHandler,name="signin"),
            tornado.web.url(r"/signup",SignupHandler,name="signup"),
            tornado.web.url(r"/signout",LogoutHandler,name="signout"),
            tornado.web.url(r"/upload",UploadHandler,name="upload")
        ],**settings)

def main():
    Application().listen(3000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
