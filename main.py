import base64
import os
import random
# import speak_greetings
import cv2
import datetime
import face_recognition
import numpy as np
import pandas as pd
from multiprocessing import shared_memory
from flask import Flask, render_template, url_for, redirect, jsonify, Response, abort, session, request, send_file
from werkzeug.utils import secure_filename
# import systemcheck
import sqlite3
import shutil
import time

#Install Build Tools: https://aka.ms/vs/17/release/vs_BuildTools.exe



conn = sqlite3.connect('./files/data.db')
print ("Opened database successfully")


conn.execute('''CREATE TABLE IF NOT EXISTS ADMIN
         (USERNAME TEXT PRIMARY KEY,
         PASSWORD           TEXT);''')

conn.execute('''CREATE TABLE IF NOT EXISTS USER
         (ID TEXT PRIMARY KEY,
         NAME           TEXT,
         BRANCH         TEXT,
         MESSAGE        TEXT,
         MAIL_ID        TEXT,
         PARENT_NAME    TEXT,
         PARENT_MAIL    TEXT,
         ISSUES         TEXT
         );''')

conn.execute('''CREATE TABLE IF NOT EXISTS ATTENDANCE
         (ID            TEXT,
         NAME           TEXT,
         BRANCH         TEXT,
         DAY            INT,
         MONTH          INT,
         YEAR           INT,
         CLASS1         TEXT,
         CLASS2         TEXT,
         CLASS3         TEXT,
         CLASS4         TEXT
         );''')

conn.close()

shape = (480, 640, 3)
app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'face_data/')
AUDIO_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'audio_data/')
CAPTURE_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'captured_picture/')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
outputFrame = None
number = random.randint(1000000, 9999999)

def html_return(msg, redirect_to = "/", delay = 5):
    return f"""
                <html>    
                    <head>      
                        <title>Camera Update</title>      
                        <meta http-equiv="refresh" content="{delay};URL='{redirect_to}'" />    
                    </head>    
                    <body> 
                        <h2> {msg}</h2>
                        <p>This page will refresh automatically.</p> 
                    </body>  
                </html>   
                
                """

def get_image_resolution():
    f1 = open("./files/camera_resolution.txt", "r")
    res_data = f1.read().strip()
    f1.close()
    res_data = res_data.split(",")
    divide_factor = int(res_data[1]) // 240
    image_resolution = (int(res_data[0])//divide_factor, int(res_data[1])//divide_factor)
    return image_resolution

def get_image_resolution2():
    f1 = open("./files/camera_resolution2.txt", "r")
    res_data = f1.read().strip()
    f1.close()
    res_data = res_data.split(",")
    divide_factor = int(res_data[1]) // 240
    image_resolution = (int(res_data[0])//divide_factor, int(res_data[1])//divide_factor)
    return image_resolution


@app.route('/', methods=['get', 'post'])
def login_page():


    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        if username == "Shreya" and password == "Shreya@12345":
            session['user'] = username
            return render_template('index.html', user=(session['user']))
        else:
            try:
                

                conn = sqlite3.connect('./files/data.db')
                print ("Opened database successfully 1")
                cursor = conn.execute(f"SELECT PASSWORD,USERNAME from ADMIN")
                for row in cursor:
                    if row[0] == password and row[1] == username:
                        session['user'] = username
                        conn.close()
                        return render_template('index.html', user=(session['user']))
                return render_template('login-page.html')
            except Exception as e:
                print("DB Error 1: ", e)
    elif 'user' in session.keys():
        return render_template('index.html', user=(session['user']))
    else:
        return render_template('login-page.html')


@app.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/add_user/', methods=['get', 'post'])
def add_user():
    if 'user' in session.keys():
        if request.method == 'POST':
            if 'file' not in request.files:
                return redirect(request.url)
            files = request.files.getlist('file')
            print(files)
            if files[0].filename == '':
                return redirect(request.url)
            ID = request.form['id']
            if files:
                try:
                    os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], ID))
                except Exception as e:
                        print("Folder Already Exists:", e)
                    
                for file in files:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], ID, filename))

            name = request.form['name']
            branch = request.form['branch']
            message = request.form['message']

            mailid = request.form['mailid']
            parent_name = request.form['parentname']
            parent_mailid = request.form['parentmailid']

            train(folder_path=(os.path.join(app.config['UPLOAD_FOLDER'], ID)), ID=ID)

            print("Updating Database")
            conn = sqlite3.connect('./files/data.db')
            conn.execute(f"INSERT INTO USER (ID, NAME, BRANCH, MESSAGE, MAIL_ID, PARENT_NAME, PARENT_MAIL) VALUES ('{ID}', '{name}','{branch}', '{message}', '{mailid}', '{parent_name}', '{parent_mailid}' )")
            conn.commit()

            day = datetime.datetime.now().day
            month = datetime.datetime.now().month
            year = datetime.datetime.now().year
            hh = datetime.datetime.now().hour
            mm = datetime.datetime.now().minute


            conn.execute(f"INSERT INTO ATTENDANCE (ID, NAME, BRANCH, DAY, MONTH, YEAR, CLASS1, CLASS2, CLASS3, CLASS4) \
            VALUES ('{ID}', '{name}' , '{branch}', '{day}', '{month}', '{year}', 'ABSENT', 'ABSENT', 'ABSENT', 'ABSENT') ")
            conn.commit()

            conn.close()

            f1 = open("./files/face_data_change.txt", 'w')
            f1.write("1")
            f1.close()


            return redirect(request.url)
        return render_template('add_user.html', user=(session['user']))
    else:
        return redirect(url_for('login_page'))


def train(folder_path, ID):

    known_faces = np.load('./files/known_faces.npy', allow_pickle=True).tolist()
    known_names = np.load('./files/known_names.npy', allow_pickle=True).tolist()

    for filename in os.listdir(folder_path):
        image_data = face_recognition.load_image_file(folder_path + f"/{filename}")
        print("Training for:", filename)
        try:
            encoding = face_recognition.face_encodings(image_data)[0]
            known_faces.append(encoding)
            known_names.append(ID)
        except Exception as e:
            print('No Face Detected.', e)
    print("Training for Folder ", folder_path,"Done.")

    np.save('./files/known_faces', np.array(known_faces))
    np.save('./files/known_names', np.array(known_names))

    f1 = open("./files/face_data_change.txt", 'w')
    f1.write("1")
    f1.close()



@app.route('/add_admin/', methods=['get', 'post'])
def add_admin():
    if 'user' in session.keys():
        if request.method == 'POST':
            print("Got Admin Enroll details")
            username = request.form['username']
            password = request.form['password']

            print("Updating Database", end = " ")
            try:
                conn = sqlite3.connect('./files/data.db')
                conn.execute(f"INSERT INTO ADMIN (USERNAME, PASSWORD) VALUES ('{username}', '{password}' )")
                conn.commit()
                conn.close()
                print("| Admin Added Successfully")
            except Exception as e:
                print("Failed. ERROR:", e)
            return redirect(url_for('login_page'))
        return render_template('add_admin.html', user=(session['user']))
    else:
        return redirect(url_for('login_page'))


@app.route('/update_admin/' , methods=['GET', 'POST'])
def update_admin():
    if 'user' in session.keys():
        print("RM", request.method)
        if request.method == 'POST':
            print("Got Admin Update details")
            userid = request.form['username1']
            print("Got userid")
            password = request.form['password1']
            print("Got userid")
            if password == "DEL":
                if userid != "Shreya":
                    try:
                        conn = sqlite3.connect('./files/data.db')
                        conn.execute(f"DELETE from ADMIN where USERNAME = '{userid}';")
                        conn.commit()
                        conn.close()    
                        return html_return("Successfully Deleted Admin User: "+str(userid), delay = 3)
                    except Exception as e:
                        return html_return("Deletion failed for Admin User: "+str(userid)+". Reason: "+str(e))
                else:
                    return html_return("Cannot Delete Master Default Admin User: "+str(userid))
            else:
            
                try:
                    conn = sqlite3.connect('./files/data.db')
                    conn.execute(f"UPDATE ADMIN set PASSWORD = '{password}' where USERNAME = '{userid}';")
                    conn.commit()
                    conn.close()   
                    return html_return("Password Updated for Admin: "+str(userid) +" if exists.")
                except Exception as e:
                        return html_return("Password Update failed for Admin User: "+str(userid)+". Reason: "+str(e))
    else:
        return redirect(url_for('login_page'))


@app.route('/update_camera/' , methods=['GET', 'POST'])
def update_camera():
    if 'user' in session.keys():
        print("RM", request.method)
        if request.method == 'POST':
            print("Got Camera Update details")
            cam_source = request.form['cam_source']
            print("Got Camera Source")
            
            try:
                f1 = open("./files/camera_source.txt", "w")
                f1.write(cam_source)
                f1.close()
                return html_return("Camera Source Updated", delay = 3)
            except Exception as e:
                    return html_return("Camera Source Updation Failed. Reason:"+ str(e))
    else:
        return redirect(url_for('login_page'))


@app.route('/update_latetime/' , methods=['GET', 'POST'])
def update_latetime():
    if 'user' in session.keys():
        print("RM", request.method)
        if request.method == 'POST':
            print("Got Late Update details")
            late_hour = request.form['hour']
            late_minute = request.form['minute']
         
            try:
                f1 = open("./files/late_time.txt", "w")
                f1.write(late_hour +","+ late_minute)
                f1.close()
                return html_return("Late Time Updated", delay = 3)
            except Exception as e:
                    return html_return("Late Time Updation Failed. Reason:"+ str(e))
    else:
        return redirect(url_for('login_page'))


@app.route('/update_message/' , methods=['GET', 'POST'])
def update_message():
    if 'user' in session.keys():
        print("RM", request.method)
        if request.method == 'POST':
            print("Got User Message Update details")
            ID = request.form['ID']
            print("Got User ID")
            message = request.form['message']
            print("Got New Message")
            
            try:
                conn = sqlite3.connect('./files/data.db')
                conn.execute(f"UPDATE USER set MESSAGE = '{message}' where ID = '{ID}';")
                conn.commit()
                conn.close()   
                os.remove(AUDIO_FOLDER+f"{ID}.wav")
                return html_return("Message Updated for User: "+str(ID) +" if exists.")
            except Exception as e:
                    return html_return("Message Update failed for User: "+str(ID)+". Reason: "+str(e))
    else:
        return redirect(url_for('login_page'))


@app.route('/all_users/')
def all_users():
    if 'user' in session.keys():
        conn = sqlite3.connect('./files/data.db')
        cursor = conn.execute("SELECT NAME, ID, BRANCH, MESSAGE, MAIL_ID, PARENT_NAME, PARENT_MAIL from USER")
        users_list = []
        for row in cursor:
            users_list.append(row)
        conn.close()
        return render_template('all_users.html', user=(session['user']), users_list=users_list)
    else:
        return redirect(url_for('login_page'))


@app.route('/attendance/')
def attendance():
    if 'user' in session.keys():
        conn = sqlite3.connect('./files/data.db')
        cursor = conn.execute("SELECT NAME, ID, BRANCH, DAY, MONTH, YEAR, CLASS1, CLASS2, CLASS3, CLASS4 from ATTENDANCE")
        attendance_list = []
        for row in cursor:
            attendance_list.append(row)
        conn.close()
        return render_template('attendance.html', user=(session['user']), attendance=attendance_list)
    else:
        return redirect(url_for('login_page'))


@app.route('/download_all/')
def download_all():
    if 'user' in session.keys():
        conn = sqlite3.connect('./files/data.db')
        cursor = conn.execute("SELECT NAME, ID, BRANCH, DAY, MONTH, YEAR, CLASS1, CLASS2, CLASS3, CLASS4 from ATTENDANCE")
        attendance_list = []
        for row in cursor:
            attendance_list.append(row)
        conn.close()
        
        name = []
        rollno = []
        branch = []
        date = []
        class1 = []
        class2 = []
        class3 = []
        class4 = []
        
        for i in attendance_list:
            name.append(i[0])
            rollno.append(i[1])
            branch.append(i[2])
            date.append(f"{i[3]}-{i[4]}-{i[5]}")
            class1.append(i[6])
            class2.append(i[7])
            class3.append(i[8])
            class4.append(i[9])

        data = pd.DataFrame({'Name': name, 'ID': rollno, 'Branch': branch, 'Date': date, 'Class_1': class1, "Class_2": class2, "Class_3": class3, "Class_4": class4})
        fname = 'Complete_Attendance_download.csv'
        data.to_csv(fname, index=False)
        return send_file(fname, as_attachment=True, download_name=fname)
    else:
        return redirect(url_for('login_page'))


@app.route('/download_month/')
def download_month():
    if 'user' in session.keys():
        cur_m = datetime.datetime.now().month
        cur_y = datetime.datetime.now().year

        conn = sqlite3.connect('./files/data.db')
        cursor = conn.execute(f"SELECT NAME, ID, BRANCH, DAY, MONTH, YEAR, CLASS1, CLASS2, CLASS3, CLASS4 from ATTENDANCE where MONTH = '{cur_m}' AND YEAR = '{cur_y}'")
        attendance_list = []
        for row in cursor:
            attendance_list.append(row)
        conn.close()
        
        name = []
        rollno = []
        branch = []
        date = []
        class1 = []
        class2 = []
        class3 = []
        class4 = []
        
        for i in attendance_list:
            name.append(i[0])
            rollno.append(i[1])
            branch.append(i[2])
            date.append(f"{i[3]}-{i[4]}-{i[5]}")
            class1.append(i[6])
            class2.append(i[7])
            class3.append(i[8])
            class4.append(i[9])

        data = pd.DataFrame({'Name': name, 'ID': rollno, 'Branch': branch, 'Date': date, 'Class_1': class1, "Class_2": class2, "Class_3": class3, "Class_4": class4})
        fname = "Attendance_"+str(cur_m)+"_"+str(cur_y)+'_download.csv'
        data.to_csv(fname, index=False)
        return send_file(fname, as_attachment=True, download_name=fname)
    else:
        return redirect(url_for('login_page'))
    

@app.route('/download_specific/<rollno>')
def download_specific(rollno):
    if 'user' in session.keys():

        conn = sqlite3.connect('./files/data.db')
        cursor = conn.execute(f"SELECT NAME, ID, BRANCH, DAY, MONTH, YEAR, CLASS1, CLASS2, CLASS3, CLASS4 from ATTENDANCE where ID = '{rollno}' ")
        attendance_list = []
        for row in cursor:
            attendance_list.append(row)
        conn.close()
        
        name = []
        rollnox = []
        branch = []
        date = []
        class1 = []
        class2 = []
        class3 = []
        class4 = []
        
        for i in attendance_list:
            name.append(i[0])
            rollnox.append(i[1])
            branch.append(i[2])
            date.append(f"{i[3]}-{i[4]}-{i[5]}")
            class1.append(i[6])
            class2.append(i[7])
            class3.append(i[8])
            class4.append(i[9])

        data = pd.DataFrame({'Name': name, 'ID': rollno, 'Branch': branch, 'Date': date, 'Class_1': class1, "Class_2": class2, "Class_3": class3, "Class_4": class4})
        fname = "Attendance_"+str(rollno)+'_download.csv'
        data.to_csv(fname, index=False)
        return send_file(fname, as_attachment=True, download_name=fname)
    else:
        return redirect(url_for('login_page'))


@app.route('/profile/<ID>')
def profile(ID):
    if 'user' in session.keys():
        rollno = ID
        conn = sqlite3.connect('./files/data.db')
        cursor = conn.execute(f"SELECT NAME, ID, BRANCH, MESSAGE, MAIL_ID, PARENT_NAME, PARENT_MAIL, ISSUES from USER where ID = '{ID}'")

        users = []
        for row in cursor:
            users = row

        cursor = conn.execute("SELECT NAME, ID, BRANCH, DAY, MONTH, YEAR, CLASS1, CLASS2, CLASS3, CLASS4 from ATTENDANCE")

        attendance_list = []
        for row in cursor:
            attendance_list.append([row[3],row[4],row[5],row[6],row[7],row[8],row[9]])
        conn.close()

        img_list = os.listdir(UPLOAD_FOLDER + '/' + ID)
        with open(UPLOAD_FOLDER + '/' + ID + '/' + img_list[0], 'rb') as (image):
            image = base64.b64encode(image.read()).decode('utf-8')
        print(attendance_list)

        return render_template('profile.html', user=users, image=image, attendance=attendance_list, rollno=ID)
    else:
        return redirect(url_for('login_page'))


@app.route('/delete_user/<ID>')
def delete_user(ID):
    if 'user' in session.keys():
        try:
            conn = sqlite3.connect('./files/data.db')
            conn.execute(f"DELETE from USER where ID = '{ID}';")
            conn.commit()
            conn.close()
        except Exception as e:
            print("Unable to delete User from Database. Reason:", e)
            return jsonify(data=False)

        try:
            known_faces = np.load('./files/known_faces.npy', allow_pickle=True).tolist()
            known_names = np.load('./files/known_names.npy', allow_pickle=True).tolist()

            for _ in range(known_names.count(ID)):
                x = known_names.index(ID)
                known_names.pop(x)
                known_faces.pop(x)

            np.save('./files/known_names.npy', np.array(known_names))
            np.save('./files/known_faces.npy', np.array(known_faces))

            f1 = open("./files/face_data_change.txt", 'w')
            f1.write("1")
            f1.close()
            try:
                os.remove(AUDIO_FOLDER+f"{ID}.wav")
            except:
                pass
        except Exception as e:
            print("Unable to delete User from np Array. Reason:", e)
            return jsonify(data=False)
        try:
            os.remove(AUDIO_FOLDER+f'{ID}.mp3')
        except Exception as e:
            print("Unable to delete Greeting Audio.:", e)

        try:
            shutil.rmtree(os.path.join(app.config['UPLOAD_FOLDER'], ID))
            return jsonify(data=True)
        except Exception as e:
            print("Unable to delete Images. Reason:", e)
            return jsonify(data=False)
    else:
        return redirect(url_for('login_page'))


@app.route('/get_attendance_frequency/')
def get_attendance_frequency():
    if 'user' in session.keys():
        db = sqlite3.connect('./files/data.db')
        data = db.execute('select day,month,year,count(*) as freq from attendance group by day,month,year order by year desc,month desc,day desc limit 10;').fetchall()
        label = []
        freq = []
        for i in data:
            label.append(f"{i[0]}: {i[1]}: {i[2]}")
            freq.append(i[3])
        db.close()
        return jsonify(label=label, freq=freq)
    else:
        return redirect(url_for('login_page'))



def generate(): #Generate Video Frame
    image_resolution = get_image_resolution()
    while True:
        try:
            shared_image = shared_memory.SharedMemory(name='shared_processed_image')
            processed_image = np.ndarray((image_resolution[1], image_resolution[0], 3), dtype=np.uint8, buffer=shared_image.buf)

            # shared_image = shared_memory.SharedMemory(name='shared_raw_image')
            # raw_image = np.ndarray((image_resolution[1], image_resolution[0], 3), dtype=np.uint8, buffer=shared_image.buf)

            while True:
                try:
                    flag, encoded_image = cv2.imencode('.png', processed_image)
                    # flag, encoded_image = cv2.imencode('.png', raw_image)
                except Exception as e:
                    print(e)

                if not flag:
                    continue
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + encoded_image.tobytes() + b'\r\n'
        except Exception as e:
            print("Error in Generate:", e)
            print("Make Sure that new_recognition.py file is running\n")
            time.sleep(1)


@app.route('/video_feed')
def video_feed(): # Show Video Feed
    if 'user' in session.keys():
        return Response((generate()), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return redirect(url_for('login_page'))


@app.route('/take_picture' , methods=['GET', 'POST'])
def take_picture(): # Show Video Feed
    if 'user' in session.keys():
        print("Take Picture Pinged")
        image_resolution = get_image_resolution()
        try:
            shared_image = shared_memory.SharedMemory(name='shared_processed_image')
            raw_image = np.ndarray((image_resolution[1], image_resolution[0], 3), dtype=np.uint8, buffer=shared_image.buf)
            
            # flag, encoded_image = cv2.imencode('.png', raw_image)
            if raw_image is not None:
                fname = str(datetime.datetime.now())[:-7]+".png"
                fname = fname.replace(" ","")
                fname = fname.replace(":","")
                fname = fname.replace("-","")
                cv2.imwrite(CAPTURE_FOLDER+fname, raw_image)
                print("Picture Taken: ", CAPTURE_FOLDER+fname)
                return "Picture Taken"
        except Exception as e:
            print("Unable to take Picture: ", e)
    else:
        return redirect(url_for('login_page'))
    

@app.errorhandler(404)
def nice(_):
    return render_template('error_404.html')


@app.route('/update_issue/', methods=['get', 'post'])
def update_issue():
    if 'user' in session.keys():
        if request.method == 'POST':
            
            id = request.form['studentid']
            issues = request.form['issues']

            try:
                conn = sqlite3.connect('./files/data.db')
                conn.execute(f"UPDATE USER set ISSUES = '{issues}' where ID = '{id}';")
                conn.commit()
                conn.close()   
                return html_return("Issue Updated for: "+str(id), redirect_to="/all_users/", delay = 3)
            except Exception as e: 
                return html_return("Issue not Updated for ID: "+str(id)+". Reason: "+str(e), redirect_to="/all_users/", delay = 3)

        return html_return("Issue not Updated for ID: "+str(id), redirect_to="/all_users/", delay = 3)
    else:
        return redirect(url_for('login_page'))


app.secret_key = 'q12q3q4e5g5htrh@werwer15454'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port= 8000, debug=True)#80)
# global outputFrame ## Warning: Unused global
