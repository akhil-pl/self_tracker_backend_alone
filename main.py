import os
import secrets
from flask import Flask
from flask_restful import Resource, Api
from application import config
from application.config import LocalDevelopmentConfig
from application.data.database import db
from application.jobs import workers
from flask_security import Security, SQLAlchemySessionUserDatastore, SQLAlchemyUserDatastore
from application.data.models import User, Role
import logging
from flask_cors import CORS
logging.basicConfig(filename='debug.log', level=logging.DEBUG, format=f'%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
from flask_caching import Cache


#customizing default flask-security templates and forms
#custom register form
from flask_security import RegisterForm
from wtforms import StringField
from wtforms.validators import DataRequired
class ExtendedRegisterForm(RegisterForm):
    uname = StringField('Name', [DataRequired()])
    gender = StringField('Gender', [DataRequired()])
    dob = StringField('Date of Birth', [DataRequired()])
    fs_uniquifier = StringField('Please login after registering', [DataRequired()])
    

app = None
api = None
celery = None
cache = None

def create_app():
    app = Flask(__name__, template_folder="templates")
    if os.getenv('ENV', "development") == "production":
        raise Exception("Currently there is no production setup")
    else:
        print("Starting Local Development")
        app.config.from_object(LocalDevelopmentConfig)
    app.app_context().push()
    db.init_app(app)
    app.app_context().push()
    user_datastore = SQLAlchemySessionUserDatastore(db.session, User, Role)
    security = Security(app, user_datastore, register_form=ExtendedRegisterForm)
    CORS(app)
    
    celery = workers.celery #Create celery
    celery.conf.update(
        broker_url = app.config["CELERY_BROKER_URL"],
        result_backend = app.config["CELERY_RESULT_BACKEND"]
    )
    celery.Task = workers.ContextTask
    app.app_context().push()
    cache = Cache(app)
    app.app_context().push()
    api = Api(app)
    app.app_context().push()
    
    return app, api, celery, cache

app, api, celery, cache = create_app()

#Importing all controllers
from application.controller.controllers import *

#Adding all restfull controllers
from application.controller.api import UserAPI, TrackersAPI, TrackerAPI, TrackerTypeAPI, LogAPI, TaskAPI
api.add_resource(UserAPI, "/user", "/user/<string:email>")
api.add_resource(TrackersAPI, "/trackers")
api.add_resource(TrackerAPI, "/tracker", "/tracker/<string:tname>")
api.add_resource(TrackerTypeAPI, "/user/<string:email>/<string:tname>")
api.add_resource(LogAPI, "/user/<string:email>/<string:tname>/<string:log>", "/user/<string:email>/<string:tname>/logs")
api.add_resource(TaskAPI, "/task/<string:email>/<string:tname>/logs")



#will take to this page if 404 error occurs
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8080
    )