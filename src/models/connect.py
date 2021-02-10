from mongoengine import connect

from src.config import load_config


def connect_db():
    conf = load_config().db
    connect(host=conf.host, port=conf.port, db=conf.db)