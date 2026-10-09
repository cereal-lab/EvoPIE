#!/bin/bash
set -e

DB_FILE=$(python3 - <<'PY'
import os

uri = os.getenv("EVOPIE_DATABASE_URI", "sqlite:////app/data/db.sqlite")
if uri.startswith("sqlite:///"):
    print(uri[len("sqlite:///"):].split("?", 1)[0])
else:
    print("/app/data/db.sqlite")
PY
)

pipenv run flask DB-init
pipenv run python3 datalayer/updateglossary.py "$DB_FILE"
# Production version: 
# pipenv run gunicorn -w 4 -b 0.0.0.0:5000 app:APP
# Dev version: 
pipenv run gunicorn --log-level debug -w 1 -b 0.0.0.0:5000 app:APP
#pipenv run gunicorn --log-level debug -w 1 -b 0.0.0.0:5010 app:APP
# seems to be old syntax:
#pipenv run gunicorn --reload --workers 1 -b 0.0.0.0:5000 app:APP --debug --debugger-address="0.0.0.0:5678"

