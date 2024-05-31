import sys, os, logging

import flask

# We aren't creating a real flask application; however,
# Flask-SQLAlchemy needs a flask app context, so this is a dummy
# flask application.  RPW:  Make sure the port doesn't collide
APP = flask.Flask(__name__)
APP.config['SECRET_KEY'] = '9OLWxND4o83j4K4iuopO' #FIXME replace this by an ENV variable
 #NOTE: timeout allows to avoid database is locked - it is workaround
APP.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('EVOPIE_DATABASE_URI', 'sqlite:///evopie/DB_quizlib.sqlite') + "?timeout=20"
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
APP.logger.setLevel(logging.INFO)

# This stuff must happen before the other dashboard imports, below
from datalayer import StartupDatabase, RegisterGlobalLogger
DB = StartupDatabase(APP)
LOGGER = RegisterGlobalLogger(APP.logger)

import analysislayer.widgetupdater


if __name__ == '__main__':
  sleepTimeInSeconds = -1
  try:
    sleepTimeInSeconds = int(sys.argv[1])
  except:
    sleepTimeInSeconds = int(os.getenv('EVOPIE_UPDATER_SLEEP', '-1'))

  analysislayer.widgetupdater.StartUpdater(sleepTimeInSeconds)