import cv2
import os
import numpy as np
#from utils import download_file
import cvlib as cv
from cvlib.object_detection import draw_bbox
import time
from playsound import playsound
import requests
from cloudant.client import Cloudant
from flask import Flask, flash, redirect, render_template, request, url_for, Response
from werkzeug.utils import secure_filename
#import detect
UPLOAD_FOLDER = "static/uploads/"
RESULTS_FOLDER = "static/results/"
app=Flask(__name__,template_folder='template')
app.secret_key = "secret-key"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
from cloudant.client import Cloudant
client=Cloudant.iam('e80322c6-5b15-4385-ba6a-c587c3471e4b-bluemix','Kf6tBtrDrpQZtYfredJ-rkYky1lX39giPycwe0lhCmyj',connect=True)
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
    # Get the form data
        try:
            uname = request.args.get('name')
            username = request.args.get('email')
            psw = request.args.get('psw')
            print(list(request.form.values()))

             #email = request.form["email"]
            #password = request.form["password"]
            # Create a database using an initialized client
            my_database = client['my_db']
            # Check that the database doesn't already exist
            if my_database.exists():
                print(f"'{my_database}' successfully created.")
            # Create a JSON document
            json_document = {
            "_id": email,
            "name": uname,
            "email": email,
            "psw": psw,
            }
            if email in my_database:
                return render_template("register.html", msg="Email already exists")
            else:
            # Create a document using the Database API
                new_document = my_database.create_document(json_document)
                return render_template("register.html", msg="Account created successfully!")
        except Exception as e:
            return render_template("register.html", msg="Something went wrong! Please try again")
    if request.method == "GET":
        return render_template("register.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.args.get('email')
        psw = request.args.get('psw')
        print (username, psw)
        # Create a database using an initialized client
        my_database = client['my_db']
        query = {'email': {'$eq': username}}
        docs = my_database.get_query_result(query)
        print(docs)
        my_database.get_query_result(query)
        print(len(docs.all()))
        if(len(docs.all())==0):
            return render_template("register.html", prediction="The username is not found.") 
        else:
            if((username==docs[0][0]['email'] and psw==docs[0][0]['psw'])):
                return redirect(url_for("predict"))
            else:
                return render_template("login.html", msg="Invalid credentials!")
    if request.method == "GET":
        return render_template("login.html")
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "POST":
        webcam = cv2.VideoCapture("drowning.mp4")
        if not webcam.isOpened():
            print("Could not open webcam")
            exit()

        t0 = time.time()  # gives time in seconds after 1970
        # variable dcount stands for how many seconds the person has been standing still for
        centre0 = np.zeros(2)
        isDrowning = False

        # this loop happens approximately every 1 second, so if a person doesn't move,
        # or moves very little for 10seconds, we can say they are drowning
        # loop through frames
        t0 = time.time()  # gives time in seconds after 1970

        # variable dcount stands for how many seconds the person has been standing still for
        centre0 = np.zeros(2)
        isDrowning = False

        # this loop happens approximately every 1 second, so if a person doesn't move,
        # or moves very little for 10seconds, we can say they are drowning

        # loop through frames
        while webcam.isOpened():
            # read frame from webcam
            status, frame = webcam.read()

            if not status:
                print("Could not read frame")
                exit()

            # apply object detection
            bbox, label, conf = cv.detect_common_objects(frame)
            # simplifying for only 1 person

            # s = (len(bbox), 2)
            print(bbox)
            if len(bbox) > 0:
                bbox0 = bbox[0]
                # centre = np.zeros(s)
                centre = [0, 0]

                # for i in range(0, len(bbox)):
                # centre[i] =[(bbox[i][0]+bbox[i][2])/2,(bbox[i][1]+bbox[i][3])/2 ]

                centre = [(bbox0[0] + bbox0[2]) / 2, (bbox0[1] + bbox0[3]) / 2]

                # make vertical and horizontal movement variables
                hmov = abs(centre[0] - centre0[0])
                vmov = abs(centre[1] - centre0[1])
                # there is still need to tweek the threshold
                # this threshold is for checking how much the centre has moved

                x = time.time()

                threshold = 30
                if hmov > threshold or vmov > threshold:
                    print(x - t0, "s")
                    t0 = time.time()
                    isDrowning = False

                else:

                    print(x - t0, "s")
                    if (time.time() - t0) > 5:
                        isDrowning = True

                # print('bounding box: ', bbox, 'label: ' label ,'confidence: ' conf[0], 'centre: ', centre)
                # print(bbox,label ,conf, centre)
                print("bbox: ", bbox, "centre:", centre, "centre0:", centre0)
                print("Is he drowning: ", isDrowning)

                centre0 = centre
                # draw bounding box over detected objects

            out = draw_bbox(frame, bbox, label, conf, isDrowning)

            # print('Seconds since last epoch: ', time.time()-t0)

            # display output
            cv2.imshow("Real-time object detection", out)
            print(isDrowning)
            if isDrowning == True:

                playsound("alarm.mp3")

            # press "Q" to stop
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        # release resources
        webcam.release()
        cv2.destroyAllWindows()

        if isDrowning == True:
            return render_template("prediction.html",prediction='Emergency!!! The person is drowning')
        else:
            return render_template("logout.html")
        return render_template("logout.html")
    if request.method == "GET":
        return render_template("prediction.html")
@app.route("/logout", methods=["GET"])
def logout():
    return render_template("logout.html")

if __name__ == "__main__":
    app.run(port=4000,debug=True)
