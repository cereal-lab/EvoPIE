# How to run EvoPIE

Run the commands from the repository root. Choose one of these five modes.

## 1. uv local

Install Python 3.8 and [uv](https://docs.astral.sh/uv/), then run:

```bash
uv sync --locked
export FLASK_APP=evopie/__init__.py
uv run flask DB-init
uv run flask run
```

Open <http://127.0.0.1:5000>. `DB-init` creates the database tables without
discarding existing data. To refresh dashboard data, run the updater
separately:

```bash
uv run python updater.py 360
```

Use `uv run python updater.py -1` to run the updater once.

## 2. Simple Docker local development

**Just command:**

```bash
just local-up
```

**Command it runs:**

```bash
docker compose --profile local up --build -d
```

This builds the web and updater images from the current checkout and serves the
web app over HTTP without nginx. Open <http://127.0.0.1:5000>. Data is stored
in `./data` by default; set `EVOPIE_DATA_DIR` to use another host directory.
The database defaults to `sqlite:////app/data/db.sqlite`.

## 3. Watched local development

**Just command:**

```bash
just local-watch
```

**Commands it runs:**

```bash
just check-watch-ignore
docker compose --profile local up --build --watch
```

`just check-watch-ignore` runs
`./scripts/check-compose-watch-ignore.py`. The check requires PyYAML in the
host Python environment. Compose Watch syncs source changes and restarts the
affected service; it stays attached to the terminal. Dependency and Dockerfile
changes trigger image rebuilds.

## 4. Deployment to production

**Just command:**

```bash
just prod-up example.edu /etc/letsencrypt /srv/evopie/data
```

The optional fourth argument selects the Git ref and defaults to `master`.

**Command it runs:**

```bash
EVOPIE_SERVER_NAME=example.edu \
EVOPIE_CERT_DOMAIN=example.edu \
EVOPIE_CERTS_DIR=/etc/letsencrypt \
EVOPIE_DATA_DIR=/srv/evopie/data \
EVOPIE_GIT_REF=master \
docker compose --profile production up --build -d
```

Replace the example domain, certificate directory, and data directory with
your settings. Provision the certificate before starting; Compose does not
issue or renew certificates. Nginx expects the certificate and key under
`live/<domain>/` in `EVOPIE_CERTS_DIR`. Open <https://example.edu:5000>, using
your configured server name.

Production images are built from the upstream repository at `EVOPIE_GIT_REF`,
not from the local checkout. See the
[certificate operations reference](reference.md#certificate-operations) for
a certbot example.

## 5. Local HTTPS mode

First create a self-signed certificate:

**Just command:**

```bash
just local-certs localhost ./certs
```

**Command it runs:**

```bash
EVOPIE_CERT_DOMAIN=localhost \
EVOPIE_CERTS_DIR=./certs \
./scripts/create-local-certs.sh
```

Then start HTTPS with the production profile using local settings:

**Just command:**

```bash
just prod-up localhost ./certs ./data
```

**Command it runs:**

```bash
EVOPIE_SERVER_NAME=localhost \
EVOPIE_CERT_DOMAIN=localhost \
EVOPIE_CERTS_DIR=./certs \
EVOPIE_DATA_DIR=./data \
EVOPIE_GIT_REF=master \
docker compose --profile production up --build -d
```

This profile builds the upstream `master` branch by default. Pass a different
Git ref as the fourth Just argument if needed. Open <https://localhost:5000>.
The browser will warn because the certificate is self-signed. Do not commit
generated certificate files or private keys.
