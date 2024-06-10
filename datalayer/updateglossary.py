# Ad-Hoc standalone script to populate the glossary table from a JSON file.
from sqlalchemy import create_engine
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy import insert
from sqlalchemy import MetaData
from sqlalchemy import inspect
from sqlalchemy.orm import Session
from datalayer import LOGGER

import json
import sys

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

  except:
    LOGGER.error("ERROR: Could not open DB at '" + connectionString + "'.")
    sys.exit(11)

  LOGGER.info("Connected to: ", connectionString)

  try:
    # If the glossary table does not exist, create it
    if not inspect(engine).has_table("glossary"): 
        LOGGER.info("  The 'glossary' table did not exist.  Creating it.") 
        metadata = MetaData() #   MetaData(engine)
        DB.Table( "glossary", metadata,
            DB.Column('id', DB.Integer, primary_key=True), 
            DB.Column('term', DB.String, nullable=False),
            DB.Column('definition', DB.String, nullable=False) )
        metadata.create_all(engine)   
    else:
      LOGGER.info("  There was already a 'glossary' table.  No need to create it.") 
  except:
    LOGGER.error("ERROR: Could not create the glossary table")
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
  except:
    print("ERROR: Could not find a JSON file at '" + jsonFilename + "'.")
    sys.exit(1)

  try:
    ids = jsonDict['ID']
    terms = jsonDict['Term']
    definitions = jsonDict['Definition']

    tmpDict = {}
    for idString in ids:
      tmpDict[int(idString)] = (terms[idString], definitions[idString])

    jsonDict = tmpDict

  except:
    print("ERROR:  The JSON file at '" + jsonFilename + "' isn't formatted as expected.")
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
            print("  Updating term '" + luTerm.term + "'.")
          else:
            print("  Skipping term '" + jterm + "'.")

        except:
          print("  Adding term '" + jterm + "'")
          glossaryTerm = GlossaryTerm(id=jid, term=jterm, definition=jdefinition)
          dbSession.add(glossaryTerm)

  except:
    print("ERROR:  There was a database access problem.")
    sys.exit(4)
    
  print("Updated the glossary table.")


if __name__ == '__main__':
  jsonFilename = "../../../glossary.json"  ## RPW:  These should not be hard-coded and
  dbFilename = "../../DB_quizlib.sqlite"   ##       will have moved.

  try:
    jsonFilename = sys.argv[1]
    dbFilename = sys.argv[2]
  except:
    pass
  
  glossaryDict = get_glossary_dict(jsonFilename)
  dbSession = get_database_session(dbFilename)
  update_glossary_table(dbSession, glossaryDict)
  dbSession.commit()
