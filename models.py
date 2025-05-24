import os
from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    DateTime,
    ForeignKey,
    Boolean,
    create_engine,
    text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255))
    last_name = Column(String(255))
    author_uid = Column(String(255), unique=True)
    is_guest = Column(Boolean, default=False)

class CQ(Base):
    __tablename__ = "cq"
    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String(255), unique=True)
    filename = Column(String(255), nullable=False)
    json_data = Column(JSON, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    version = Column(String(50), nullable=False)
    last_update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    access_authorization = Column(String(50), nullable=False)
    author = relationship("User")

class Transcription(Base):
    __tablename__ = "transcription"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    json_data = Column(JSON, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    version = Column(String(50), nullable=False)
    last_update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    access_authorization = Column(String(50), nullable=False)
    author = relationship("User")

class LegacyCQ(Base):
    __tablename__ = "legacy_cq"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    interviewer = Column(Integer, ForeignKey('users.id'), nullable=False)
    consultant = Column(Integer, ForeignKey('users.id'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    version = Column(String(50), nullable=False, default="1")
    last_update_date = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    access_authorization = Column(String(50), nullable=False)
    author = relationship("User")

def get_engine(db_url):
    return create_engine(db_url, echo=True)

def init_db():
    auth_db_url = os.environ.get("AUTH_DATABASE_URL")  # e.g. postgresql://user:pwd@db:5432/auth_db
    cq_db_url = os.environ.get("CQ_DATABASE_URL")  # e.g. postgresql://user:pwd@cq_db:5433/cq_db
    transcription_db_url = os.environ.get("TRANSCRIPTION_DATABASE_URL")  # e.g. postgresql://user:pwd@transcription_db:5434/transcription_db
    lcq_db_url = os.environ.get("LCQ_DATABASE_URL")  # e.g. postgresql://user:pwd@lcq_db:5435/lcq_db

    auth_engine = get_engine(auth_db_url)
    cq_engine = get_engine(cq_db_url)
    transcription_engine = get_engine(transcription_db_url)
    lcq_engine = get_engine(lcq_db_url)

    Base.metadata.create_all(auth_engine)
    Base.metadata.create_all(cq_engine)
    Base.metadata.create_all(transcription_engine)
    Base.metadata.create_all(lcq_engine)

    # Ensure cq table has the filename column
    with cq_engine.begin() as conn:
        result = conn.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name='cq' AND column_name='filename'
                """
            )
        )
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE cq ADD COLUMN filename VARCHAR(255)"))

    # Ensure transcription table has the filename column
    with transcription_engine.begin() as conn:
        result = conn.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name='transcription' AND column_name='filename'
                """
            )
        )
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE transcription ADD COLUMN filename VARCHAR(255)"))

    # Ensure the cq table has the uid column
    with cq_engine.begin() as conn:
        result = conn.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_name='cq' AND column_name='uid'
                """
            )
        )
        if result.fetchone() is None:
            conn.execute(text("ALTER TABLE cq ADD COLUMN uid VARCHAR(255)"))

    # Populate missing uid values from json_data if any exist
    Session = sessionmaker(bind=cq_engine)
    with Session.begin() as session:
        missing_uids = (
            session.query(CQ)
            .filter(CQ.uid.is_(None))
            .all()
        )
        for cq in missing_uids:
            if isinstance(cq.json_data, dict) and "uid" in cq.json_data:
                cq.uid = str(cq.json_data["uid"])

    # Ensure the users table has required columns in all databases
    for engine in (auth_engine, cq_engine, transcription_engine, lcq_engine):
        with engine.begin() as conn:
            existing_columns = {
                row[0]
                for row in conn.execute(
                    text(
                        """
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name='users'
                        """
                    )
                )
            }
            if 'is_guest' not in existing_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_guest BOOLEAN DEFAULT FALSE"))
            if 'first_name' not in existing_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR(255)"))
            if 'last_name' not in existing_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR(255)"))
            if 'author_uid' not in existing_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN author_uid VARCHAR(255) UNIQUE"))

def get_session(db_url):
    engine = get_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()

init_db()  # Initialize the databases when the module is imported
