##############################################################################
#                                                        #
#   Deer Detection                                        #
#   Version: Prototpe                                                          #
##############################################################################

# -*- coding: utf-8 -*-
from flask import Flask,render_template,Response,request,redirect,jsonify,url_for
from flask_cors import CORS, cross_origin
import os
import io
import logging
import socketserver
from http import server
from threading import Condition
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from werkzeug.utils import secure_filename
import time
from datetime import *
import time
import math
import subprocess
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
from pycurl import Curl
from urllib.parse import urlencode
import socket
import requests
from ftplib import FTP
from zipfile import ZipFile
import sqlite3 as lite
import cv2
import socket
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
LED_PIN = 17
VUSB_PIN = 17
CHG_PIN = 18
LO_DT_PIN = 27
GPIO.setup(VUSB_PIN, GPIO.IN)
GPIO.setup(CHG_PIN, GPIO.IN)
GPIO.setup(LO_DT_PIN, GPIO.IN)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.output(LED_PIN,GPIO.LOW)

app = Flask(__name__)

CORS(app, supports_credentials=True)
#PathToDatabase = "/home/system/PythonProjects/DeerDetector/static/main.db"
PathToDatabase = "/home/system/DeerDetector/static/main.db"

CurrentPage = 1
PerPage = 25
pages = 0
LastPage = 1
loggedin = 0
message = ""
BatStatus = True

def BatState():
    global BatStatus
    charging = GPIO.input(CHG_PIN)
    low_battery = GPIO.input(LO_DT_PIN)
    external_power = GPIO.input(VUSB_PIN)
    # If it's not charging and the battery is low, shut down the pi
    # Even if the external power is connected, no charging means the power supply is not strong enough
    if not charging and low_battery:
        # Do some stuff before shutting down
        BatStatus = False
        # Shutdown
        print("Shutting down...")
        time.sleep(1)
        os.system("sudo shutdown -h now")

def save_config(data):
    global message
    try:
        con = lite.connect(PathToDatabase)
        cur = con.cursor()  
        cur.execute("UPDATE config SET device_id=?, itemsperpage = ?, pin = ?, save_images = ?, motion_duration = ? WHERE id=?",(data[0],data[1],data[2],data[3],data[4],1))
        con.commit()
        con.close()
        return True
    except lite.Error as error:
        print("SaveConfig: Error: ",error)
        return False
    except Exception as e:
        print("SaveConfig: Exception: ",e)
        return False

def update_version(data):
    global message
    try:
        con = lite.connect(PathToDatabase)
        cur = con.cursor()  
        cur.execute("UPDATE config SET version = ? WHERE id=?",(data,1))
        con.commit()
        con.close()
        return True
    except lite.Error as error:
        print("update_version: Error: ",error)
        return False
    except Exception as e:
        print("update_version: Exception: ",e)
        return False
           
def get_data(TableName, orderby="id",order="ASC",start=0,stop=0):
    con = lite.connect(PathToDatabase)
    con.row_factory = lite.Row
    try:
        cur = con.cursor()
        query = "SELECT * FROM %s" % TableName + " ORDER BY "+orderby+" "+order
        if stop > 0:
            query = "SELECT * FROM %s" % TableName + " ORDER BY "+orderby+" "+order+" LIMIT "+str(start)+","+str(stop)
        print(query)
        cur.execute(query)
        lines = cur.fetchall()
        print(lines)
        con.commit()
        if con:
            con.close()
            if len(lines) > 0:
                return lines
            else:
                return False 
    except Exception as e:
        if con:
            con.rollback()
            print("Error %s:" % e.args[0])
            return False

            
config = get_data("config")
appversion = config[0]['version']
NextVersion = appversion

def convert(seconds): 
    return time.strftime("%H:%M:%S", time.gmtime(seconds)) 

    
def get_ip_address():
    try:
        ip_address = ''
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print(e)
        return False
    
def save_LastIp(ip):
    try:
        con = lite.connect(PathToDatabase)
        cur = con.cursor()  
        cur.execute("UPDATE config SET lastip=? WHERE id=?",(ip,1))
        con.commit()
        con.close() 
        return True
    except lite.Error as error:
        print("Error: ",error)
        #save_event("flow.py save_event: sql error: ",str(error))
        return error
    except Exception as e:
        print("Exception: ",e)
        #save_event("flow.py save_event: Exception: ",str(e))
        return str(e)

start=0
def CalculatePagination(p,query,path,perpage):
    global start
    global CurrentPage
    from models import model
    data = model.MainModel.Paginate(model.MainModel,perpage,query)
    total_records = data[1]
    prev_page = p -1
    next_page = p + 1
    page = p
    pages = total_records / perpage # this is the number of pages
    pages = math.ceil(pages)
    offset = (page-1)*perpage # offset for SQL query
    limit = perpage
    if page == pages:
        limit = total_records
        next_page = pages
    else: 
        perpage # limit for SQL query
    if page < 2:
        prev_page=1
    #print("**********************",page,pages,offset,limit,"**********************")
    prev_path = path+str(prev_page)
    next_path = path+str(next_page)
    PageData =[prev_path,next_path,offset,limit,pages]
    #print(PageData)
    return PageData

def GetRowcount(data):
    x = 0
    for item in data:
        #print(item['step'])
        x+=1
    return x

def WriteData(data):
    try:
        stat = open("/home/system/DeerDetector/stat.txt","w")
        stat.write(data)
        return True
    except Exception as E:
        print("Failure ",E)
        return False
WriteData("off")

def GetData(): #Monitor video status, did we detect something?
    try:
        stat = open("/home/system/DeerDetector/vidstat.txt","r")
        data = stat.read()
        return data
    except Exception as E:
        print("Failure !!!!!!!!!!!!!!!!!!!!!!! ",E)
        return False

detection_status = "off"
sign_status = "off"
sensor1Status = "no"
sensor2Status = "no"
@app.errorhandler(404) 
def invalid_route(e):
	return render_template('404.html',error=e)

@app.route('/login', methods=["POST"])
def Auth():
    global loggedin
    global message
    config = get_data("config")
    pin = request.form['pin']
    if pin == config[0]['pin']:
        loggedin = 1
        message = "Logged In"
    else:
        loggedin = 0
        message = "Login Failed, please try again"
    return redirect('/config')

@app.route('/logout', methods=["GET"])
def logout():
    global loggedin
    global message
    loggedin = 0
    message = "Logged Out"
    return redirect('/')

@app.route('/', methods=["GET"])
def index():
    return render_template('index.html')


@app.route('/ClearLog/<string:table>', methods=["GET"])
def clearlog(table):
    from models import model
    if(table == "logs_motion"):
        model.MainModel.Clear_logs_motion(model.MainModel)
        return redirect('/logsMotion/1')
    if(table == "logs_detection"):
        model.MainModel.Clear_logs_detection(model.MainModel)
        return redirect('/logsDetection/1')

@app.route('/sensor1/<string:status>', methods=["GET"])
def sensor1(status):
    global detection_status
    global sensor1Status
    import json
    from models import model
    config = get_data("config")
    duration = int(config[0]['motion_duration'])*60
    print('motion_duration: ',duration)
    if status == "YES":
        model.MainModel.Insert_log_motion(model.MainModel,1)
        sensor1Status = "yes"
        print("Motion detected from Sensor: 1")
        print("Trigger camera for detection: ",config[0]['motion_duration']," Minutes")
        detection_status = "on"
        WriteData("on")
        time.sleep(duration)
        WriteData("off")
        sensor1Status = "no"
        detection_status = "off"

    res = '''{"status":"Recieved"}'''
    return json.loads(res)

@app.route('/sensor2/<string:status>', methods=["GET"])
def sensor2(status):
    global detection_status
    global sensor2Status
    import json
    from models import model
    config = get_data("config")
    duration = int(config[0]['motion_duration'])*60
    print('motion_duration: ',duration)
    if status == "YES":
        model.MainModel.Insert_log_motion(model.MainModel,2)
        sensor2Status = "yes"
        print("Motion detected from Sensor: 2")
        print("Trigger camera for detection: ",config[0]['motion_duration']," Minutes")
        detection_status = "on"
        WriteData("on")
        time.sleep(duration)
        WriteData("off")
        sensor2Status = "no"
        detection_status = "off"

    res = '''{"status":"Recieved"}'''
    return json.loads(res)

logged = False
@app.route('/sensor3', methods=["GET"])
def sensor3():
    global sign_status
    global logged
    config = get_data("config")
    from models import model
    import json
    data = GetData()
    print("Sensor3 ",data)
    try:
        BatState()
        if data != "":
            score = float(data)
        else:
            score = 0.0
        print("Sensor3 ",score)
        res = '''{"status":"off"}'''
        if score > 0.4:
            res = '''{"status":"on"}'''
            sign_status = "on"
            print("********************"," !!! Analyzing !!! ","************************")
            data = [score,"",config[0]['motion_duration']]
            if not logged:
                model.MainModel.Insert_log_detection(model.MainModel,data)
                logged = True
            return json.loads(res)
        else:
            logged = False
            res = '''{"status":"off"}'''
            return json.loads(res)
    except Exception as E:
        logged = False
        print("!!!!!!!!!!! ERROR !!!!!!!!!!",E)
        score = 0
        res = '''{"status":"off"}'''
        return json.loads(res)

@app.route('/sensor4/<string:status>', methods=["GET"])
def sensor4(status):
    global sign_status
    sign_status = status
    import json
    res = '''{"status":"ok"}'''
    return res

@app.route('/GetStatus', methods=["GET"])
def GetStatus():
    import json
    res = [str(sign_status),str(detection_status),str(sensor1Status),str(sensor2Status)]
    print(res)
    return res

@app.route('/config', methods=["GET"])
def config():
    global inventory
    global message
    titles = ['active','','','','']
    FileName = ""
    #update = CheckUpdate()
    if update:
        FileName = update
    BatStatus = True
    try:
        voltage = subprocess.check_output("dmesg | grep -iC 3 'Undervoltage'", shell=True)
        if "Undervoltage" in str(voltage):
            BatStatus = False
            GPIO.output(LED_PIN,GPIO.HIGH)
            print("LOW BATTERY")
        else:
            BatStatus = True
        if "normalised" in str(voltage):
            BatStatus = True
            print("GOOD BATTERY")
            GPIO.output(LED_PIN,GPIO.LOW)
    except:
        BatStatus = True

    config = get_data("config")       
    return render_template('config.html',title = titles,BatStatus=BatStatus,FileName=FileName,update=update,config=config,loggedin=loggedin,message=message) 
    
@app.route('/logsDetection/<int:page>', methods=["GET"])
def logsDetection(page):
    global message
    FileName = ""
    update = False
    titles = ['','active','','','']
    BatStatus = True
    from models import model
    pagination = CalculatePagination(page,"SELECT * FROM logs_detection ORDER BY id ASC","/recipes/",25)
    try:
        voltage = subprocess.check_output("dmesg | grep -iC 3 'Undervoltage'", shell=True)
        if "Undervoltage" in str(voltage):
            BatStatus = False
            print("LOW BATTERY")
        else:
            BatStatus = True
        if "normalised" in str(voltage):
            BatStatus = True
            print("GOOD BATTERY")
            #GPIO.output(LED_PIN,GPIO.LOW)
    except:
        BatStatus = True
    logs_detection = model.MainModel.Get_logs_detection(model.MainModel,pagination[2],pagination[3])
    config = get_data("config")       
    return render_template('detectionlogs.html',logs_detection=logs_detection,title=titles,BatStatus=BatStatus,FileName=FileName,update=update,config=config,loggedin=loggedin,message=message,prev=pagination[0],next=pagination[1],page=page)

@app.route('/logsMotion/<int:page>', methods=["GET"])
def logsMotion(page):
    global message
    FileName = ""
    update = False
    titles = ['','','active','','']
    BatStatus = True
    from models import model
    pagination = CalculatePagination(page,"SELECT * FROM logs_motion ORDER BY id ASC","/recipes/",25)
    try:
        voltage = subprocess.check_output("dmesg | grep -iC 3 'Undervoltage'", shell=True)
        if "Undervoltage" in str(voltage):
            BatStatus = False
            print("LOW BATTERY")
        else:
            BatStatus = True
        if "normalised" in str(voltage):
            BatStatus = True
            print("GOOD BATTERY")
            #GPIO.output(LED_PIN,GPIO.LOW)
    except:
        BatStatus = True
    logs_motion = model.MainModel.Get_logs_motion(model.MainModel,pagination[2],pagination[3])
    config = get_data("config")       
    return render_template('motionlogs.html',logs_motion=logs_motion,title=titles,BatStatus=BatStatus,FileName=FileName,update=update,config=config,loggedin=loggedin,message=message,prev=pagination[0],next=pagination[1],page=page)
    
@app.route('/files/<int:page>', methods=["GET"])
def files(page):
    global inventory
    global message
    FileName = ""
    titles = ['','','','active','']
    update = False
    from models import model
    pagination = CalculatePagination(page,"SELECT * FROM files ORDER BY date DESC","/files/",25)
    print(pagination)
    files = model.MainModel.Get_files(model.MainModel,pagination[2],pagination[3])
    
    BatStatus = True
    try:
        voltage = subprocess.check_output("dmesg | grep -iC 3 'Undervoltage'", shell=True)
        if "Undervoltage" in str(voltage):
            BatStatus = False
            print("LOW BATTERY")
        else:
            BatStatus = True
        if "normalised" in str(voltage):
            BatStatus = True
            print("GOOD BATTERY")
            #GPIO.output(LED_PIN,GPIO.LOW)
    except:
        BatStatus = True
    #print(update)
    config = get_data("config")       
    return render_template('files.html',files=files,title=titles,BatStatus=BatStatus,FileName=FileName,update=update,config=config,loggedin=loggedin,message=message,prev=pagination[0],next=pagination[1],page=page)

@app.route('/fileEdit/<int:id>', methods=["GET"])
def fileEdit(id):
    config = get_data("config")
    from models import model
    file = model.MainModel.GetFile(id)
    titles = ['','','','active','']
    return render_template('file.html',config=config,title=titles,FileName=file[0])

@app.route('/updatefile/<int:id>', methods=["GET","POST"])
def updatefile(id):
    from models import model
    print(request.form) 
    data = [
        request.form.get("comments"),
        id
    ]
    model.MainModel.Update_Image(model.MainModel,data)
    return redirect('/files')

@app.route('/DeleteFile/<int:id>/<string:filename>', methods=["GET","POST"])
def DeleteFile(id,filename):
    from models import model
    model.MainModel.Delete_Image(model.MainModel,id,filename)
    return redirect('/files/1')

@app.route('/uploadmodel', methods = ["POST","GET"])
def uploadmodel():
    if request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join("", filename))
    return redirect("/config")

@app.route('/uploadFW', methods = ["POST","GET"])
def uploadFW():
    if request.files:
        file = request.files['file']
        if file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join("", filename))
    return redirect("/update/"+filename)

@app.route('/update/<string:FileName>', methods=["GET"])
def update(FileName):
    global message
    return render_template('update.html',FileName=FileName,config=config)
    


@app.route('/save_config', methods=["POST"])
def saveconfig():
    global message
    global currentSSID
    global curentPassphrase
    config = []
    config.append(request.form['device_id'])
    config.append(request.form['itemsperpage'])
    config.append(request.form['pin'])
    config.append(request.form['save_images'])
    config.append(request.form['motion_duration'])
    save_config(config)
    return redirect("/config")

@app.route('/preview', methods=["GET"])
def preview():
    titles = ['','','','','active']
    config = get_data("config")
    return render_template('video.html',title=titles,config=config)

@app.route('/confirmrestart', methods=["GET"])
def ConfRestart():
    config = get_data("config")
    ipaddress = get_ip_address()
    return render_template('restart.html',config=config,last_ip=ipaddress)

@app.route('/confirmstop', methods=["GET"])
def ConfStop():
    return render_template('stop.html')

@app.route('/restart', methods=["GET"])
def Restart():
    os.system("sudo reboot &")
    return "REBOOTING"

@app.route('/stop', methods=["GET"])
def Stop():
    os.system("sudo shutdown now &")
    return "Shutdown"

@app.route('/checkconnect', methods=["GET"])
def checkconnect():
    ipaddress = get_ip_address()
    return ipaddress
#Orient the screen 90 Deg. right

if __name__ == '__main__':
    app.run(host='10.42.0.1',port=5000, debug=False, threaded=True)
