sudo docker run -d --name=EB-mysql --env=MYSQL_ROOT_PASSWORD=mypassword mysql:5.7
echo -e "EB-mysql\nroot\nmypassword\nblackboard" > ../mysql_auth.txt
sudo docker run --name=EB -it --link EB-mysql:mysql -v "$PWD":/home/EB -w /home/EB -p 3000:3000 -p 4000:4000 billy4195/electronic-blackboard bash
