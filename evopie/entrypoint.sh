#!/bin/bash 
pipenv run flask DB-init
pipenv run python3 datalayer/updateglossary.py /app/data/db.sqlite
pipenv run gunicorn -w 4 -b 0.0.0.0:5000 app:APP