## RPW:  Ad-Hoc stand-alone script to remove usernames from the DB
# Run from the repository root with: python -m datalayer.sanatize

from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy.orm import Session

import logging

from datalayer import ConfigureLogger

LOGGER = ConfigureLogger(logging.getLogger(__name__))
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


engine = create_engine("sqlite:///alessio.sqlite", future=True)
session = Session(engine)
sanitized_count = 0

for instance in session.query(User).order_by(User.id):
  instance.first_name = instance.role + '-' + str(instance.id)
  instance.last_name = instance.role + '-' + str(instance.id)
  instance.email="noone@nowhere.xyz"
  sanitized_count += 1

session.commit()
LOGGER.info("Anonymized %s user records.", sanitized_count)

