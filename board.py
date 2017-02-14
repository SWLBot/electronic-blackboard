import tornado.ioloop
import tornado.web
import os.path
import json
import pprint
from PIL import Image
from broadcast_api import arrange_schedule 
from broadcast_api import load_schedule 
from broadcast_api import edit_schedule 

class BaseHandler(tornado.web.RequestHandler):
	def get_current_user(self):
		return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    
	def get(self):
		base_dir = os.path.dirname(__file__)
		file_dir = os.path.join(base_dir,"static/img")
		files = []
		files.append("0.jpg")
		self.set_cookie("_xsrf",self.xsrf_token)
		self.render("board.html",files=files)


	def post(self):
		self.write("")

class Get_DB_Data(BaseHandler):
	def get(self):
		self.write("")

	def post(self):
		json_obj =  tornado.escape.json_decode(self.request.body)
		response_to_send =  arrange_schedule(json_obj)
		self.write(json.dumps(response_to_send))
		
class Get_txt_Data(BaseHandler):
	def get(self):
		self.render("")

	def post(self):
		json_obj =  tornado.escape.json_decode(self.request.body)
		response_to_send = load_schedule(json_obj)
		self.write(json.dumps(response_to_send))

class Edit_txt_Data(BaseHandler):
	def get(self):
		self.render("")

	def post(self):
		json_obj =  tornado.escape.json_decode(self.request.body)
		response_to_send = edit_schedule(json_obj)
		self.write(json.dumps(response_to_send))


class Application(tornado.web.Application):
	def __init__(self):
		base_dir = os.path.dirname(__file__)

		settings = {
			"cookie_secret": "bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
			"signin_url": "/signin",
			"template_path":os.path.join(base_dir,"template"),
			"static_path":os.path.join(base_dir,"static"),
			"thumbnail_path":os.path.join(base_dir,"thumbnail"),
			"debug":False,
			"xsrf_cookies":True,
			"autoreload":True
		}
		tornado.web.Application.__init__(self,[
			tornado.web.url(r"/",MainHandler,name="main"),
			tornado.web.url(r"/db_schedule",Get_DB_Data),
			tornado.web.url(r"/txt_schedule",Get_txt_Data),
			tornado.web.url(r"/txt_edit",Edit_txt_Data)
			],**settings)

def main():
	Application().listen(4000)
	tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	main()
