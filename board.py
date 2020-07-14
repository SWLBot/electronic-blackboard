import tornado.ioloop
import tornado.web
import tornado.httpserver
from tornado.options import define, options, parse_command_line
import os.path
from broadcast_api import load_schedule 
import argparse
import config.settings

define('port',default=4000,help='run the server on the given port',type=int)
#define('log_file_prefix',default='board.log',help='log file name',type=str)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class MainHandler(BaseHandler):
    
    def get(self):
        self.set_cookie("_xsrf",self.xsrf_token)
        self.render("board.html")

class Get_DB_Data(BaseHandler):
    def get(self):
        display_content = load_schedule()
        if display_content['result'] == 'fail':
            pass
        elif display_content['display_type'] == 'image':
            self.render('show-image.html',img_info=display_content)
        elif display_content['display_type'] == 'text':
            from tornado.template import Loader
            loader = Loader('template')
            print(loader.load('show-text.html').generate(text_info=display_content))
            self.render('show-text.html', text_info=display_content)
        elif display_content['display_type'] == 'news':
            self.render('show-news.html', news_info=display_content)

def main():

    base_dir = os.path.dirname(__file__)
    settings = {
        "cookie_secret": config.settings.board['cookie_secret'],
        "template_path":os.path.join(base_dir,"template"),
        "static_path":os.path.join(base_dir,"static"),
        "thumbnail_path":os.path.join(base_dir,"thumbnail"),
        "debug":True,
    }
    application = tornado.web.Application([
        tornado.web.url(r"/",MainHandler,name="main"),
        tornado.web.url(r"/db_schedule",Get_DB_Data),
    ],**settings)
    http_server = tornado.httpserver.HTTPServer(application)

    http_server.listen(options.port)

    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
