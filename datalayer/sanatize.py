## RPW:  Ad-Hoc stand-alone script to remove usernames from the DB

from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy.orm import Session
from datalayer import LOGGER

DB = SQLAlchemy()

ROLE_STUDENT = "STUDENT"
ROLE_INSTRUCTOR = "INSTRUCTOR"
ROLE_ADMIN = "ADMIN"

class User(DB.Model):
  id = DB.Column(DB.Integer, primary_key=True)
  email = DB.Column(DB.String)
  first_name = DB.Column(DB.String)
  last_name = DB.Column(DB.String)
  password = DB.Column(DB.String)
  role = DB.Column(DB.String, default=ROLE_STUDENT)


engine = create_engine("sqlite:///alessio.sqlite", echo=True, future=True)
session = Session(engine)

for instance in session.query(User).order_by(User.id):
  LOGGER.info("OLD::", instance.id, instance.first_name, instance.last_name, instance.email, instance.role)
  instance.first_name = instance.role + '-' + str(instance.id)
  instance.last_name = instance.role + '-' + str(instance.id)
  instance.email="noone@nowhere.xyz"
  LOGGER.info("NEW::", instance.id, instance.first_name, instance.last_name, instance.email, instance.role)
  LOGGER.info("")

session.commit()

