#!/usr/bin/python3

# Copyright (c) 2022 Raspberry Pi Ltd
# Author: Alasdair Allan <alasdair@raspberrypi.com>
# SPDX-License-Identifier: BSD-3-Clause

# A TensorFlow Lite example for Picamera2 on Raspberry Pi OS Bullseye
#
# Install necessary dependences before starting,
#
# $ sudo apt update
# $ sudo apt install build-essential
# $ sudo apt install libatlas-base-dev
# $ sudo apt install python3-pip
# $ pip3 install tflite-runtime
# $ pip3 install opencv-python==4.4.0.46
# $ pip3 install pillow
# $ pip3 install numpy
#
# and run from the command line,
#
# $ python3 real_time_with_labels.py --model mobilenet_v2.tflite --label coco_labels.txt

import argparse

import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import MappedArray, Picamera2, Preview
import sqlite3 as lite
PathToDatabase = "/home/system/DeerDetector/static/main.db"

normalSize = (640, 480)
lowresSize = (320, 240)

rectangles = []
captured = False

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

def SaveImage(FileName):
    try:
        from models import model
        from datetime import datetime
        cdt = datetime.today()
        currentdate = cdt.date()
        current_time = cdt.strftime("%H:%M:%S")        
        print(FileName)
        #data = self.Cleaninput(self,data)
        query = "INSERT INTO files (date, time, filename) VALUES('"+str(currentdate)+"','"+str(current_time)+"','"+FileName+"')"
        con = model.db.connect(model.PathToDatabase)
        con.row_factory = model.db.Row
        cur = con.cursor()
        cur.execute(query)
        con.commit()
        ID = cur.lastrowid
        cur.close()
        return ID
    except model.db.Error as error:
        print("Insert image Error: ",str(error))
        return False
    except Exception as e:
        print("insert image Error %s:" % e.args[0])
        return False
   
config = get_data("config")       
def GetData():
    try:
        stat = open("stat.txt","r")
        data = stat.read()
        return data
    except Exception as E:
        print("Failure ",E)
        return False
    
def WriteCapture(data):
    try:
        stat = open("capture.txt","w")
        stat.write(str(data))
        return True
    except Exception as E:
        print("Failure ",E)
        return False
    
def WriteData(data):
    try:
        stat = open("/home/system/DeerDetector/vidstat.txt","w")
        stat.write(str(data))
        return True
    except Exception as E:
        print("Failure ",E)
        return False
    
WriteData(0.0)

def ReadLabelFile(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    ret = {}
    for line in lines:
        pair = line.strip().split(maxsplit=1)
        ret[int(pair[0])] = pair[1].strip()
    return ret


def DrawRectangles(request):
    with MappedArray(request, "main") as m:
        for rect in rectangles:
            #print(rect)
            rect_start = (int(rect[0] * 2) - 5, int(rect[1] * 2) - 5)
            rect_end = (int(rect[2] * 2) + 5, int(rect[3] * 2) + 5)
            cv2.rectangle(m.array, rect_start, rect_end, (0, 255, 0, 0))
            if len(rect) == 5:
                text = rect[4]
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(m.array, text, (int(rect[0] * 2) + 10, int(rect[1] * 2) + 10),
                            font, 1, (255, 255, 255), 2, cv2.LINE_AA)

def Capture(picam2):
    from datetime import datetime
    config = get_data("config")
    if config[0]['save_images'] == 1:
        timestamp = datetime.now().isoformat()
        picam2.capture_file('/home/system/DeerDetector/static/captures/%s.jpg' % timestamp)
        SaveImage('%s.jpg' % timestamp)

def InferenceTensorFlow(image, model, output, label=None):
    global rectangles
    global captured
    #WriteData(0.0)
    if label:
        labels = ReadLabelFile(label)
    else:
        labels = None
    
    interpreter = tflite.Interpreter(model_path=model, num_threads=4)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    #print(output_details)
    height = input_details[0]['shape'][1]
    width = input_details[0]['shape'][2]
    floating_model = False
    if input_details[0]['dtype'] == np.float32:
        floating_model = True

    rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    initial_h, initial_w, channels = rgb.shape

    picture = cv2.resize(rgb, (width, height))

    input_data = np.expand_dims(picture, axis=0)
    if floating_model:
        input_data = (np.float32(input_data) - 127.5) / 127.5

    interpreter.set_tensor(input_details[0]['index'], input_data)

    interpreter.invoke()

    detected_boxes = interpreter.get_tensor(output_details[0]['index'])
    detected_classes = interpreter.get_tensor(output_details[1]['index'])
    detected_scores = interpreter.get_tensor(output_details[2]['index'])
    num_boxes = interpreter.get_tensor(output_details[3]['index'])

    rectangles = []
    for i in range(int(num_boxes)):
        res = GetData()
        top, left, bottom, right = detected_boxes[0][i]
        classId = int(detected_classes[0][i])
        score = detected_scores[0][i]
        if score > 0.4:
            xmin = left * initial_w
            ymin = bottom * initial_h
            xmax = right * initial_w
            ymax = top * initial_h
            box = [xmin, ymin, xmax, ymax]
            rectangles.append(box)
            if labels:
                if labels[classId] == "person":
                    print("Person")
                    #WriteData(score)
                    #Capture(output)
                if labels[classId] == "deer":
                    print("Deer")
                    WriteData(score)
                    if not captured:
                        Capture(output)
                        captured = True
                if labels[classId] == "horse":
                    WriteData(score)
                    if not captured:
                        Capture(output)
                        captured = True
                    print("Deer**")
                print(labels[classId], 'score = ', score)
                rectangles[-1].append(labels[classId])
            else:
                print('score = ', score)
                #WriteData(0.0)
        else:
            captured = False

def main():
    conf = get_data("config")
    label_file = "coco_labels.txt"
    model = conf[0]['detection_model']
    picam2 = Picamera2()
    #picam2.start_preview(Preview.QTGL)
    config = picam2.create_preview_configuration(main={"size": normalSize},
                                                 lores={"size": lowresSize, "format": "YUV420"})
    picam2.configure(config)
    stride = picam2.stream_configuration("lores")["stride"]
    picam2.post_callback = DrawRectangles
    picam2.start()
    while True:
        res = GetData()
        print(res)
        if res == "on":
            buffer = picam2.capture_buffer("lores")
            grey = buffer[:stride * lowresSize[1]].reshape((lowresSize[1], stride))
            _ = InferenceTensorFlow(grey, model, picam2, label_file)
        else:
            WriteData(0.0)
            print("standing by")

if __name__ == '__main__':
    main()
