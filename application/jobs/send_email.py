from email import encoders, message
from email.mime.base import MIMEBase
from re import template
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from unicodedata import name
from jinja2 import Template
from flask import current_app as app  #for logging

import os
current_dir = os.path.abspath(os.path.dirname(__file__))


#Make this read from config
SMTP_SERVER_HOST = "localhost"
SMTP_SERVER_PORT = 1025
SENDER_ADDRESS = "21f1006584@student.onlinedegree.iitm.ac.in"
SENDE_PASSWORD = ""

def sent_email(to_address, subject, message, content="text", attachment_file=None):
    msg = MIMEMultipart()
    msg["From"] = SENDER_ADDRESS
    msg["To"] = to_address
    msg["Subject"] = subject

    if content == "html":
        msg.attach(MIMEText(message, "html"))
    else:
        msg.attach(MIMEText(message, "plain"))

    if attachment_file:
        with open(attachment_file, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")  #Add file as application/octet-stream
            part.set_payload(attachment.read())
        encoders.encode_base64(part)  #Email attachments are sent as base64 encoded
        part.add_header( #From: https://www.ietf.org/rfc/rfc2183.txt regarding attachment and body disposition
            "Content-Disposition", f"attachment: filename= {attachment_file}",
        )
        msg.attach(part)  #Add the attachment to msg

    s = smtplib.SMTP(host=SMTP_SERVER_HOST, port=SMTP_SERVER_PORT)
    s.login(SENDER_ADDRESS, SENDE_PASSWORD)
    s.send_message(msg)
    s.quit()
    return True  #Do a try catch

def format_message(template_file, data={}):
    with open(template_file) as file_:
        template = Template(file_.read())
        return template.render(data=data)
        

def email(): #reference dummy
    new_users = [
        {"name":"Raj", "email":"raj@example.com"},
        {"name":"Anagha", "email":"anagha@example.com"}
    ]
    for user in new_users:
        EMAIL_TEMPLATE_DIR = os.path.join(current_dir, "../../templates/email.html")
        message =format_message(EMAIL_TEMPLATE_DIR, data=user)
        ATTACHMENT_DIR = os.path.join(current_dir, "../../templates/downl.pdf")
        sent_email(user["email"], subject="Log email", message = message, content="html", attachment_file=ATTACHMENT_DIR)


def logsemail(email, uname, tname, logs):
    user = {"name":uname, "email":email, "tname":tname, "logs":logs}
    EMAIL_TEMPLATE_DIR = os.path.join(current_dir, "../../templates/logs.html")
    message =format_message(EMAIL_TEMPLATE_DIR, data=user)
    subject = uname + ", here is your" + tname + " Logs"
    sent_email(to_address=email, subject=subject, message=message, content="html", attachment_file=None)
    app.logger.debug("User Tracker {}".format(user)) #For testing


def reminderemail(freq, list):
    freq = freq
    list = list
    for l in list:
        EMAIL_TEMPLATE_DIR = os.path.join(current_dir, "../../templates/remainderemail.html")
        message =format_message(EMAIL_TEMPLATE_DIR, data=l)
        subject = freq + " Remainder"
        email = l['email']
        sent_email(to_address=email, subject=subject, message=message, content="html", attachment_file=None)
        app.logger.debug("Remainder mail attribute {}".format(l)) #For testing