from sqlalchemy import ForeignKey, LargeBinary, Column, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY
from datetime import datetime
from app import Config

from . import db
from geoalchemy2 import Geometry
from typing import Final

OS_NATIONAL_GRID: Final = 27700


class BaseModel(db.Model):
    __abstract__ = True
    creation_timestamp = db.Column(db.DateTime())
    def __init__(self, **kwargs):
        super(BaseModel, self).__init__(**kwargs)
        self.tenant = None
        self.creation_timestamp = datetime.utcnow()


class TestModel(BaseModel):
    """this is a public model"""
    __tablename__ = 'users'
    name = Column(Integer, primary_key=True)


class TestModel2(BaseModel):
    """this is tenant"""
    __tablename__ = 'tenent_users'
    name = Column(Integer, primary_key=True)