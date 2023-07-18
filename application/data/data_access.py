from application.data.models import TrackerType, User, Tracker, Log, Onetoone
from application.data.database import db
from main import cache

@cache.cached(timeout=50, key_prefix='get_all_trackers')
def get_all_trackers():
    trackers = db.session.query(Tracker).order_by(Tracker.tname).all()
    return trackers