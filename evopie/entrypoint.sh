#!/bin/bash 
pipenv run flask DB-init
pipenv run python3 datalayer/updateglossary.py /app/data/db.sqlite
pipenv run gunicorn --log-level debug -w 4 -b 0.0.0.0:5000 app:APP
# seems to be old syntax:
#pipenv run gunicorn --reload --workers 1 -b 0.0.0.0:5000 app:APP --debug --debugger-address="0.0.0.0:5678"
