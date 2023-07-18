from os import uname
from flask_restful import Resource
from flask_restful import fields, marshal_with
from flask_restful import reqparse
from flask import current_app as app
from flask_security import auth_required, login_required, current_user
from time import perf_counter_ns

from application.data.database import db
from application.data.models import TrackerType, User, Tracker, Log, Onetoone
from application.data import data_access
from application.utils.validation import NotFoundError, UserValidationError
from application.jobs import send_email



# all output formats as in API schemas
useremail_fields = {"email" : fields.String}
user_fields = {"id"  : fields.Integer,
                "uname" : fields.String,
                "email" : fields.String,
                "password"   : fields.String,
                "gender"   : fields.String,
                "dob"   : fields.String}
tracker_fields = {"tid"  : fields.Integer,
                "tname" : fields.String,
                "description" : fields.String}
trackers_fields = {"trackers": fields.List(fields.Nested(tracker_fields))}
usertrackers_fields = {"id"  : fields.Integer,
                        "uname" : fields.String,
                        "email" : fields.String,
                        "password"   : fields.String,
                        "gender"   : fields.String,
                        "dob"   : fields.String,
                        "trackers": fields.List(fields.Nested(tracker_fields))}
type_fields = {"type"  : fields.String,
                "unit" : fields.String,
                "frequency" : fields.String}
trackertype_fields = {"user" : fields.Nested(useremail_fields),
                    "tracker" : fields.Nested(tracker_fields),
                    "type"  : fields.String,
                    "unit" : fields.String,
                    "frequency" : fields.String}
trackertypes_fields = {"trackertypes": fields.List(fields.Nested(trackertype_fields))}
log_fields = {"lid" : fields.Integer,
                "oneid"  : fields.Integer,
                "timestamp"  : fields.String, #need to change to DateTime format curresponding to format of the form
                "value" : fields.Integer,
                "comment" : fields.String}
logs_fields = {"logs": fields.List(fields.Nested(log_fields))}
trackertypelogs_fields = {"trackertype" : fields.Nested(trackertype_fields),
                        "logs" : fields.List(fields.Nested(log_fields))}




create_user_parser = reqparse.RequestParser()
create_user_parser.add_argument('uname')
create_user_parser.add_argument('email')
create_user_parser.add_argument('password')
create_user_parser.add_argument('gender')
create_user_parser.add_argument('dob')

update_user_parser = reqparse.RequestParser()
update_user_parser.add_argument('uname')
update_user_parser.add_argument('gender')
update_user_parser.add_argument('dob')

create_trackertype_parser = reqparse.RequestParser()
create_trackertype_parser.add_argument('email')
create_trackertype_parser.add_argument('tname')
create_trackertype_parser.add_argument('description')
create_trackertype_parser.add_argument('type')
create_trackertype_parser.add_argument('unit')
create_trackertype_parser.add_argument('frequency')

class UserAPI(Resource):
    @auth_required("token")
    @marshal_with(usertrackers_fields)
    def get(self, email):
        user = db.session.query(User).filter(User.email == email).first() #First not nescessary as email constraint is unique
        #tracker = Tracker.query.filter(Tracker.users.any(email=email)), tracker is available without any query (maybe because of relationship in model)
        if user: # if user exist return it in JASON format otherwise return error code
            return user # Format the return JASON
        else:
            raise NotFoundError(status_code=404) # because marshel will try jason even for null user

    @marshal_with(user_fields)
    def put(self, email):
        args = update_user_parser.parse_args()
        uname = args.get("uname", None)
        gender = args.get("gender", None)
        dob = args.get("dob", None)

        if uname is None:
            raise UserValidationError(status_code=400, error_code="U1001", error_message="username required")

        user = db.session.query(User).filter(User.email == email).first()#Check wether the user exists
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        user.uname = uname
        user.gender = gender
        user.dob = dob
        db.session.add(user)
        db.session.commit()
        return user

    
    def delete(self, email):
        user = db.session.query(User).filter(User.email == email).first()#Check wether the user exists
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        '''trackers = Tracker.query.filter(Tracker.users.any(email=user)) #If user exists check whether any trackertype associated with the user and are there any logs for that trackertype
        if trackers is None:
            pass
        else:
            for tracker in trackers:
                logs = #query for getting logs of that that tracker
                if logs is None:
                    pass
                else:
                    db.session.delete(logs)
                    db.session.commit()
            db.session.delete(trackers)
            db.session.commit()
        '''
        db.session.delete(user) #Deletes trackertype associated with it, but not respective ontonone and logs. Need to add relations for them (2 foreign key of onetoone is causing some issue)
        db.session.commit()
        return "", 200

    def post(self): #cannot find way to hash the submitted password yet. So not adviced to add user from API
        args = create_user_parser.parse_args()
        uname = args.get("uname", None)
        email = args.get("email", None)
        password = args.get("password", None)
        gender = args.get("gender", None)
        dob = args.get("dob", None)

        if uname is None:
            raise UserValidationError(status_code=400, error_code="U1001", error_message="username required")

        if email is None:
            raise UserValidationError(status_code=400, error_code="U1002", error_message="email required")
        
        if "@" in email:
            pass
        else:
            raise UserValidationError(status_code=400, error_code="U1003", error_message="invalid email")

        user = db.session.query(User).filter(User.email == email).first()
        if user:
            raise UserValidationError(status_code=400, error_code="U1004", error_message="duplicate email")

        new_user = User(uname=uname, email=email, password=password, gender=gender, dob=dob)
        db.session.add(new_user)
        db.session.commit()
        return "", 201

    def post(self, email): #This is for creating new trackertype
        args = create_trackertype_parser.parse_args()
        email = args.get("email", None)
        tname = args.get("tname", None)
        type = args.get("type", None)
        unit = args.get("unit", None)
        frequency = args.get("frequency", None)

        if email is None:
            raise UserValidationError(status_code=400, error_code="U1002", error_message="email required")
        if tname is None:
            raise UserValidationError(status_code=400, error_code="T1001", error_message="trackername is required")
        if type is None:
            raise UserValidationError(status_code=400, error_code="T1007", error_message="tracker type is required")
        if unit is None:
            raise UserValidationError(status_code=400, error_code="T1002", error_message="tracker unit is required")
        if frequency is None:
            raise UserValidationError(status_code=400, error_code="T1003", error_message="tracking frequency is required")

        user = db.session.query(User).filter(User.email == email).first()
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        uid = user.id

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        tid = tracker.tid
        #NEED TO ADD AN ERROR HANDLER FOR PRIMARY KEY CONSTRAIN OF TRACKERTYPE

        new_trackertype = TrackerType(tid=tid, uid=uid, type=type, unit=unit, frequency=frequency)
        new_onetoone = Onetoone(tid=tid, uid=uid)
        db.session.add(new_trackertype)
        db.session.add(new_onetoone)
        db.session.commit() 
        return "", 201
        


class TrackersAPI(Resource): #API to get all the trackers
    @marshal_with(tracker_fields)
    def get(self): #To get all the trackers
        start_time = perf_counter_ns()
        trackers = data_access.get_all_trackers()
        stop_time = perf_counter_ns()
        print("Time taken for get all trackers from db or cache: ", stop_time - start_time)
        if trackers: # if tracker exist return it in JASON format otherwise return error code
            return trackers # Format the return JASON
        else:
            raise NotFoundError(status_code=404) # because marshel will try jason even for null user






create_tracker_parser = reqparse.RequestParser()
create_tracker_parser.add_argument('tname')
create_tracker_parser.add_argument('description')

update_tracker_parser = reqparse.RequestParser()
update_tracker_parser.add_argument('description')

class TrackerAPI(Resource):
    @marshal_with(tracker_fields)
    def get(self, tname):
        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first() #First not nescessary as tname constraint is unique
        if tracker: # if tracker exist return it in JASON format otherwise return error code
            return tracker # Format the return JASON
        else:
            raise NotFoundError(status_code=404) # because marshel will try jason even for null user

    @marshal_with(tracker_fields)
    def put(self, tname):
        args = update_tracker_parser.parse_args()
        description = args.get("description", None)

        if description is None:
            raise UserValidationError(status_code=400, error_code="T1004", error_message="description required")

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()#Check wether the tracker exists
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the tracker does not exist
        tracker.description = description
        db.session.add(tracker)
        db.session.commit()
        return tracker
        
    def delete(self, tname): #Should delete only if no user have a trackertype of this tracker
        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker:
            tid = tracker.tid
            trackertype = db.session.query(TrackerType).filter(TrackerType.tid == tid).first()
            if trackertype:
                raise UserValidationError(status_code=400, error_code="T1006", error_message="cannot delete a tracker that is in use")
            else:
                db.session.delete(tracker)
                db.session.commit()
                return "", 200
        else:
            raise NotFoundError(status_code=404)#Return error if the tracker does not exist

        
    def post(self):
        args = create_tracker_parser.parse_args()
        tname = args.get("tname", None)
        description = args.get("description", None)

        if tname is None:
            raise UserValidationError(status_code=400, error_code="T1001", error_message="Tracker name required")

        if description is None:
            raise UserValidationError(status_code=400, error_code="T1004", error_message="Description required") #Error code not in API document
        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker:
            raise UserValidationError(status_code=400, error_code="T1005", error_message="duplicate tracker") #Error code not in API document

        new_tracker = Tracker(tname=tname, description=description)
        db.session.add(new_tracker)
        db.session.commit()
        return "", 201
    

update_trackertype_parser = reqparse.RequestParser()
update_trackertype_parser.add_argument('unit')

create_log_parser = reqparse.RequestParser()
create_log_parser.add_argument('oneid')
create_log_parser.add_argument('timestamp')
create_log_parser.add_argument('value')
create_log_parser.add_argument('comment')


class TrackerTypeAPI(Resource):
    @marshal_with(trackertype_fields)
    def get(self, email, tname):
        user = db.session.query(User).filter(User.email == email).first()
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        uid = user.id

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        tid = tracker.tid

        trackertype = db.session.query(TrackerType).filter(TrackerType.tid==tid, TrackerType.uid==uid).first()
        if trackertype: # if tracker exist return it in JASON format otherwise return error code
            return trackertype # Format the return JASON
        else:
            raise NotFoundError(status_code=404) # because marshel will try jason even for null user


    @marshal_with(trackertype_fields)
    def put(self, email, tname):
        args = update_trackertype_parser.parse_args()
        unit = args.get("unit", None)
        if unit is None:
            raise UserValidationError(status_code=400, error_code="T1002", error_message="unit required")

        user = db.session.query(User).filter(User.email == email).first()
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        uid = user.id

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        tid = tracker.tid

        trackertype = db.session.query(TrackerType).filter(TrackerType.tid==tid, TrackerType.uid==uid).first()
        if trackertype is None:
            raise NotFoundError(status_code=404)#Return error if the tracker does not exist
        trackertype.unit = unit
        db.session.add(trackertype)
        db.session.commit()
        return trackertype
        

    '''def delete(self, email, tname):
        user = db.session.query(User).filter(User.email == email).first()
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        uid = user.id

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        tid = tracker.tid

        trackertype = db.session.query(TrackerType).filter(TrackerType.tid==tid, TrackerType.uid==uid).first()
        if trackertype:
            onetoone = db.session.query(Onetoone).filter(Onetoone.tid==tid, Onetoone.uid==uid).first()
            oneid = onetoone.oneid
            logs = db.session.query(Log).filter(Log.oneid==oneid).all()
            if logs:
                db.session.delete(logs)
                db.session.commit()
            db.session.delete(onetoone)
            db.session.delete(trackertype)
            db.session.commit
            return "", 200
        else:
            raise NotFoundError(status_code=404)#Return error if the tracker does not exist'''

    def post(self, email, tname): #This is for posting log
        args = create_log_parser.parse_args()
        oneid = args.get("oneid", None) #This oneid is overriden latter as it is easy to check whether the trackertype exist
        timestamp = args.get("timestamp", None)
        value = args.get("value", None)
        comment = args.get("comment", None)

        if oneid is None:
            raise UserValidationError(status_code=400, error_code="L1002", error_message="oneid required")
        if value is None:
            raise UserValidationError(status_code=400, error_code="L1001", error_message="value is required")
        if timestamp is None:
            raise UserValidationError(status_code=400, error_code="L1001", error_message="timestamp is required")
        
        user = db.session.query(User).filter(User.email == email).first()
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        uid = user.id

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the tracker does not exist
        tid = tracker.tid

        onetoone = db.session.query(Onetoone).filter(Onetoone.tid==tid, Onetoone.uid==uid).first()
        if onetoone is None:
            raise NotFoundError(status_code=404)#Return error if the trackertype does not exist
        oneid = onetoone.oneid

        new_log = Log(oneid=oneid, timestamp=timestamp, value=value, comment=comment)
        db.session.add(new_log)
        db.session.commit() 
        return "", 201
        

update_log_parser = reqparse.RequestParser()
update_log_parser.add_argument('oneid')
update_log_parser.add_argument('timestamp')
update_log_parser.add_argument('value')
update_log_parser.add_argument('comment')

class LogAPI(Resource):
    @marshal_with(log_fields)
    def get(self, email, tname, log):
        user = db.session.query(User).filter(User.email == email).first()
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        uid = user.id

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        tid = tracker.tid

        onetoone = db.session.query(Onetoone).filter(Onetoone.tid==tid, Onetoone.uid==uid).first()
        if onetoone is None:
            raise NotFoundError(status_code=404)#Return error if the trackertype does not exist
        oneid = onetoone.oneid

        log = db.session.query(Log).filter(Log.oneid==oneid, Log.lid==log).first()
        if log: # if log exist return it in JASON format otherwise return error code
            return log # Format the return JASON
        else:
            raise NotFoundError(status_code=404) # because marshel will try jason even for null user
 
    @marshal_with(log_fields)
    def put(self, email, tname, log):
        args = update_log_parser.parse_args()
        oneid = args.get("oneid", None) #This oneid is overriden latter as it is easy to check whether the trackertype exist
        timestamp = args.get("timestamp", None)
        value = args.get("value", None)
        comment = args.get("comment", None)
        
        #if oneid is None:
        #    raise UserValidationError(status_code=400, error_code="L1002", error_message="oneid required")
        if value is None:
            raise UserValidationError(status_code=400, error_code="L1001", error_message="value is required")
        if timestamp is None:
            raise UserValidationError(status_code=400, error_code="L1001", error_message="timestamp is required")
        
        user = db.session.query(User).filter(User.email == email).first()
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        uid = user.id

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the tracker does not exist
        tid = tracker.tid

        onetoone = db.session.query(Onetoone).filter(Onetoone.tid==tid, Onetoone.uid==uid).first()
        if onetoone is None:
            raise NotFoundError(status_code=404)#Return error if the trackertype does not exist
        oneid = onetoone.oneid

        log = db.session.query(Log).filter(Log.oneid==oneid, Log.lid==log).first()
        if log is None:
            raise NotFoundError(status_code=404)#Return error if the tracker does not exist
        log.timestamp = timestamp
        log.value = value
        log.comment = comment
        db.session.add(log)
        db.session.commit()
        return log


    def delete(self, email, tname, log):
        user = db.session.query(User).filter(User.email == email).first()
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        uid = user.id

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the tracker does not exist
        tid = tracker.tid

        onetoone = db.session.query(Onetoone).filter(Onetoone.tid==tid, Onetoone.uid==uid).first()
        if onetoone is None:
            raise NotFoundError(status_code=404)#Return error if the trackertype does not exist
        oneid = onetoone.oneid

        log = db.session.query(Log).filter(Log.oneid==oneid, Log.lid==log).first()
        if log is None:
            raise NotFoundError(status_code=404)#Return error if the tracker does not exist
        db.session.delete(log)
        db.session.commit()
        return "", 200

    @auth_required("token")
    @marshal_with(log_fields)
    def get(self, email, tname): #To get all logs of same oneid
        user = db.session.query(User).filter(User.email == email).first()
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        uid = user.id

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        tid = tracker.tid

        onetoone = db.session.query(Onetoone).filter(Onetoone.tid==tid, Onetoone.uid==uid).first()
        if onetoone is None:
            raise NotFoundError(status_code=404)#Return error if the trackertype does not exist
        oneid = onetoone.oneid

        logs = db.session.query(Log).filter(Log.oneid==oneid).order_by(Log.timestamp).all()
        if logs: # if log exist return it in JASON format otherwise return error code
            return logs # Format the return JASON
        else:
            raise NotFoundError(status_code=404) # because marshel will try jason even for null user




class TaskAPI(Resource):
    def get(self, email, tname): #To get all logs og same oneid
        user = db.session.query(User).filter(User.email == email).first()
        if user is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        uid = user.id
        uname = user.uname

        tracker = db.session.query(Tracker).filter(Tracker.tname == tname).first()
        if tracker is None:
            raise NotFoundError(status_code=404)#Return error if the user does not exist
        tid = tracker.tid

        onetoone = db.session.query(Onetoone).filter(Onetoone.tid==tid, Onetoone.uid==uid).first()
        if onetoone is None:
            raise NotFoundError(status_code=404)#Return error if the trackertype does not exist
        oneid = onetoone.oneid

        logs = db.session.query(Log).filter(Log.oneid==oneid).order_by(Log.timestamp).all()
        send_email.logsemail(email=email, uname=uname, tname=tname, logs=logs)
        return "", 200
