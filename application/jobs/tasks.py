from application.jobs.workers import celery
from datetime import datetime
from celery.schedules import crontab #This is for scheduling a task
from flask import current_app as app  #for logging


from application.data.database import db
from application.data.models import TrackerType, User, Tracker, Log, Onetoone
from application.jobs import send_email


@celery.on_after_configure.connect
def setup_periodic_task(sender, **kwargs):
    sender.add_periodic_task(3600.0, email_reminnder.s("Hourly"), name='Hourly remainder') #60x60=3600
    sender.add_periodic_task(300.0, email_reminnder.s("Daily"), name='Daily remainder') #60x60X24=86400
    sender.add_periodic_task(604800.0, email_reminnder.s("Weekly"), name='Weekly remainder') #60x60X24x7=604800
    sender.add_periodic_task(120.0, email_reminnder.s("Monthly"), name='Monthly remainder') #60x60X24x30=2592000
    #sender.add_periodic_task(crontab(minute=34), print_current_time_job.s(), name='add every 50 sec') #Crontab Import missing



@celery.task()
def print_current_time_job():
    print("START")
    now = datetime.now()
    print("Now in task =", now)
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    print("COMPLETE")
    return dt_string



@celery.task()
def email_reminnder(freq):
    freq = freq
    trackertypes = db.session.query(TrackerType).filter(TrackerType.frequency == freq).all()
    maillist = []
    for trackertype in trackertypes:
        uname = db.session.query(User.uname).filter(User.id == trackertype.uid).first()
        email = db.session.query(User.email).filter(User.id == trackertype.uid).first()
        tname = db.session.query(Tracker.tname).filter(Tracker.tid == trackertype.tid).first()
        maildetails = {"uname":uname[0], "email":email[0], "tname":tname[0]}
        maillist.append(maildetails)
    print("Daily remainder list {}".format(maillist)) #For testing
    send_email.reminderemail(freq=freq, list=maillist)


# Just trying something in GitHub