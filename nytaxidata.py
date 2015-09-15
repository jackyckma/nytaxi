# -*- coding: utf-8 -*-
"""
Created on Tue Sep 15 03:24:54 2015

@author: jacky
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker, mapper
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy import create_engine, MetaData, Table

#Custom SQL settings.py
import settings


DeclarativeBase = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    


class Tripdata(object):
    pass

def loadSession():
    """"""    
    engine = create_engine('postgresql://postgres:w1ndm4ge@localhost/nytaxi') 
    #!More secure way
    #engine = create_engine(URL(**settings.DATABASE))
    
    metadata = MetaData(engine)
    tripdata = Table('tripdata', metadata, autoload=True)
    mapper(Tripdata, tripdata)
 
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
    


session = loadSession()
i=0
for p in session.query(Tripdata).yield_per(5):
    print(p)
    i+=1
    if i>10:break
