import os
import databases
from sqlalchemy import (
    create_engine,
    MetaData,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base


DATABASE_URL = os.getenv("DB_CREDS")

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    password = Column(String(150))
    email = Column(String(100))
    is_active = Column(Boolean)
    fullname = Column(String(50))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    active_at = Column(DateTime)

    class Config:
        orm_mode = True


class ObservationEvents(Base):
    __tablename__ = "observation_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    # the observer, as contained in the body of the observation; this should match the logged in user
    observer = Column(String(50))
    source = Column(String(50))
    observed_at = Column(DateTime)
    submitted_at = Column(DateTime)
    location = Column(JSONB)
    observation_count = Column(Integer)

    class Config:
        orm_mode = True


class Observations(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("observation_events.id"))
    observation_type = Column(Enum("asset", "facility", "resource", "transport", name="observation_type"))
    payload = Column(JSONB)

    class Config:
        orm_mode = True


engine = create_engine(DATABASE_URL)
db = databases.Database(DATABASE_URL)

metadata.create_all(engine)

