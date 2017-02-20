from mysql import mysql
from datetime import date
from datetime import datetime
from datetime import timedelta
from shutil import copyfile
import os.path

#
def upload_image_insert_db(json_obj):
	return_msg = {}
	return_msg["result"] = "fail"
	try:
		server_dir = json_obj["server_dir"]
		type_id = json_obj["file_type"]
		img_file_dir = json_obj["file_dir"]
		img_start_date = json_obj["start_date"]
		img_end_date = json_obj["end_date"]
		img_start_time = json_obj["start_time"]
		img_end_time = json_obj["end_time"]
		img_display_time = json_obj["display_time"]
		user_id = json_obj["user_id"]
	except:
		return_msg["error"] = "input parameter missing"
		return return_msg

	img_id = ""
	img_file_name = os.path.split(img_file_dir)[1]
	img_new_file_dir = ""
	user_level_low_bound = 100
	#default
	if len(img_start_time)==0:
		img_start_time = "00:00:00"
	if len(img_end_time)==0:
		img_end_time = "23:59:59"

	#connect to mysql
	db = mysql()
	if db.connect() == -1:
		return_msg["error"] = "connect mysql error"
		return return_msg
	
	#check user level
	sql = ("SELECT user_level " \
			+"FROM user " \
			+"WHERE user_id=" + str(user_id))
			
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "mysql sql error1"
		return return_msg
	else:
		try: 
			if pure_result[0][0] < user_level_low_bound:
				db.close()
				return_msg["error"] = "user right is too low"
				return return_msg
		except:
			db.close()
			return_msg["error"] = "no such user id : " + str(user_id)
			return return_msg
	
	#get new file place
	sql = ("SELECT type_dir " \
			+"FROM data_type " \
			+"WHERE type_id=" + str(type_id))
	
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "mysql sql error2"
		return return_msg
	else:
		try:
			img_new_file_dir = os.path.join(server_dir, "static/"+str(pure_result[0][0]))
		except:
			db.close()
			return_msg["error"] = "no such type id : " + str(type_id)
			return return_msg
	
	
	#generate new id
	sql = ("SELECT img_id " \
			+"FROM image_data " \
			+"ORDER BY img_upload_time DESC " \
			+"LIMIT 1")
	
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "mysql sql error3"
		return return_msg
	else:
		try:
			img_id =  str(int(pure_result[0][0][4:]) + 1)
			for length_count in range(10 - len(img_id)):
				img_id = '0' + img_id
			img_id = "imge" + img_id
		except:
			img_id = "imge0000000001"
			#db.close()
			#return_msg["error"] = "no basic image"
			#return return_msg
	

	img_system_name = img_id + os.path.splitext(img_file_name)[1]
	img_thumbnail_name = "thumbnail_" + img_system_name
	img_system_dir = os.path.join(img_new_file_dir, img_system_name)
	try:
		copyfile(img_file_dir, img_system_dir)
		if os.path.isfile(img_file_dir) and os.path.isfile(img_system_dir):
			os.remove(img_file_dir)
	except:
		try:
			if os.path.isfile(img_file_dir) and os.path.isfile(img_system_dir):
				os.remove(img_system_dir)
		except:
			"DO NOTHING"
		db.close()
		return_msg["error"] = "copy or remove file error"
		return return_msg
	
	
	#insert images data to mysql
	sql = "INSERT image_data " \
			+" (`img_id`, `type_id`, `img_system_name`, `img_thumbnail_name`, `img_file_name`, `img_start_date`, `img_end_date`, `img_start_time`, `img_end_time`, `img_display_time`, `user_id`) " \
			+" VALUE " \
			+" ( \"" + img_id + "\", " \
			+ str(type_id) + ", " \
			+ "\"" + img_system_name + "\", " \
			+ "\"" + img_thumbnail_name + "\", " \
			+ "\"" + img_file_name + "\", " \
			+ "\"" + img_start_date + "\", " \
			+ "\"" + img_end_date + "\", " \
			+ "\"" + img_start_time + "\", " \
			+ "\"" + img_end_time + "\", " \
			+ str(img_display_time) + ", " \
			+ str(user_id) + " ) " 
	
	pure_result = db.cmd(sql)
	if pure_result == -1:
		return_msg["error"] = "insert mysql error please check file system " + img_system_dir
		try:
			copyfile(img_system_dir, img_file_dir)
			if os.path.isfile(img_file_dir) and os.path.isfile(img_system_dir):
				os.remove(img_system_dir)
			return_msg["error"] = "insert mysql error please check file system " + img_file_dir
		except:
			"DO NOTHING"
		db.close()
		return return_msg
	
	db.close()

	return_msg["img_id"] = img_id
	return_msg["img_system_dir"] = img_system_dir
	return_msg["img_thumbnail_name"] = img_thumbnail_name
	return_msg["result"] = "success"
	return return_msg
	
	
#
def edit_image_data(json_obj):
	return_msg = {}
	return_msg["result"] = "fail"
	try:
		server_dir = json_obj["server_dir"]
		img_id = json_obj["img_id"]
		type_id = json_obj["file_type"]
		img_start_date = json_obj["start_date"]
		img_end_date = json_obj["end_date"]
		img_start_time = json_obj["start_time"]
		img_end_time = json_obj["end_time"]
		img_display_time = json_obj["display_time"]
		user_id = json_obj["user_id"]
	except:
		return_msg["error"] = "input parameter missing"
		return return_msg

	user_level_low_bound = 100
	user_level_high_bound = 10000
	img_type_id = 0
	
	#connect to mysql
	db = mysql()
	if db.connect() == -1:
		return_msg["error"] = "connect mysql error"
		return return_msg
	
	#check user level
	sql = ("SELECT user_level " \
			+"FROM user " \
			+"WHERE user_id=" + str(user_id))
			
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "mysql sql error"
		return return_msg
	else:
		try: 
			user_level = pure_result[0][0]
			if user_level < user_level_low_bound:
				db.close()
				return_msg["error"] = "user right is too low"
				return return_msg
			
			sql = ("SELECT user_id, type_id " \
					+"FROM image_data " \
					+"WHERE img_id=\"" + img_id + "\"")
					
			pure_result = db.query(sql)
			if pure_result == -1:
				db.close()
				return_msg["error"] = "mysql sql error"
				return return_msg
			else:
				try:
					if pure_result[0][0] != user_id and user_level < user_level_high_bound:
						db.close()
						return_msg["error"] = "can not modify other user image "
						return return_msg
					img_type_id = pure_result[0][1]
				except:
					db.close()
					return_msg["error"] = "no such image id : " + img_id
					return return_msg
		except:
			db.close()
			return_msg["error"] = "no such user id : " + str(user_id)
			return return_msg
	
	
	#check if we need to move the file
	old_dir = ""
	new_dir = ""
	if img_type_id == type_id:
		"DO NOTHING"
	else :
		#get img_system_name
		sql = ("SELECT img_system_name " \
				+"FROM image_data " \
				+"WHERE img_id=\"" + img_id + "\"")
				
		pure_result = db.query(sql)
		if pure_result == -1:
			db.close()
			return_msg["error"] = "mysql sql error"
			return return_msg
		else:
			try: 
				old_dir = pure_result[0][0]
				new_dir = pure_result[0][0]
			except:
				db.close()
				return_msg["error"] = "no such image id : " + img_id
				return return_msg
		
		#get old image type dir
		sql = ("SELECT type_dir " \
				+"FROM data_type " \
				+"WHERE type_id=" + str(img_type_id))
				
		pure_result = db.query(sql)
		if pure_result == -1:
			db.close()
			return_msg["error"] = "mysql sql error"
			return return_msg
		else:
			try: 
				old_dir = pure_result[0][0] + old_dir
			except:
				db.close()
				return_msg["error"] = "no such image type : " + str(img_type_id)
				return return_msg
				
		#get new image type dir		
		sql = ("SELECT type_dir " \
				+"FROM data_type " \
				+"WHERE type_id=" + str(type_id))
				
		pure_result = db.query(sql)
		if pure_result == -1:
			db.close()
			return_msg["error"] = "mysql sql error"
			return return_msg
		else:
			try: 
				new_dir = pure_result[0][0] + new_dir
			except:
				db.close()
				return_msg["error"] = "no such image type : " + str(type_id)
				return return_msg
		#check if we need to move the file
		if old_dir == new_dir:
			"DO NOTHING"
		else :
			try:
				old_dir = os.path.join(server_dir,"static/"+old_dir)
				new_dir = os.path.join(server_dir,"static/"+new_dir)
				copyfile(old_dir, new_dir)
				if os.path.isfile(old_dir) and os.path.isfile(new_dir):
					os.remove(old_dir)
			except:
				try:
					if os.path.isfile(old_dir) and os.path.isfile(new_dir):
						os.remove(new_dir)
				except:
					"DO NOTHING"
				db.close()
				return_msg["error"] = "move file error1 : " + old_dir
				return return_msg
	
	#start to modify mysql
	sql = ("UPDATE image_data " \
			+" SET type_id=" + str(type_id) + ", " \
			+" img_start_date=\"" + img_start_date + "\", " \
			+" img_end_date=\"" + img_end_date + "\", " \
			+" img_start_time=\"" + img_start_time + "\", " \
			+" img_end_time=\"" + img_end_time + "\", " \
			+" img_display_time=" + str(img_display_time) + ", " \
			+" img_last_edit_user_id=\"" + str(user_id) + "\" " \
			+" WHERE img_id=\"" + img_id + "\"")


	if db.cmd(sql) == -1:
		try:
			copyfile(new_dir, old_dir)
			if os.path.isfile(old_dir) and os.path.isfile(new_dir):
				os.remove(new_dir)
		except:
			try:
				if os.path.isfile(old_dir) and os.path.isfile(new_dir):
					os.remove(old_dir)
			except:
				db.close()
				return_msg["error"] = "move file error : duplicate files : " + old_dir
				return return_msg
			db.close()
			return_msg["error"] = "move file error2 : " + new_dir
			return return_msg
		db.close()
		return_msg["error"] = "update mysql error"
		return return_msg

	db.close()
	return_msg["result"] = "success"
	return return_msg

#
def upload_text_insert_db(json_obj):
	return_msg = {}
	return_msg["result"] = "fail"
	server_dir = ""
	type_id = 1
	text_start_date = ""
	text_end_date = ""
	text_start_time = ""
	text_end_time = ""
	text_display_time = 5
	user_id = ""
	try:
		server_dir = json_obj["server_dir"]
		type_id = json_obj["file_type"]
		text_start_date = json_obj["start_date"]
		text_end_date = json_obj["end_date"]
		text_start_time = json_obj["start_time"]
		text_end_time = json_obj["end_time"]
		text_display_time = json_obj["display_time"]
		user_id = json_obj["user_id"]
	except:
		return_msg["error"] = "input parameter missing"
		return return_msg

	text_id = ""
	system_file_dir = ""
	text_system_name = ""
	user_level_low_bound = 100
	#default
	if len(text_start_time)==0:
		text_start_time = "00:00:00"
	if len(text_end_time)==0:
		text_end_time = "23:59:59"

	#connect to mysql
	db = mysql()
	if db.connect() == -1:
		return_msg["error"] = "connect mysql error"
		return return_msg
	
	#check user level
	sql = ("SELECT user_level " \
			+"FROM user " \
			+"WHERE user_id=" + str(user_id))
			
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "mysql sql error1"
		return return_msg
	else:
		try: 
			if pure_result[0][0] < user_level_low_bound:
				db.close()
				return_msg["error"] = "user right is too low"
				return return_msg
		except:
			db.close()
			return_msg["error"] = "no such user id : " + str(user_id)
			return return_msg

	#generate new id
	sql = ("SELECT text_id " \
			+"FROM text_data " \
			+"ORDER BY text_upload_time DESC " \
			+"LIMIT 1")
	
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "mysql sql error3"
		return return_msg
	else:
		try:
			text_id =  int(pure_result[0][0][4:]) + 1
			text_id = "text" + "{0:010d}".format(text_id)
		except:
			text_id = "text0000000001"
			#db.close()
			#return_msg["error"] = "no basic image"
			#return return_msg
	
	#get file place
	sql = ("SELECT type_dir " \
			+"FROM data_type " \
			+"WHERE type_id=" + str(type_id))
	
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "mysql sql error2"
		return return_msg
	else:
		try:
			text_system_name = text_id + ".txt"
			system_file_dir = os.path.join(server_dir, "static/"+str(pure_result[0][0]))
			system_file_dir = os.path.join(system_file_dir, text_system_name)
		except:
			db.close()
			return_msg["error"] = "no such type id : " + str(type_id)
			return return_msg
	
	#insert images data to mysql
	sql = "INSERT text_data " \
			+" (`text_id`, `type_id`, `text_system_name`, `text_file_name`, `text_start_date`, `text_end_date`, `text_start_time`, `text_end_time`, `text_display_time`, `user_id`) " \
			+" VALUE " \
			+" ( \"" + text_id + "\", " \
			+ str(type_id) + ", " \
			+ "\"" + text_system_name + "\", " \
			+ "\"" + text_id + "\", " \
			+ "\"" + text_start_date + "\", " \
			+ "\"" + text_end_date + "\", " \
			+ "\"" + text_start_time + "\", " \
			+ "\"" + text_end_time + "\", " \
			+ str(text_display_time) + ", " \
			+ str(user_id) + " ) " 
	
	pure_result = db.cmd(sql)
	if pure_result == -1:
		return_msg["error"] = "insert mysql error"
		db.close()
		return return_msg
	
	db.close()

	return_msg["text_id"] = text_id
	return_msg["text_system_dir"] = system_file_dir
	return_msg["result"] = "success"
	return return_msg
	














