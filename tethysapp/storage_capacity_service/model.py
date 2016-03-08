# Put your persistent store models in this file
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import sessionmaker
import datetime
from .app import StorageCapacityService
from sqlalchemy.types import TypeDecorator, VARCHAR
import json

# DB Engine, sessionmaker and base
engine = StorageCapacityService.get_persistent_store_engine('storage_capacity_service_db')
SessionMaker = sessionmaker(bind=engine)
Base = declarative_base()

# SQLAlchemy ORM definition for the stream_gages table
class JobRecord(Base):
    '''
    Example SQLAlchemy DB Model
    '''
    __tablename__ = 'job_record'

    # Columns
    id = Column(Integer, primary_key=True)
    userid = Column(Integer)

    jobid = Column(String(32))
    xlon = Column(Float)
    ylat = Column(Float)
    prj = Column(String(32))
    damh = Column(Float)
    interval = Column(Float)
    start_time = Column(DateTime, default=datetime.datetime.now)
    start_time_utc = Column(DateTime, default=datetime.datetime.utcnow)


    def __init__(self, userid, jobid, xlon, ylat, prj, damh, interval):
        """
        Constructor for a job_record
        """
        self.userid = userid
        self.jobid = jobid
        self.xlon = xlon
        self.ylat = ylat
        self.prj = prj
        self.damh = damh
        self.interval = interval


class JSONEncodedDict(TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class JobResult(Base):
    '''
    Example SQLAlchemy DB Model
    '''
    __tablename__ = 'job_result'

    # Columns
    id = Column(Integer, primary_key=True)

    jobid = Column(String(32))
    result_dict = Column(JSONEncodedDict())

    stop_time = Column(DateTime, default=datetime.datetime.now)
    stop_time_utc = Column(DateTime, default=datetime.datetime.utcnow)


    def __init__(self, jobid, result_str):
        """
        Constructor for a job_record        """

        self.jobid = jobid
        self.result_dict = result_str



