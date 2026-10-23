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
uv run flask DB-init
```

To discard local data and recreate the tables, run:

```bash
uv run flask DB-reboot
```

## How do I create the initial admin account?

Set `EVOPIE_ADMIN_EMAIL` and `EVOPIE_ADMIN_PASSWORD` before you initialize an
empty database. `DB-init` creates the admin account, and self-service signups
receive the student role. See [How to run EvoPIE](how-to-run.md#initial-admin-account)
for setup details.

## Why is port 5000 unavailable?

Another process may already be using port 5000. Stop that process or run Flask
on another port:

```bash
uv run flask run --port 5010
```

## Why is dashboard data stale?

Run the updater once:

```bash
uv run python updater.py -1
```

For a continuously refreshed local dashboard, run the updater in another
terminal:

```bash
uv run python updater.py 360
```

## Why does nginx fail to start in the production profile?

The production profile requires `EVOPIE_DATA_DIR`, `EVOPIE_SERVER_NAME`,
`EVOPIE_CERTS_DIR`, and `EVOPIE_SECRET_KEY`. Nginx also checks that the
certificate and key exist at:

```text
${EVOPIE_CERTS_DIR}/live/${EVOPIE_CERT_DOMAIN}/fullchain.pem
${EVOPIE_CERTS_DIR}/live/${EVOPIE_CERT_DOMAIN}/privkey.pem
```

`EVOPIE_CERT_DOMAIN` defaults to `EVOPIE_SERVER_NAME`. Set the variables to
match your deployment and ensure both files exist. For local HTTPS, do not use
the production profile: generate a self-signed certificate with
`just local-certs localhost ./certs`, start one local app mode, then activate
the standalone HTTPS proxy with `just local-https-up localhost ./certs`. See
[How to run EvoPIE](how-to-run.md#optional-local-https) for details.

## Why does the local HTTPS proxy return 502 Bad Gateway?

The local HTTPS proxy forwards to `host.docker.internal:5000` by default. Ensure
a local EvoPIE mode is running and its HTTP endpoint is reachable at that host
and port. For `uv local`, run Flask with `--host=0.0.0.0`; the default loopback
binding is not reachable from the proxy container. If the app uses a different
port, set the proxy upstream, for example:

```bash
just local-https-up localhost ./certs 5443 host.docker.internal:5010
```

The HTTPS proxy is separate from the app and can be stopped without stopping
EvoPIE using `just local-https-down`.

## Why do Docker changes from my local checkout not appear in the container?

The `production` profile builds from the upstream GitHub repository and checks
out `EVOPIE_GIT_REF`, which defaults to `master`. Use the `local` profile to
build from your current checkout. For iterative development, use Compose Watch
with `docker compose --profile local up --build --watch`. The standalone local
HTTPS proxy only forwards requests; it does not build or update the app image.
