import numpy as np
import cv2
import os
from multiprocessing import shared_memory
from threading import Thread
import face_recognition
import time
import sqlite3
from datetime import datetime

import cv2
import numpy as np


DEBUG = 1

DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'shared_data/')

window_name = "Shared_FaceRecog"

KNOWN_FACES_DIR = 'face_data'
TOLERANCE = 0.45
FRAME_THICKNESS = 3
FONT_THICKNESS = 2
MODEL = 'hog'

count = 0
start = time.time() + 1

f1 = open("./files/camera_resolution.txt", "r")
res_data = f1.read().strip()
f1.close()
res_data = res_data.split(",")
divide_factor = int(res_data[1]) // 240
image_resolution = (int(res_data[0])//divide_factor, int(res_data[1])//divide_factor)



try:
    f1 = open("./files/camera_source.txt", "r")
    text_data = f1.read()
    f1.close()
    try:
        
        cam_source = int(text_data)
    except:
        cam_source = text_data
    
except Exception as e:
    print("Unable to Camera Source, Using Default Camera.")
    cam_source = 0



print('Initializing Camera')
print("OpenCV Mode:", cam_source)
if ":/" in str(cam_source):
    print("Network Mode")
    cap = cv2.VideoCapture(cam_source)
else:
    print("Webcam Mode")
    cap = cv2.VideoCapture(cam_source)#,cv2.CAP_DSHOW)

print('Waiting for First Frame')
raw_imag = None
while raw_imag is None:
    _,raw_imag = cap.read()
    time.sleep(0.1)
print('Got First Frame')

raw_image = cv2.resize(raw_imag, image_resolution)

try:
    shared_processed_image = shared_memory.SharedMemory(create=True, size=raw_image.nbytes, name="shared_processed_image")
except FileExistsError:
    shared_processed_image = shared_memory.SharedMemory(create=False, size=raw_image.nbytes, name="shared_processed_image")
    shared_processed_image.unlink()

    time.sleep(2)
    shared_processed_image = shared_memory.SharedMemory(create=True, size=raw_image.nbytes, name="shared_processed_image")

processed_image_buf = np.ndarray(raw_image.shape, dtype=raw_image.dtype, buffer=shared_processed_image.buf)

print('Loading known faces...', end =" ")
try:
    known_faces = np.load('./files/known_faces.npy', allow_pickle=True).tolist()
    known_names = np.load('./files/known_names.npy', allow_pickle=True).tolist()
except FileNotFoundError:
    ls = []
    np.save('./files/known_faces', np.array(ls))
    np.save('./files/known_names', np.array(ls))

    known_faces = np.load('./files/known_faces.npy', allow_pickle=True).tolist()
    known_names = np.load('./files/known_names.npy', allow_pickle=True).tolist()

f1 = open("./files/face_data_change.txt", 'w')
f1.close()

conn = sqlite3.connect('./files/data.db')
cursor = conn.execute("SELECT NAME, ID, BRANCH, MESSAGE, MAIL_ID, PARENT_NAME, PARENT_MAIL from USER")
users_data = dict()
for row in cursor:
    users_data[row[1]] = (row[0], row[2], row[3])
conn.close()

print("Loaded")







day = datetime.now().day
month = datetime.now().month
year = datetime.now().year
hh = datetime.now().hour
mm = datetime.now().minute


conn = sqlite3.connect('./files/data.db')
cursor = conn.execute(f"SELECT NAME from ATTENDANCE where DAY = '{day}' AND MONTH = '{month}' AND YEAR = '{year}'; ")
attendance = []
for row in cursor:
    attendance.append(row)
if len(attendance) == 0:
    print("Date Not Added, Adding Absent Data for All.")
    for ID in users_data:
        print("Adding For:", users_data[ID])
        name = users_data[ID][0]
        branch = users_data[ID][1]
        conn.execute(f"INSERT INTO ATTENDANCE (ID, NAME, BRANCH, DAY, MONTH, YEAR, CLASS1, CLASS2, CLASS3, CLASS4) \
            VALUES ('{ID}', '{name}' , '{branch}', '{day}', '{month}', '{year}', 'ABSENT', 'ABSENT', 'ABSENT', 'ABSENT') ")
    conn.commit()

else:
    print("Date Already Processed")

conn.close()

time.sleep(10)
status = 0



while True:
    print()
    
    # cv2.imshow(window_name, raw_image)

    day = datetime.now().day
    month = datetime.now().month
    year = datetime.now().year
    hour = datetime.now().hour
    minute = datetime.now().minute


    in_time = hour*100 + minute
    print("InTime:", in_time)

    
    # f1 = open("./files/late_time.txt")
    # late_data = f1.read()
    # f1.close()

    # late_data = late_data.split(",")
    # late_hour = int(late_data[0])
    # late_minute = int(late_data[1])


    class_1_time = 900
    class_1_late = 910

    class_2_time = 1110
    class_2_late = 1120

    class_3_time = 1330
    class_3_late = 1340

    class_4_time = 1530
    class_4_late = 1540


    # image = raw_image.copy()
    _,image = cap.read()
        
    if image is not None:
        image = cv2.resize(image, image_resolution)
        raw_image = image.copy()
        # cv2.imshow("Frame", raw_image)
        if (cv2.waitKey(1) == 113):
            break

    if status == 0:
        status = 1
        image_rgb = cv2.cvtColor(raw_image, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(image_rgb, model=MODEL)
        encodings = face_recognition.face_encodings(image_rgb, locations)
        face_detected = False
        faces = []

        all_names = []

        for face_encoding, face_location in zip(encodings, locations):
            results = face_recognition.compare_faces(known_faces, face_encoding, TOLERANCE)
            face_detected = True
            match = None
            if True in results:
                match = known_names[results.index(True)]
                print("Match:", match)
            
                faces.append([ users_data[match][0], face_location])
                conn = sqlite3.connect('./files/data.db')
                # cursor = conn.execute(f"SELECT NAME from ATTENDANCE where ID = '{match}' AND DAY = '{day}' AND MONTH = '{month}' AND YEAR = '{year}'; ")
                # attendance = []
                # for row in cursor:
                #     attendance.append(row)
                # if len(attendance) == 0:
                if 1:
                    print("Adding Attendance to Database")
                    

                    if class_1_time <= in_time <=  class_1_late:
                        print("OnTime for Class 1")
                        to_update_class = "CLASS1"
                        to_update_data = "PRESENT " + str(hour)+":"+str(minute)
                    
                    elif class_2_time <= in_time <=  class_2_late:
                        print("OnTime for Class 2")
                        to_update_class = "CLASS2"
                        to_update_data = "PRESENT " + str(hour)+":"+str(minute)

                    elif class_3_time <= in_time <=  class_3_late:
                        print("OnTime for Class 3")
                        to_update_class = "CLASS3"
                        to_update_data = "PRESENT " + str(hour)+":"+str(minute)

                    elif class_4_time <= in_time <=  class_4_late:
                        print("OnTime for Class 4")
                        to_update_class = "CLASS1"
                        to_update_data = "PRESENT " + str(hour)+":"+str(minute)
                    

                    elif class_1_late <= in_time <=  class_2_time:
                        print("Late for Class 1")
                        to_update_class = "CLASS1"
                        to_update_data = "ABSENT " + str(hour)+":"+str(minute)

                    elif class_2_late <= in_time <=  class_3_time:
                        print("Late for Class 2")
                        to_update_class = "CLASS2"
                        to_update_data = "ABSENT " + str(hour)+":"+str(minute)

                    elif class_3_late <= in_time <=  class_4_time:
                        print("Late for Class 3")
                        to_update_class = "CLASS3"
                        to_update_data = "ABSENT " + str(hour)+":"+str(minute)

                    elif class_4_late <= in_time:
                        print("Late for Class 4")
                        to_update_class = "CLASS4"
                        to_update_data = "ABSENT " + str(hour)+":"+str(minute)
                    
                    else:
                        print("Default")
                        to_update_class = 0

                    if to_update_class != 0:
                        conn.execute(f"UPDATE ATTENDANCE set {to_update_class} = '{to_update_data}' WHERE ID = '{match}' AND DAY = '{day}' AND MONTH = '{month}' AND YEAR = '{year}'")
                        conn.commit()
                    conn.close()



            else:
                faces.append(['Unknown', face_location])
              
    else:
        status = 0


    if face_detected:
        print("Face was detected")

        for name, face_location in faces:

            color = [(ord(c.lower()) - 97) * 8 for c in name[:3]]
            top_left = (face_location[3]-20, face_location[0]-20)
            bottom_right = (face_location[1]+20, face_location[2]+20)
            cv2.rectangle(image, top_left, bottom_right, color, FRAME_THICKNESS)
            
            top_left = (face_location[3]-22, face_location[0]-40)
            bottom_right = (face_location[1]-5, face_location[0]-20)
            cv2.rectangle(image, top_left, bottom_right, color, cv2.FILLED)
            cv2.putText(image, name, (face_location[3] - 10, face_location[0] - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200,200), FONT_THICKNESS)

    processed_image_buf[:] = image[:]

    # cv2.imshow(window_name, image)
    cv2.waitKey(1)
    count += 1
    if time.time() - start >= 10:
        fps = count/10
        print("Average FPS: ", fps)
        if fps < 5:
            print("Very Low FPS, Consider using more Powerful PC")
        f1 = open("./files/face_data_change.txt", 'r')
        face_data_change = f1.read()
        f1.close()
        if "1" in face_data_change:
            print("Face Data Changed")
            print('Loading known faces...', end =" ")
            known_faces = np.load('./files/known_faces.npy', allow_pickle=True).tolist()
            known_names = np.load('./files/known_names.npy', allow_pickle=True).tolist()
            f1 = open("./files/face_data_change.txt", 'w')
            f1.close()
            conn = sqlite3.connect('./files/data.db')
            cursor = conn.execute("SELECT NAME, ID, BRANCH, MESSAGE, MAIL_ID, PARENT_NAME, PARENT_MAIL from USER")
            users_data = dict()
            for row in cursor:
                users_data[row[1]] = (row[0], row[2], row[3])
            conn.close()
            print("Loaded")
        count = 0
        start = time.time()


