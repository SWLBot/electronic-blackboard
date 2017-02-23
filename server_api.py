from mysql import mysql
from datetime import date
from datetime import datetime
from datetime import timedelta
from shutil import copyfile
import os
import os.path
import shutil
import bcrypt

#
def check_user_level(json_obj):
	return_msg = {}
	return_msg["result"] = "fail"
	user_id = 0
	user_level = 0
	compare_level = []
	compare_ans = []
	try:
		user_id = json_obj["user_id"]
		compare_level = json_obj["compare_level"]
	except:
		return_msg["error"] = "input parameter missing"
		return return_msg

	#connect to mysql
	db = mysql()
	if db.connect() == -1:
		return_msg["error"] = "connect mysql error"
		return return_msg
	
	#check user level
	sql = "SELECT user_level FROM user WHERE user_id=" + str(user_id)
			
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "mysql sql error"
		return return_msg
	else:
		try:
			user_level = int(pure_result[0][0])
		except:
			db.close()
			return_msg["error"] = "no such user id : " + str(user_id)
			return return_msg

	for num1 in range(len(compare_level)):
		if int(compare_level[num1]) >= user_level:
			compare_ans.append("pass")
		else :
			compare_ans.append("fail")

	db.close()

	return_msg["compare_ans"] = compare_ans
	return_msg["result"] = "success"
	return return_msg

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
		return_msg["error"] = "mysql sql error"
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
		return_msg["error"] = "mysql sql error"
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
		return_msg["error"] = "mysql sql error"
		return return_msg
	else:
		try:
			img_id =  int(pure_result[0][0][4:]) + 1
			img_id = "imge" + "{0:010d}".format(img_id)
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
			#check self image
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
				return_msg["error"] = "move file error : " + old_dir
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
			return_msg["error"] = "move file error : " + new_dir
			return return_msg
		db.close()
		return_msg["error"] = "update mysql error"
		return return_msg

	db.close()
	return_msg["result"] = "success"
	return return_msg


#never debug this function
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
		return_msg["error"] = "mysql sql error"
		return return_msg
	else:
		try: 
			if int(pure_result[0][0]) < user_level_low_bound:
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
		return_msg["error"] = "mysql sql error"
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
		return_msg["error"] = "mysql sql error"
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
			+" (`text_id`, `type_id`, `text_system_name`, `text_invisible_title`, `text_start_date`, `text_end_date`, `text_start_time`, `text_end_time`, `text_display_time`, `user_id`) " \
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
	

#
def edit_text_data(json_obj):
	return_msg = {}
	return_msg["result"] = "fail"
	server_dir = ""
	text_id = ""
	invisible_title = ""
	type_id = 0
	text_start_date = ""
	text_end_date = ""
	text_start_time = ""
	text_end_time = ""
	text_display_time = 5
	user_id = ""
	try:
		server_dir = json_obj["server_dir"]
		text_id = json_obj["text_id"]
		invisible_title = json_obj["invisible_title"]
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

	user_level_low_bound = 100
	user_level_high_bound = 10000
	text_type_id = 0
	
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
			user_level = int(pure_result[0][0])
			if user_level < user_level_low_bound:
				db.close()
				return_msg["error"] = "user right is too low"
				return return_msg
			#check self text
			sql = ("SELECT user_id, type_id " \
					+"FROM text_data " \
					+"WHERE text_id=\"" + text_id + "\"")
					
			pure_result = db.query(sql)
			if pure_result == -1:
				db.close()
				return_msg["error"] = "mysql sql error"
				return return_msg
			else:
				try:
					if pure_result[0][0] != user_id and user_level < user_level_high_bound:
						db.close()
						return_msg["error"] = "can not modify other user text"
						return return_msg
					text_type_id = int(pure_result[0][1])
				except:
					db.close()
					return_msg["error"] = "no such text id : " + text_id
					return return_msg
		except:
			db.close()
			return_msg["error"] = "no such user id : " + str(user_id)
			return return_msg
	
	
	
	old_dir = ""
	new_dir = ""
	#get text_system_name
	sql = ("SELECT text_system_name " \
			+"FROM text_data " \
			+"WHERE text_id=\"" + text_id + "\"")
			
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
			return_msg["error"] = "no such text id : " + text_id
			return return_msg
	
	#get old text type dir
	sql = ("SELECT type_dir " \
			+"FROM data_type " \
			+"WHERE type_id=" + str(text_type_id))
			
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
			return_msg["error"] = "no such text type : " + str(text_type_id)
			return return_msg

	#check if we need to move the file
	if text_type_id == type_id:
		old_dir = os.path.join(server_dir,"static/"+old_dir)
		new_dir = old_dir
	else :	
		#get new text type dir		
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
				return_msg["error"] = "no such text type : " + str(type_id)
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
				return_msg["error"] = "move file error : " + old_dir
				return return_msg
	
	#start to modify mysql
	sql = ("UPDATE text_data " \
			+" SET type_id=" + str(type_id) + ", " \
			+" text_invisible_title='" + invisible_title + "', "\
			+" text_start_date=\"" + text_start_date + "\", " \
			+" text_end_date=\"" + text_end_date + "\", " \
			+" text_start_time=\"" + text_start_time + "\", " \
			+" text_end_time=\"" + text_end_time + "\", " \
			+" text_display_time=" + str(text_display_time) + ", " \
			+" text_last_edit_user_id=\"" + str(user_id) + "\" " \
			+" WHERE text_id=\"" + text_id + "\"")

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
			return_msg["error"] = "move file error : " + new_dir
			return return_msg
		db.close()
		return_msg["error"] = "update mysql error"
		return return_msg

	db.close()
	return_msg["result"] = "success"
	return_msg["text_system_dir"] = new_dir
	return return_msg


#
def delete_image_or_text_data(json_obj):
	return_msg = {}
	return_msg["result"] = "fail"
	server_dir = ""
	target_id = ""
	user_id = ""
	target_dir = ""
	trash_dir = ""
	target_type_id = 0
	user_level_low_bound = 100
	user_level_high_bound = 10000
	try:
		server_dir = json_obj["server_dir"]
		target_id = json_obj["target_id"]
		user_id = json_obj["user_id"]
	except:
		return_msg["error"] = "input parameter missing"
		return return_msg

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
			user_level = int(pure_result[0][0])
			if user_level < user_level_low_bound:
				db.close()
				return_msg["error"] = "user right is too low"
				return return_msg
			#check self data and get type_id
			if target_id[0:4] == "imge":
				sql = "SELECT type_id, img_system_name, user_id FROM image_data WHERE img_id='" + target_id + "'"
			elif target_id[0:4] == "text":
				sql = "SELECT type_id, text_system_name, user_id FROM text_data WHERE text_id='" + target_id + "'"
			else :
				db.close()
				return_msg["error"] = "target id type error"
				return return_msg
			pure_result = db.query(sql)
			if pure_result == -1:
				db.close()
				return_msg["error"] = "mysql sql error"
				return return_msg
			else:
				try:
					if pure_result[0][2] != user_id and user_level < user_level_high_bound:
						db.close()
						return_msg["error"] = "can not modify other user image or text"
						return return_msg
					target_type_id =  int(pure_result[0][0])
					target_dir = pure_result[0][1]
				except:
					db.close()
					return_msg["error"] = "no such target id : " + str(target_id)
					return return_msg
		except:
			db.close()
			return_msg["error"] = "no such user id : " + str(user_id)
			return return_msg
	
	#get file place
	sql = "SELECT type_dir FROM data_type WHERE type_id=" + str(target_type_id)
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "mysql sql error"
		return return_msg
	else:
		try:
			trash_dir = os.path.join(server_dir, "static/img/trash_data/"+target_dir)
			system_file_dir = os.path.join(server_dir, "static/"+str(pure_result[0][0]))
			target_dir = os.path.join(system_file_dir, target_dir)
		except:
			db.close()
			return_msg["error"] = "no such type id : " + str(type_id)
			return return_msg

	#check trash_data 
	if not os.path.exists(os.path.split(trash_dir)[0]):
		try:
			os.makedirs(os.path.split(trash_dir)[0])
		except:
			db.close()
			return_msg["error"] = "no trash_data folder"
			return return_msg

	#move to trash
	if os.path.isfile(target_dir):
		try:
			shutil.move(target_dir, trash_dir)
		except:
			db.close()
			return_msg["error"] = "move fail"
			return return_msg

	if target_id[0:4] == "imge":
		sql = "UPDATE image_data SET img_is_delete=1, img_last_edit_user_id="+str(user_id)+" WHERE img_id='"+ target_id + "'"
	elif target_id[0:4] == "text":
		sql = "UPDATE text_data SET text_is_delete=1, text_last_edit_user_id="+str(user_id)+" WHERE text_id='"+target_id+"'"
	else :
		sql = ""
	if db.cmd(sql) == -1:
		db.close()
		return_msg["error"] = "update fail"
		return return_msg

	
	db.close()

	return_msg["result"] = "success"
	return return_msg
	

def add_new_data_type(json_obj):
	return_msg = {}
	return_msg["result"] = "fail"
	type_name = json_obj['type_name']
	db = mysql()
	if db.connect() == -1:
		return_msg["error"] = "connect mysql error"
		return return_msg

	sql = "SELECT count(*) FROM data_type WHERE type_name = \""+type_name+"\""
	if db.query(sql)[0][0] == 1:
		return_msg["error"] = "Type name has existed"
		return return_msg

	sql = "INSERT INTO data_type (type_name,type_dir) VALUES (\"" \
		+type_name+"\",\"" \
		+type_name+"/\")"
	if db.cmd(sql) == -1:
		db.close()
		return_msg["error"] = "add type fail"
		return return_msg

	db.close()

	if not os.path.exists("static/"+type_name):
		os.makedirs("static/"+type_name)

	return_msg["result"] = "success"
	return return_msg


#
def change_password(json_obj):
	return_msg = {}
	return_msg["result"] = "fail"
	user_id = 0
	old_password = ""
	new_password = ""
	try:
		user_id = json_obj["user_id"]
		old_password = json_obj["old_password"]
		new_password = json_obj["new_password"]
	except:
		return_msg["error"] = "input parameter missing"
		return return_msg

	#connect to mysql
	db = mysql()
	if db.connect() == -1:
		return_msg["error"] = "connect mysql error"
		return return_msg
	
	#check user
	sql = "SELECT user_password FROM user WHERE user_id=" + str(user_id)
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "mysql sql error"
		return return_msg
	else:
		hashed_key = ""
		try:
			hashed_key = pure_result[0][0].encode('utf-8')
			if bcrypt.checkpw(old_password.encode('utf-8'),hashed_key):
				# old password correct
				hashed_key = bcrypt.hashpw(new_password.encode('utf-8'),bcrypt.gensalt())
				sql = "UPDATE user SET user_password=" + str(hashed_key)[1:] + " WHERE user_id=" + str(user_id)
				if db.cmd(sql) == -1:
					db.close()
					return_msg["error"] = "update error"
					return return_msg
			else:
				db.close()
				return_msg["error"] = "old password incorrect"
				return return_msg
		except:
			db.close()
			return_msg["error"] = "no such user id : " + str(user_id)
			return return_msg
	
	db.close()

	return_msg["result"] = "success"
	return return_msg


