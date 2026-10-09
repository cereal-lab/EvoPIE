# Troubleshooting

This document is an FAQ for common EvoPIE problems.

## Why does `flask DB-init` say it cannot find the Flask app?

Set the Flask application entry point before running Flask commands:

```bash
export FLASK_APP=evopie/__init__.py
```

Then rerun the command.

## Why is the local database empty?

Initialize the database tables:

```bash
pipenv run flask DB-init
```

To discard local data and recreate the tables, run:

```bash
pipenv run flask DB-reboot
```

## Why is the first account an instructor?

On an empty database, EvoPIE makes the first signed-up account an instructor.
Later accounts become students.

## Why is port 5000 unavailable?

Another process may already be using port 5000. Stop that process or run Flask
on another port:

```bash
pipenv run flask run --port 5010
```

## Why is dashboard data stale?

Run the updater once:

```bash
pipenv run python updater.py -1
```

For a continuously refreshed local dashboard, run the updater in another
terminal:

```bash
pipenv run python updater.py 360
```

## Why does Docker deployment fail at nginx startup?

The current Docker deployment expects TLS certificates for
`evopie.cse.usf.edu`. Make sure the configured certificate and key files exist
before starting Docker Compose.

## Why do Docker changes from my local checkout not appear in the container?

The current Dockerfiles clone `master` from GitHub during image build. They do
not run the local checkout from which `docker compose` is invoked.
