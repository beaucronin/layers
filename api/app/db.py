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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
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
    payload = Column(JSONB)

    class Config:
        orm_mode = True


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


async def create_reward(username: str, amount: int):
    """Create a reward for a user, including both a reward ledger entry and an increment to the 
    user's XP. This must be done in a transaction (assumed to be handled by the caller)."""
    reward = insert(Rewards).values(
        username=username, amount=amount, created_at=datetime.now()
    )
    bump = update(Users).where(Users.username == username).values(xp = Users.xp + amount)
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
