import tornado.ioloop
import tornado.web
import os.path
from broadcast_api import load_schedule 
import argparse

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    
    def get(self):
        self.set_cookie("_xsrf",self.xsrf_token)
        self.render("board.html")

    def post(self):
        self.write("")

class Get_DB_Data(BaseHandler):
    def get(self):
        self.write(load_schedule())

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
        }
        tornado.web.Application.__init__(self,[
            tornado.web.url(r"/",MainHandler,name="main"),
            tornado.web.url(r"/db_schedule",Get_DB_Data),
            ],**settings)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port",help="The port for electronic-blackboard")
  
    args = parser.parse_args()

    if args.port:
        Application().listen(args.port)
    else:
        Application().listen(4000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
