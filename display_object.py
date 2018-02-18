
class DisplayObject(object):
	user_id = None
	id = None
	type_id = None
	system_name = ""
	start_date = None
	end_date = None
	start_time = None
	end_time = None
	display_time = None
	server_dir = ""

class DisplayImage(DisplayObject):
	filepath = ""
	file_name = ""
	thumbnail_name = ""

class DisplayText(DisplayObject):
	invisible_title = None