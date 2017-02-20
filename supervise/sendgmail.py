import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
#msg_content can be html format

def sendgmail(receiver_name, To_email, receiver_name2, cc_email, titlee, msg_content):
	filee = open('token',"r")
	From_email = filee.readline().rstrip('\n')
	token = filee.readline().rstrip('\n')
	filee.close()
	sender_name = 'icecat_bot'
	pure_text = ''
	html_text = msg_content
	
	message = MIMEMultipart('alternative')
	message['From'] = sender_name + ' <' + From_email + '>'
	
	if len(To_email) > 0:	
		for tmp_num in range(len(To_email)) :
			if tmp_num == 0:
				message['To'] = receiver_name[0] + ' <' + To_email[0] + '>'
			else :
				message['To'] += ', ' + receiver_name[tmp_num] + ' <' + To_email[tmp_num] + '>'
	else :
		message['To'] = ''
		
	if len(cc_email) > 0:
		for tmp_num in range(len(cc_email)) :
			if tmp_num == 0:
				message['Cc'] = receiver_name2[0] + ' <' + cc_email[0] + '>'
			else :
				message['Cc'] += ', ' + receiver_name2[tmp_num] + ' <' + cc_email[tmp_num] + '>'
	else :
		message['Cc'] = ''
		
	message['Subject'] = titlee

	# Record the MIME types of both parts - text/plain and text/html.
	part1 = MIMEText(pure_text, 'plain')
	part2 = MIMEText(html_text, 'html')

	# Attach parts into message container.
	# According to RFC 2046, the last part of a multipart message, in this case
	# the HTML message, is best and preferred.
	message.attach(part1)
	message.attach(part2)

	msg_full = message.as_string()

	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(From_email, token)
	server.sendmail(From_email,
					(To_email + cc_email),
					msg_full)
	server.quit()
	return 1