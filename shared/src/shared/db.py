from typing import List
import os
import databases
from datetime import datetime
from sqlalchemy import (
    select,
    insert,
    update,
    create_engine,
    MetaData,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship, Mapped, declarative_base
from sqlalchemy.dialects.postgresql import JSONB

# from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from .util import level_for_xp

DATABASE_URL = os.getenv("DB_CREDS")

metadata = MetaData()
Base = declarative_base(metadata=metadata)
engine = create_engine(DATABASE_URL)
db = databases.Database(DATABASE_URL)


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    password = Column(String(150))
    email = Column(String(100))
    fullname = Column(String(50))
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    active_at = Column(DateTime)
    disabled = Column(Boolean)
    xp = Column(Integer)
    level = Column(Integer)

    class Config:
        orm_mode = True


class UserStats(Base):
    __tablename__ = "user_stats"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True))
    counts_alltime = Column(JSONB)
    counts_1day = Column(JSONB)
    counts_7days = Column(JSONB)
    counts_30days = Column(JSONB)
    counts_90days = Column(JSONB)
    counts_365days = Column(JSONB)
    last_observation = Column(DateTime)

    class Config:
        orm_mode = True


class ObservationEvents(Base):
    __tablename__ = "observation_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(String(50))
    # the observer, as contained in the body of the observation; this should match the logged in user
    observer = Column(String(50))
    source = Column(String(50))
    observed_at = Column(DateTime)
    submitted_at = Column(DateTime)
    location = Column(JSONB)
    observation_count = Column(Integer)
    geo = Column(Geometry(geometry_type="POINT", srid=4326))
    observations = relationship("Observations", back_populates="event")

    class Config:
        orm_mode = True


class Observations(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("observation_events.id"))
    observation_type = Column(
        Enum(
            "asset",
            "facility",
            "resource",
            "transport",
            "extent",
            "",
            name="observation_type",
        )
    )
    geo = Column(Geometry(geometry_type="POLYGON", srid=4326))
    payload = Column(JSONB)
    event = relationship("ObservationEvents", back_populates="observations")
    entities = relationship("EntityObservation", back_populates="observation")

    class Config:
        orm_mode = True


class Entity(Base):
    __tablename__ = "entities"
    id = Column(Integer, primary_key=True)
    entity_type = Column(
        Enum("asset", "facility", "resource", "extent", name="entity_type")
    )
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    latest_observation_at = Column(DateTime(timezone=True))
    geo = Column(Geometry(geometry_type="POLYGON", srid=4326))
    data = Column(JSONB)
    observations = relationship("EntityObservation", back_populates="entity")
    identifiers = relationship("EntityIdentifier", back_populates="entity")

    class Config:
        orm_mode = True


class EntityObservation(Base):
    """A many-to-many relationship between entities and observations."""

    __tablename__ = "entities_observations"
    entity_id = Column(Integer, ForeignKey("entities.id"), primary_key=True)
    observation_id = Column(Integer, ForeignKey("observations.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True))
    status = Column(Enum("active", "inactive", name="entity_observation_status"))
    entity = relationship("Entity", back_populates="observations")
    observation = relationship("Observations", back_populates="entities")


class EntityIdentifier(Base):
    """The various kinds of identifiers that can be associated with an entity. These include
    - government-issued (e.g., license plates),
    - manufacturer-issued (e.g., serial numbers, VINs),
    - operator-issued (e.g., asset tags, fleet numbers), and
    - end-user-issued (e.g., nicknames or common names)
    """

    __tablename__ = "entity_identifiers"
    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey("entities.id"))
    issuer_type = Column(
        Enum("government", "manufacturer", "operator", "end-user", name="issuer_type")
    )
    issuer = Column(String(250))
    identifier = Column(String(250))
    identifier_canonical = Column(String(250))
    entity = relationship("Entity", back_populates="identifiers")


class Entries(Base):
    """A ledger of all transactions between users."""

    __tablename__ = "entries"
    id = Column(Integer, primary_key=True)
    from_account_id = Column(Integer, ForeignKey("accounts.id"))
    to_account_id = Column(Integer, ForeignKey("accounts.id"))
    from_username = Column(String(50))
    to_username = Column(String(50))
    amount = Column(Integer)
    created_at = Column(DateTime(timezone=True))
    txtype = Column(String(50))
    txdata = Column(JSONB)

    class Config:
        orm_mode = True


class Accounts(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    balance = Column(Integer)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))

    class Config:
        orm_mode = True


class Rewards(Base):
    __tablename__ = "rewards"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    amount = Column(Integer)
    created_at = Column(DateTime(timezone=True))
    observation_event_id = Column(Integer, ForeignKey("observation_events.id"))


async def create_reward(username: str, amount: int, event_id: int):
    """Create a reward for a user, including both a reward ledger entry and an increment to the
    user's XP. This must be done in a transaction (assumed to be handled by the caller)."""
    reward = insert(Rewards).values(
        username=username,
        amount=amount,
        observation_event_id=event_id,
        created_at=datetime.now(),
    )
    bump = update(Users).where(Users.username == username).values(xp=Users.xp + amount)
    await db.execute(reward)
    await db.execute(bump)


async def create_transaction(
    from_username: str, to_username: str, amount: int, txtype: str
):
    """Create a transaction. This requires inserting a new entry into the ledger, and updating the
    balance of the from and to accounts."""

    # For now, assume each user has a single account.
    from_account = await db.fetch_one(
        select(Accounts).filter(Accounts.username == from_username)
    )
    to_account = await db.fetch_one(
        select(Accounts).filter(Accounts.username == to_username)
    )

    if from_account.balance < amount:
        # insufficient funds
        raise Exception("Insufficient funds")

    entry = insert(Entries).values(
        from_account_id=from_account.id,
        to_account_id=to_account.id,
        from_username=from_username,
        to_username=to_username,
        amount=amount,
        created_at=datetime.now(),
        txtype=txtype,
    )
    debit = (
        update(Accounts)
        .where(Accounts.id == from_account.id)
        .values(balance=Accounts.balance - amount)
    )
    credit = (
        update(Accounts)
        .where(Accounts.id == to_account.id)
        .values(balance=Accounts.balance + amount)
    )
    await db.execute(entry)
    await db.execute(debit)
    await db.execute(credit)


async def maybe_increase_level(username) -> bool:
    """Increase the level of a user if they have enough XP."""
    user = await db.fetch_one(select(Users).filter(Users.username == username))
    new_level = level_for_xp(user.xp)
    if new_level > user.level:
        await db.execute(
            update(Users).where(Users.username == username).values(level=new_level)
        )
        return True
    return False
