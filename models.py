import os
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

class CQ(Base):
    __tablename__ = "cq"
    id = Column(Integer, primary_key=True, autoincrement=True)
    json_data = Column(JSON, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    version = Column(String(50), nullable=False)
    last_update_date = Column(DateTime, default=datetime.utcnow)
    access_authorization = Column(String(50), nullable=False)
    author = relationship("User")

class Transcription(Base):
    __tablename__ = "transcription"
    id = Column(Integer, primary_key=True, autoincrement=True)
    json_data = Column(JSON, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    version = Column(String(50), nullable=False)
    last_update_date = Column(DateTime, default=datetime.utcnow)
    access_authorization = Column(String(50), nullable=False)
    author = relationship("User")

def get_engine(db_url):
    return create_engine(db_url, echo=True)

def init_db():
    auth_db_url = os.environ.get("AUTH_DATABASE_URL")  # e.g. postgresql://user:pwd@db:5432/auth_db
    cq_db_url = os.environ.get("CQ_DATABASE_URL")  # e.g. postgresql://user:pwd@cq_db:5433/cq_db
    transcription_db_url = os.environ.get("TRANSCRIPTION_DATABASE_URL")  # e.g. postgresql://user:pwd@transcription_db:5434/transcription_db

    auth_engine = get_engine(auth_db_url)
    cq_engine = get_engine(cq_db_url)
    transcription_engine = get_engine(transcription_db_url)

    Base.metadata.create_all(auth_engine)
    Base.metadata.create_all(cq_engine)
    Base.metadata.create_all(transcription_engine)

def get_session(db_url):
    engine = get_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()

init_db()  # Initialize the databases when the module is imported
