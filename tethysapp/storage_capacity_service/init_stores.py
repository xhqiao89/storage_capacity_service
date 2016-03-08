# Put your persistent store initializer functions in here
from .model import engine, Base

def init_storage_capacity_service_db(first_time):
    """
    An example persistent store initializer function
    """
    # Create tables
    Base.metadata.create_all(engine)

