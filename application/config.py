import os
current_dir = os.path.abspath(os.path.dirname(__file__))

class Config():
    DEBUG = False
    SQLITE_DB_DIR = None
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    SECURITY_TOKEN_AUTHENTICATION_HEADER = "Authentication-Token"
    CELERY_BROKER_URL = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_HOST = "localhost"
    CACHE_REDIS_PORT = 6379

class LocalDevelopmentConfig(Config):
    DEBUG = True
    SQLITE_DB_DIR = os.path.join(current_dir, "../db_directory")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(SQLITE_DB_DIR, "testdb.sqlite3")
    #didn't work while given another name for db file ("trackerdb.sqlite3" instead of "testdb.sqlite3")
    SECRET_KEY = "njkdf367ncnvg"
    SECURITY_PASSWORD_HASH = "bcrypt"
    SECURITY_PASSWORD_SALT = "fjhbhf7985jfjh"
    #better to set key and salt in the os environment and read from there
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_UNAUTHORIZED_VIEW = None
    SECURITY_POST_LOGIN_VIEW = "/you"
    SECURITY_POST_REGISTER_VIEW = "/logout"
    CELERY_BROKER_URL = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/2"
    CACHE_TYPE = "RedisCache"
    CACHE_REDIS_HOST = "localhost"
    CACHE_REDIS_PORT = 6379

#another config for production version
#class ProductionConfig(Config):
#    DEBUG = False
#    SQLITE_DB_DIR = os.path.join(current_dir, "../db_directory")
#    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(SQLITE_DB_DIR, "productiondb.sqlite3")