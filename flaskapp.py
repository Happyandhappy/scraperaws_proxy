from flask import Flask, render_template, request
import os, uuid, json
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from apscheduler.scheduler import Scheduler
from proxyRequest import ScrapingUnit
import logging
import datetime
logging.basicConfig()
from requests import get

domain = get('https://api.ipify.org').text

path = os.path.dirname(__file__)
app = Flask(__name__)


""""Schedular"""
sched = Scheduler()  # Scheduler object
sched.start()

exportfile = path + "/imports.txt"

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
                fileName = path + "/upload/" + str(uuid.uuid4()) + ".xlsx"
                file.save(fileName)
        email = request.form['email'] if 'email' in request.form else None
        if fileName and email:
            file = open(exportfile, "a")
            file.write(fileName + "|" + email + '\n')
            file.close()
    return json.dumps({"result": "File uploading succeeded! you will get email ( %s ) after finish scraping!" % email})

def sendEmail(email, csvname, start):
    email = email.lstrip().rstrip()
    html = """\
    <html>
      <head></head>
      <body>
        <p>Hi!<br>
           click this url to download result file<br>
           Here is the <a href="http://%s/%s">link</a>
           <br>
           %s - %s
        </p>
      </body>
    </html>
    """ % (domain ,csvname, start, datetime.datetime.now())
    text = "please download result here, %s/%s" % (domain ,csvname)
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Result'
    msg['From'] = "honestdev21@gmail.com"
    msg['To'] = email
    msg.attach(part1)
    msg.attach(part2)

    smtpemail = "honestdev21@gmail.com"
    smtppass="Ahgifrhehdejd"

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(smtpemail, smtppass)
    server.ehlo()
    server.sendmail(smtpemail, [email], msg.as_string())
    server.quit()

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
        excelname = rowdata.split('|')[0]
        email = rowdata.split('|')[1]
        csvname = "static/result/" + str(uuid.uuid4()) + ".csv"
        start = datetime.datetime.now()
        processor = ScrapingUnit(excelname, path + "/" + csvname)
        processor.process()
        sendEmail(email, csvname, start)

# add your job here
sched.add_interval_job(cronJob, seconds=20)
if __name__ == '__main__':
    app.run()