from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text(), nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_by = relationship("User", backref="authors")

    def __repr__(self):
        return f"<Author ({self.name})>"


class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text(), nullable=False)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    author = relationship("Author", backref="books")
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_by = relationship("User", backref="books")

    def __repr__(self):
        return f"<Book ({self.title})>"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True)
    email = Column(String(256), unique=True)
    is_superuser = Column(Boolean, default=False)
    created_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User (name='{self.username}', email='{self.email}')>"
