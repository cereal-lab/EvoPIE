# Ad-Hoc standalone script to populate the glossary table from a JSON file.
# Run from the EvoPIE directory like this:
#  python datalayer/updateglossary.py
#
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy import insert
from sqlalchemy import MetaData
from sqlalchemy import inspect
from sqlalchemy.orm import Session

import json
import logging
import sys

from datalayer import ConfigureLogger

LOGGER = ConfigureLogger(logging.getLogger(__name__))

DB = SQLAlchemy()

ROLE_STUDENT = "STUDENT"
ROLE_INSTRUCTOR = "INSTRUCTOR"
ROLE_ADMIN = "ADMIN"


class GlossaryTerm(DB.Model):
   """
   The ORM secheme for glossary terms. 
   """
   __tablename__ = "glossary"

   id = DB.Column(DB.Integer, primary_key=True)
   term = DB.Column(DB.String, nullable=False)
   definition = DB.Column(DB.String, nullable=False)


def get_database_session(dbFilename):
  """
  Connect to the database, return the session object
  """
  connectionString = "sqlite:///" + dbFilename
  engine = None
  session = None

  try:
    engine = create_engine(connectionString)
    session = Session(engine)

  except Exception:
    LOGGER.exception("Could not open DB at %s.", connectionString)
    sys.exit(11)

  LOGGER.info("Connected to %s.", connectionString)

  try:
    # If the glossary table does not exist, create it
    if not inspect(engine).has_table("glossary"): 
        LOGGER.info("The glossary table does not exist; creating it.")
        metadata = MetaData() #   MetaData(engine)
        DB.Table( "glossary", metadata,
            DB.Column('id', DB.Integer, primary_key=True), 
            DB.Column('term', DB.String, nullable=False),
            DB.Column('definition', DB.String, nullable=False) )
        metadata.create_all(engine)   
    else:
      LOGGER.info("The glossary table already exists; no need to create it.")
  except Exception:
    LOGGER.exception("Could not create the glossary table.")
    sys.exit(12)

  return session


def get_glossary_dict(jsonFilename):
  """
  Go get the JSON file and return a dictionary
  """
  jsonDict = None
  try:
    jsonFile = open(jsonFilename)
    jsonDict = json.load(jsonFile)
  except Exception:
    LOGGER.exception("Could not read JSON file %s.", jsonFilename)
    sys.exit(1)

  try:
    ids = jsonDict['ID']
    terms = jsonDict['Term']
    definitions = jsonDict['Definition']

    tmpDict = {}
    for idString in ids:
      tmpDict[int(idString)] = (terms[idString], definitions[idString])

    jsonDict = tmpDict

  except Exception:
    LOGGER.exception("JSON file %s has an unexpected format.", jsonFilename)
    sys.exit(2)

  return jsonDict


def update_glossary_table(dbSession, jsonDict):
  """"""
  try:
    for jid in jsonDict:
        jterm, jdefinition = jsonDict[jid]

        ## Check if jid is in the glossary table  If not, add, if so update via ORM
        try:
          luTerm = dbSession.query(GlossaryTerm).filter_by(id=jid).one()

          if (not jterm == luTerm.term) or (not jdefinition == luTerm.definition):
            luTerm.term = jterm
            luTerm.definition = jdefinition
            LOGGER.info("Updating glossary term %r.", luTerm.term)
          else:
            LOGGER.debug("Glossary term %r is unchanged.", jterm)

        except:
          LOGGER.info("Adding glossary term %r.", jterm)
          glossaryTerm = GlossaryTerm(id=jid, term=jterm, definition=jdefinition)
          dbSession.add(glossaryTerm)

  except Exception:
    LOGGER.exception("Could not update the glossary table.")
    sys.exit(4)

  LOGGER.info("Updated the glossary table.")


if __name__ == '__main__':
  jsonFilename = "./glossary.json"  ## RPW:  These should not be hard-coded and
  dbFilename = "./evopie/DB_quizlib.sqlite"   ##       will have moved.

  try:
    dbFilename = sys.argv[1]
    jsonFilename = sys.argv[2]
  except:
    pass
  
  glossaryDict = get_glossary_dict(jsonFilename)
  dbSession = get_database_session(dbFilename)
  update_glossary_table(dbSession, glossaryDict)
  dbSession.commit()
