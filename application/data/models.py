from enum import unique
from .database import db
from flask_security import UserMixin, RoleMixin
from sqlalchemy.orm import backref # https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html

roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    uname = db.Column(db.String)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    gender = db.Column(db.Integer)
    dob = db.Column(db.Integer)
    fs_uniquifier = db.Column(db.String(255), unique = True, nullable=False)
    trackers = db.relationship("Tracker", secondary="trackertype") #This will conflict with users in Tracker
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))
    #trackertype = db.relationship('TrackerType', back_populates="user")

class Role(db.Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class Tracker(db.Model):
    __tablename__ = 'tracker'
    tid = db.Column(db.Integer, autoincrement=True, primary_key=True)
    tname = db.Column(db.String, nullable=False, unique=True)
    description = db.Column(db.String, nullable=False)
    #users = db.relationship("User", secondary="trackertype") #This is need for flask template rendering, may conflict some API need to check
    #trackertype = db.relationship('TrackerType', back_populates="tracker")
    
class TrackerType(db.Model):
    __tablename__ = 'trackertype'
    tid = db.Column(db.Integer, db.ForeignKey("tracker.tid"), primary_key=True, nullable=False)
    uid = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True, nullable=False)
    type = db.Column(db.String, nullable=False)
    unit = db.Column(db.String, nullable=False)
    frequency = db.Column(db.String, nullable=False)
    user = db.relationship('User', overlaps="trackers,users")
    tracker = db.relationship('Tracker', overlaps="trackers,users")

# Couldn't find a way to effectively map one-to-many relationship of 'trackrtype' with composite primary key
# So an intermediate one-to-one table is formed
class Onetoone(db.Model):
    __tablename__ = 'onetoone'
    oneid = db.Column(db.Integer, autoincrement=True, primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey("trackertype.tid"), nullable=False)
    uid = db.Column(db.Integer, db.ForeignKey("trackertype.uid"), nullable=False)
    logs = db.relationship("Log")

class Log(db.Model):
    __tablename__ = 'log'
    lid = db.Column(db.Integer, primary_key=True, nullable=False)
    oneid = db.Column(db.Integer, db.ForeignKey("onetoone.oneid"), nullable=False)
    timestamp = db.Column(db.String, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String)