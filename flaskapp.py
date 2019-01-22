from flask import Flask, render_template, request
import os, uuid, json
import smtplib, ssl
from email.mime.text import MIMEText

from apscheduler.scheduler import Scheduler
from proxyRequest import ScrapingUnit
import socket

domain = socket.getfqdn()

path = os.path.dirname(__file__)
app = Flask(__name__)


""""Schedular"""
sched = Scheduler()  # Scheduler object
sched.start()

exportfile = "imports.txt"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        if 'file' in request.files:
            uploadsFiles = request.files.getlist("file")
            fileName = None
            for file in uploadsFiles:
                fileName = "upload/" + str(uuid.uuid4()) + ".xlsx"
                file.save(fileName)
        email = request.form['email'] if 'email' in request.form else None
        if fileName and email:
            file = open(exportfile, "a")
            file.write(fileName + ":" + email + '\n')
            file.close()
    return json.dumps({"result": "File uploading succeeded! you will get email ( %s ) after finish scraping!" % email})

def sendEmail(email, csvname):
    msg = MIMEText("please download result here, %s/%s" % (domain ,csvname))
    msg['Subject'] = 'Result'
    msg['From'] = "honestdev21@gmail.com"
    msg['To'] = email

    email = email.lstrip().rstrip()
    smtpemail = "honestdev21@gmail.com"
    smtppass="Ahgifrhehdejd"

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(smtpemail, smtppass)
    server.ehlo()
    server.sendmail(smtpemail, [email], msg.as_string())

def cronJob():
    lines = open(exportfile, 'r').readlines()
    flag = 0
    rowdata = None
    remaining = ""
    for line in lines:
        if flag == 0:
            rowdata = line
            flag = 1
        else:
            remaining += line
    f = open(exportfile, "w")
    f.write(remaining)
    f.close()
    if rowdata:
        excelname = rowdata.split(':')[0]
        email = rowdata.split(':')[1]
        csvname = "static/result/" + str(uuid.uuid4()) + ".csv"
        processor = ScrapingUnit(excelname, csvname)
        processor.process()
        sendEmail(email, csvname)

# add your job here
sched.add_interval_job(cronJob, seconds=20)
if __name__ == '__main__':
    app.run()