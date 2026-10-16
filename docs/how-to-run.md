# How to run EvoPIE

Run the commands from the repository root. Choose one of these four modes.

## Required session-signing key

EvoPIE requires a private `EVOPIE_SECRET_KEY` and exits at startup if it is
missing. Generate a unique key for this installation:

```bash
export EVOPIE_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

Keep the value private and stable across restarts. Generate a different key
for each installation. Replacing a key invalidates existing session cookies.
For Docker Compose, you can store it in a root `.env` file; start with
`.env.example`, fill in the key, and never commit `.env`. For direct local
commands, export the variable in the shell before running EvoPIE.

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

## 2. Docker local

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

## 3. Watched Docker local

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
host Python environment. It checks that ignored files match between the Compose
Watch configuration and the ignore files used by the project. Compose Watch
syncs source changes and restarts the affected service; it stays attached to
the terminal. Dependency and Dockerfile changes trigger image rebuilds.

## 4. Production

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

## Optional local HTTPS

Local HTTPS is a separate TLS reverse-proxy service. It does not build, start,
or select an EvoPIE app service, so it can be enabled alongside any one of the
three local modes above. It proxies to the app's HTTP endpoint, which remains
available on its normal port. Do not use this proxy with the production mode;
production has its own HTTPS service.

First create a local self-signed certificate. The certificate domain should
match the hostname you will use in the browser:

```bash
just local-certs localhost ./certs
```

Start EvoPIE in one local mode. For `uv local`, the app must listen on an
interface reachable from Docker rather than only loopback. Thus, you must add
the `--host 0.0.0.0` option, as shown below:

```bash
uv run flask run --host=0.0.0.0
```

The Docker local and watched modes already publish the app on port 5000. Then,
in another terminal, start the HTTPS proxy:

```bash
just local-https-up localhost ./certs
```

Open <https://localhost:5443>. The browser will warn because the certificate
is self-signed. The proxy defaults to forwarding to `host.docker.internal:5000`
and maps its HTTPS listener to host port 5443, leaving the app's HTTP port
unchanged. Override the destination with the fourth argument if the app uses a
different port, for example:

```bash
just local-https-up localhost ./certs 5443 host.docker.internal:5010
```

To stop only the HTTPS proxy, run:

```bash
just local-https-down
```

This does not stop EvoPIE. Do not commit generated certificate files or
private keys.
