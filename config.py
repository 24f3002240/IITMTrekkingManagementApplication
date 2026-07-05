import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'trekking.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_NAME = 'Administrator'
    ADMIN_EMAIL = 'avinash732004kumar@gmail.com'
    ADMIN_PASSWORD = '@Jh00302000'
    
