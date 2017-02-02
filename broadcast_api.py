from mysql_class import mysql
from random import sample
from datetime import date
from datetime import datetime
from datetime import timedelta
import os.path

#The API connect mysql and arrange the schedule and write it to the schedule.txt
def arrange_schedule(json_obj):
	schedule_dir = json_obj["schedule_dir"]
	arrange_mode = json_obj["arrange_mode"]
	mode_condition = []
	if "mode_condition" in json_obj:
		mode_condition = json_obj["mode_condition"]
	return_msg = {}

	update_fail = False
	find_fail = False
	deal_result = []
	
	file_name = "sql_token"
	
	#connect to mysql
	db = mysql()
	if db.connect(file_name) == -1:
		return_msg["num"] = 0
		return return_msg
	
	#update expire data berfore query
	sql = ("UPDATE image_data " \
			+"SET img_is_expire=1 " \
			+"WHERE TO_DAYS(NOW())-TO_DAYS(img_end_date)>0 " \
			+"or (TO_DAYS(NOW())-TO_DAYS(img_end_date)=0 and TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s'))-TIME_TO_SEC(img_end_time)>0)")
	
	if db.cmd(sql) == -1:
		update_fail = True
	
	#find images that may be schedule
	if arrange_mode == 1 or arrange_mode == 2:
		sql = "SELECT a0.img_id, a0.img_system_name, a0.img_display_time, a1.type_dir, a0.img_end_time FROM " \
			+" (SELECT img_id, type_id, img_system_name, img_display_time, img_end_time " \
			+" FROM image_data " \
			+" WHERE img_is_expire=0 and TO_DAYS(NOW())-TO_DAYS(img_start_date)>=0 " \
			+" and TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(img_start_time) and TIME_TO_SEC(img_end_time)) a0 " \
			+" LEFT JOIN (SELECT type_id, type_dir FROM image_type) a1 on a0.type_id=a1.type_id "
	elif arrange_mode == 3 or arrange_mode == 4:
		sql = "SELECT a0.img_id, a0.img_system_name, a0.img_display_time, a1.type_dir, a0.img_end_time FROM " \
			+" (SELECT img_id, type_id, img_system_name, img_display_time, img_end_time " \
			+" FROM image_data " \
			+" WHERE img_is_expire=0 "
		for content in mode_condition:
			sql = sql + " and type_id=" + content + " "
		sql = sql + " and TO_DAYS(NOW())-TO_DAYS(img_start_date)>=0 " \
			+" and TIME_TO_SEC(DATE_FORMAT(NOW(), '%H:%i:%s')) between TIME_TO_SEC(img_start_time) and TIME_TO_SEC(img_end_time)) a0 " \
			+" LEFT JOIN (SELECT type_id, type_dir FROM image_type "
		for content_num in range(len(mode_condition)):
			if content_num == 0:
				sql = sql + " WHERE type_id=" + mode_condition[content_num] + " "
			else :
				sql = sql + " and type_id=" + mode_condition[content_num] + " "
		sql = sql + ") a1 on a0.type_id=a1.type_id "
	#print(sql)
	
	pure_result = db.query(sql)
	if pure_result == -1:
		find_fail = True
	else:
		#restruct results of query
		for result_row in pure_result:
			deal_result.append([result_row[0], (result_row[3] + result_row[1]), result_row[2], result_row[4]])
			#                     img_id,            dir and file name,         display time,     end time
     
	#display in loop or random display
	if arrange_mode == 1:
		"DO NOTHING"
	elif arrange_mode == 2:
		if len(deal_result)>20:
			deal_result = sample(deal_result, 20)
	elif arrange_mode == 3:
		"DO NOTHING"
	elif arrange_mode == 4:
		if len(deal_result)>20:
			deal_result = sample(deal_result, 20)
	
	#update img display count and write to schedule
	date_now = date.today()
	schedule_file = ("broad_" + str(date_now.year) + "_" + str(date_now.month) + "_" + str(date_now.day) + ".txt")
	schedule_file = os.path.join(schedule_dir,("static/log/"+schedule_file))

	add_num = 0
	try:
		if not os.path.isfile(schedule_file) :
			file_pointer = open(schedule_file, "w")
		else :
			file_pointer = open(schedule_file, "a")
		if len(deal_result)>0:
			for tt in range(len(deal_result)):
				sql = "UPDATE image_data SET img_display_count=img_display_count+1 WHERE img_id='"+deal_result[tt][0]+"'"
				if db.cmd(sql) == -1:
					update_fail = True
				else :
					int_str1 = str(deal_result[tt][2])
					int_str2 = str(deal_result[tt][3])
					write_str = ("0 " + deal_result[tt][0] + " " + deal_result[tt][1] + " " + int_str1 + " " + int_str2 + " \n")
					#                     image_id,                   img_dir,            display time,     expire_time
					file_pointer.write(write_str)
					add_num+=1
		file_pointer.close()
	except:
		"Do noting"
	
	return_msg["num"] = add_num
	return return_msg


#The API load schedule.txt and find out the first image which has not print and the time limit still allow
def load_schedule(json_obj):
	schedule_dir = json_obj["schedule_dir"]
	return_msg = {}

	date_now = date.today()
	schedule_file = ("broad_" + str(date_now.year) + "_" + str(date_now.month) + "_" + str(date_now.day) + ".txt")
	new_file = ("new_" + schedule_file)
	old_file = ("old_" + schedule_file)
	schedule_file = os.path.join(schedule_dir,("static/log/"+schedule_file))
	new_file = os.path.join(schedule_dir,("static/log/"+new_file))
	old_file = os.path.join(schedule_dir,("static/log/"+old_file))

	if os.path.isfile(new_file) :
		try:
			if os.path.isfile(old_file) :
				os.remove(old_file)
			os.rename(schedule_file, old_file)
			os.rename(new_file,schedule_file)
		except:
			"Do noting"
	

	try:
		file_pointer = open(schedule_file, "r+")
	except:
		return_msg["next_img"] = "img/0.jpg"
		return_msg["limit_time"] = 5
		return_msg["enough_schedule"] = 0
		return return_msg
	

	pure_data = ""
	deal_data = ""
	char_count = 0
	lock_count = []
	already_get_target = 0
	check_less_line = 0
	enough_less_line = 0
	for line in file_pointer:
		pure_data = ""
		pure_data = line.rstrip('\n').split(' ')
		if pure_data[0] is '0':
			if already_get_target == 0:
				limit_time = pure_data[4].split(":")
				now_time = datetime.now()
				time1 = timedelta(hours=int(limit_time[0]), minutes=int(limit_time[1]), seconds=int(limit_time[2]))
				time2 = timedelta(hours=now_time.hour, minutes=now_time.minute, seconds=now_time.second)
				time3 = timedelta(hours=0, minutes=0, seconds=0)
				
				if (time1 - time2) > time3:
					lock_count.append(char_count)
					already_get_target = 1
					deal_data = pure_data
				elif (time1 - time2) <= time3:
					lock_count.append(char_count)
			else :
				check_less_line = check_less_line + 1
				if check_less_line > 10:
					enough_less_line = 1
					break
		char_count+=(len(line))
	if len(lock_count) > 0 :
		for seek_num in lock_count :
			file_pointer.seek(seek_num, 0)
			file_pointer.write('1')
	file_pointer.close()

	try:
		return_msg["next_img"] = deal_data[2]
		return_msg["limit_time"] = int(deal_data[3])
		return_msg["enough_schedule"] = int(enough_less_line)
	except:
		return_msg["next_img"] = "img/0.jpg"
		return_msg["limit_time"] = 5
		return_msg["enough_schedule"] = 0
		return return_msg

	return return_msg

#the api can only edit furtre schedule. 
#It can edit schedule not to print image by setting img_check=0 or edit furtre schedule to print new image.
def edit_schedule(json_obj):
	schedule_dir = json_obj["schedule_dir"]
	next_img = json_obj["next_img"]
	img_check = json_obj["img_check"]
	img_id = json_obj["img_id"]
	img_dir = json_obj["img_dir"]
	img_time = json_obj["img_time"]
	img_end_time = json_obj["img_end_time"]
	return_msg = {}


	#can not edit scheduling next item
	if next_img <= 1:
		return_msg["result"] = "error next_img <= 1"
		return return_msg

	date_now = date.today()
	schedule_file = ("broad_" + str(date_now.year) + "_" + str(date_now.month) + "_" + str(date_now.day) + ".txt")
	new_file = ("new_" + schedule_file)
	schedule_file = os.path.join(schedule_dir,("static/log/"+schedule_file))
	new_file = os.path.join(schedule_dir,("static/log/"+new_file))
	try:
		file1 = open(schedule_file, "r")
		file2 = open(new_file, "w")

		pure_data = ""
		deal_data = (str(img_check) + ' ' + img_id + ' ' + img_dir + ' ' + str(img_time) + ' ' + img_end_time + '\n')
		pass_count = 0
		for line in file1:
			pure_data = ""
			pure_data = line.rstrip('\n').split(' ')
			if pure_data[0] is '0':
				pass_count+=1
				if pass_count == next_img:
					file2.write(deal_data)
				else :
					file2.write(line)
			else :
				file2.write(line)
	
		file1.close()
		file2.close()
	except:
		try:
			if os.path.isfile(new_file) :
				os.remove(new_file)
		except:
			"Do nothing"
		return_msg["result"] = "error"
		return return_msg

	return_msg["result"] = "scuess"
	return return_msg








