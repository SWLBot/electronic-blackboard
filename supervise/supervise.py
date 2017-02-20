from sendgmail import sendgmail
from time import sleep
import os.path


def main():
	shutdown = 0
	error_dir_txt = "../static/log/impossible_error.txt"
	setting_dir_txt = "../setting.txt"
	file_pointer = ""
	file_pointer2 = ""
	last_line_count = 0
	small_bug = 1
	middle_bug = 5
	big_bug = 10

	#initial
	with open(error_dir_txt, 'r') as file_pointer :
		last_line_count = sum(1 for line_content in file_pointer)
	

	while shutdown == 0:
		sleep(300)
		file_pointer = open(error_dir_txt, "r")
		line_count = sum(1 for line_content in file_pointer)
		msg_content = ""
		if last_line_count < line_count:
			if last_line_count + small_bug >= line_count:
				msg_content = ("arrange_schedule got "+ str(small_bug) +" error last 5 minute \r\n")
			elif last_line_count + middle_bug >= line_count:
				msg_content = ("arrange_schedule got "+ str(middle_bug) +" error last 5 minute \r\n")
			elif last_line_count + big_bug >= line_count:
				msg_content = ("arrange_schedule got "+ str(big_bug) +" error last 5 minute \r\n")
			else :
				msg_content = ("arrange_schedule got more than "+ str(big_bug) +" error last 5 minute \r\n")
				msg_content = (msg_content + "arrange_schedule ceased \r\n")
				shutdown = 1
				content = ""
				with open(setting_dir_txt, 'r') as file_pointer2 :
					content = file_pointer2.read()
				# Replace the target string
				content = content.replace('shutdown 0', 'shutdown 1')
				# Write the file out again
				with open(setting_dir_txt, 'w') as file_pointer2:
					file_pointer2.write(content)
			sendgmail(['FROM_BOT'],['icecat2012@gmail.com'], [''], [''], 'supervise', msg_content)
		last_line_count = line_count
		file_pointer.close()
	sleep(3)
	return 1


if __name__ == "__main__":
	main()
