import tornado.ioloop
import tornado.web
import os.path
from PIL import Image
from os import listdir

class BaseHandler(tornado.web.RequestHandler):
   pass 

class MainHandler(BaseHandler):
    
    def get(self):
        base_dir = os.path.dirname(__file__)
        file_dir = os.path.join(base_dir,"static/img")
        print(file_dir)
        files = listdir(file_dir)
        print
        self.render("board.html",files=files)


class Application(tornado.web.Application):
    def __init__(self):
        base_dir = os.path.dirname(__file__)

        settings = {
            "cookie_secret": "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
            "template_path":os.path.join(base_dir,"template"),
            "static_path":os.path.join(base_dir,"static"),
            "thumbnail_path":os.path.join(base_dir,"thumbnail"),
            "file_path":os.path.join(base_dir,"files"),
            "debug":True,
            "xsrf_cookies":True,
            "autoreload":True
        }
        tornado.web.Application.__init__(self,[
            tornado.web.url(r"/",MainHandler,name="main"),
        ],**settings)

def main():
    Application().listen(4000)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
