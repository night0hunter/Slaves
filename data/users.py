import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, 
                           primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    money = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    parent_id = sqlalchemy.Column(sqlalchemy.Integer, 
                              index=True, nullable=True)
    count_slaves = sqlalchemy.Column(sqlalchemy.Integer, 
                              index=True, nullable=True)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, 
                                     default=datetime.datetime.now)