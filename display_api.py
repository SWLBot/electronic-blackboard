from mysql import mysql
from datetime import date
from datetime import datetime
from datetime import timedelta
import os.path

#The API connect mysql and list all upload images' information
def display_image(argu_user):
	user_name = argu_user

	return_msg = {}
	return_msg_list = []

	
	#connect to mysql
	db = mysql()
	if db.connect() == -1:
		return_msg["error"] = "Cannot connect database"
		return return_msg
	

	#display image data from the same user
	sql = "SELECT img_id, img_upload_time, img_file_name, img_start_time, img_end_time, img_start_date, img_end_date, type_id, img_thumbnail_name, img_display_time, img_display_count " \
			+ "FROM image_data WHERE user_id in ( select user_id from user where user_name = \""+user_name+"\")"



	if db.cmd(sql) == -1:
		db.close()
		return_msg["error"] = "sql error 1"
		return return_msg
	
	
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "sql error 2"
		return return_msg
	else:
		#restruct results of query
		for result_row in pure_result:
			return_msg_list.append([result_row[0],result_row[1],result_row[2],result_row[3],result_row[4],result_row[5],result_row[6],result_row[7],result_row[8],result_row[9],result_row[10]])
			#                   img_id, img_upload_time, img_file_name, img_start_time, img_end_time, img_start_date, img_end_date, type_id, img_thumbnail_name, img_display_time, img_display_count


	'''
	if len(deal_result)>0:
		for i in range(len(deal_result)):
			return_msg_list.append({'img_id':deal_result[i][0], 'img_upload_time':deal_result[i][1], 'img_file_name':deal_result[i][2], 'img_start_time':deal_result[i][3], 'img_end_time':deal_result[i][4], 'img_start_date':deal_result[i][5], 'img_end_date':deal_result[i][6], 'type_id':int(deal_result[i][7]), 'img_thumbnail_name':deal_result[i][8], 'img_display_time':int(deal_result[i][9]), 'img_display_count':int(deal_result[i][10])})
			
	
			return_msg["img_id"] = deal_result[i][0]
			return_msg["img_upload_time"] = deal_result[i][1]
			return_msg["img_file_name"] = deal_result[i][2]
			return_msg["img_start_time"] = deal_result[i][3]
			return_msg["img_end_time"] = deal_result[i][4]
			return_msg["img_start_date"] = deal_result[i][5]
			return_msg["img_end_date"] = deal_result[i][6]
			return_msg["type_id"] = int(deal_result[i][7])
			return_msg["img_thumbnail_name"] = deal_result[i][8]
			return_msg["img_display_time"] = int(deal_result[i][9])
			return_msg["img_display_count"] = int(deal_result[i][10])
			return_msg["result"] = "success"
			return_msg_list.append(return_msg.copy())
			print (return_msg["img_id"])
	'''
	
	db.close()

	return return_msg_list




def display_data_type(type_id=None, type_name=None, type_dir=None, type_weight=None):
	current_type_id = type_id
	current_type_name = type_name
	current_type_dir = type_dir
	current_type_weight = type_weight


	return_msg = {}
	return_msg_list = []

	deal_result = []
	
	#connect to mysql
	db = mysql()
	if db.connect() == -1:
		return_msg["error"] = "Cannot connect database"
		return return_msg
	

	if current_type_id :
		sql = "SELECT * FROM data_type WHERE type_id = \""+str(current_type_id)+"\""
	elif current_type_name :
		sql = "SELECT * FROM data_type WHERE type_name = \""+current_type_name+"\""
	elif current_type_dir :
		sql = "SELECT * FROM data_type WHERE type_dir = \""+current_type_dir+"\""
	elif current_type_weight :
		sql = "SELECT * FROM data_type WHERE type_weight = \""+str(current_type_weight)+"\""
	else:
		return_msg["error"] = "Error type select"
		return return_msg


	if db.cmd(sql) == -1:
		db.close()
		return_msg["error"] = "sql error 1"
		return return_msg
	
	
	pure_result = db.query(sql)
	if pure_result == -1:
		db.close()
		return_msg["error"] = "sql error 2"
		return return_msg
	else:
		if current_type_weight:
			for result_row in pure_result:
				return_msg_list.append([result_row[0],result_row[1],result_row[2],result_row[3]])
		else:
			for result_row in pure_result:
				return_msg_list.extend([result_row[0],result_row[1],result_row[2],result_row[3]])
				#                   	id           ,name         ,dir          ,weight


	
	db.close()

	return return_msg_list