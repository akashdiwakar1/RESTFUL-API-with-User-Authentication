from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DATABASE_URL = "postgresql://postgres:postgres@localhost/firstappDB"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Taskit(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    description = Column(String)
    project_id = Column(Integer)
    completed = Column(Boolean)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    owner = Column(String)

Base.metadata.create_all(bind=engine)
