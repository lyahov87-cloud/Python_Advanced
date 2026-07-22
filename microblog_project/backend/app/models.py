from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, String, Text, Table, Column, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# Таблица связей для подписчиков (многие-ко-многим)
followers = Table(
    "followers",
    Base.metadata,
    Column("follower_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("following_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)

# Таблица связей для лайков (многие-ко-многим)
likes = Table(
    "likes",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("tweet_id", Integer, ForeignKey("tweets.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    api_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    tweets: Mapped[List["Tweet"]] = relationship("Tweet", back_populates="user", cascade="all, delete-orphan")

    following: Mapped[List["User"]] = relationship(
        "User",
        secondary=followers,
        primaryjoin=(id == followers.c.follower_id),
        secondaryjoin=(id == followers.c.following_id),
        back_populates="followers_list",
    )
    followers_list: Mapped[List["User"]] = relationship(
        "User",
        secondary=followers,
        primaryjoin=(id == followers.c.following_id),
        secondaryjoin=(id == followers.c.follower_id),
        back_populates="following",
    )


class Tweet(Base):
    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="tweets")
    attachments: Mapped[List["Media"]] = relationship("Media", back_populates="tweet", cascade="all, delete-orphan")
    liked_by: Mapped[List["User"]] = relationship("User", secondary=likes)


class Media(Base):
    __tablename__ = "medias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    tweet_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tweets.id", ondelete="SET NULL"), nullable=True)

    tweet: Mapped[Optional["Tweet"]] = relationship("Tweet", back_populates="attachments")
