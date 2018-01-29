# Electronic Blackboard [![Build Status](https://travis-ci.org/SWLBot/electronic-blackboard.svg?branch=master)](https://travis-ci.org/SWLBot/electronic-blackboard) 

This project is a electronic bulletin board of broadcasting images and announcement templates by web browser. The system provides broadcast scheduling, wieldy user interface for uploading and mutiple automated functions.  

The functions Electronic-Blackboard included are as follows
* Customized scheduling mode selection
* CWB crawler for weather radar image
* Google calendar
* Announcement template
* etc

## Quick start
### Prerequisities
* docker

### Starting up docker
```
./docker/run.sh
[sudo] password for <username>: 
root@XXXXXXXXXX:/home/EB# 
```
### Testing
`root@XXXXXXXXXX:/home/EB# ./docker/test.sh`
if success, it should print
```
============================= test session starts ==============================
platform linux -- Python 3.4.6, pytest-3.1.3, py-1.4.33, pluggy-0.4.0
rootdir: /home/travis/build/SWLBot/electronic-blackboard, inifile:
plugins: ordering-0.5
 ...

=================== XX passed, XX warnings in XXXX seconds ====================
```
### Running up 
```
root@XXXXXXXXXX:/home/EB# python3 env_init.py
...
root@XXXXXXXXXX:/home/EB# ./autorun.sh
root@XXXXXXXXXX:/home/EB# tmux ls
blackboard: 4 windows (created XXXXXX ) [135x34]
```
Now you can use your browser connect to following addresses:
#### backend dashboard
*Default* 
Account: admin
Password: admin
http://localhost:3000/
#### frontend display
http://localhost:4000/
## Functional test
### Firefox
1. Install geckodriver
```
$ wget https://github.com/mozilla/geckodriver/releases/download/v0.16.1/geckodriver-v0.16.1-linux64.tar.gz
$ sudo sh -c 'tar -x geckodriver -zf geckodriver-v0.16.1-linux64.tar.gz -O > /usr/bin/geckodriver'
$ sudo chmod +x /usr/bin/geckodriver
$ rm geckodriver-v0.16.1-linux64.tar.gz
```
2. Run test
```
$ pytest functional_test
```
