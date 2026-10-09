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

## Why does nginx fail to start in the production profile?

The production profile requires `EVOPIE_DATA_DIR`, `EVOPIE_SERVER_NAME`, and
`EVOPIE_CERTS_DIR`. Nginx also checks that the certificate and key exist at:

```text
${EVOPIE_CERTS_DIR}/live/${EVOPIE_CERT_DOMAIN}/fullchain.pem
${EVOPIE_CERTS_DIR}/live/${EVOPIE_CERT_DOMAIN}/privkey.pem
```

`EVOPIE_CERT_DOMAIN` defaults to `EVOPIE_SERVER_NAME`. Set the variables to
match your deployment and ensure both files exist. For local HTTPS testing,
create a self-signed certificate with `./scripts/create-local-certs.sh`.

## Why do Docker changes from my local checkout not appear in the container?

The `production` profile builds from the upstream GitHub repository and checks
out `EVOPIE_GIT_REF`, which defaults to `master`. Use the `local` profile to
build from your current checkout. For iterative development, use Compose Watch
with `docker compose --profile local up --build --watch`.
