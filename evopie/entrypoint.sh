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

uv run --frozen --no-sync flask DB-init
uv run --frozen --no-sync python3 datalayer/updateglossary.py "$DB_FILE"
# Production version: 
# uv run --frozen --no-sync gunicorn -w 4 -b 0.0.0.0:5000 app:APP
# Dev version: 
uv run --frozen --no-sync gunicorn --log-level debug -w 1 -b 0.0.0.0:5000 app:APP
#uv run --frozen --no-sync gunicorn --log-level debug -w 1 -b 0.0.0.0:5010 app:APP
# seems to be old syntax:
#uv run --frozen --no-sync gunicorn --reload --workers 1 -b 0.0.0.0:5000 app:APP --debug --debugger-address="0.0.0.0:5678"

