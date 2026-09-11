# Docker TLS certificate setup

EvoPIE's production Docker deployment runs the Flask application behind nginx.
The web container speaks plain HTTP inside the Docker network, and nginx
accepts the browser connection on port 5000.

Docker Compose uses profiles so deployment intent is explicit:

- `local`: direct HTTP startup without nginx or certificates.
- `production`: nginx HTTPS startup with required data, domain, and certs.

## Why certificates are required for HTTPS

A TLS certificate lets a browser verify a server name and negotiate encrypted
traffic. A typical nginx setup needs two files:

- `fullchain.pem`: the public certificate chain sent to browsers.
- `privkey.pem`: the private key proving the server owns that certificate.

For production, these files normally come from a trusted certificate authority,
such as Let's Encrypt. For local testing, they can be self-signed. A
self-signed certificate is enough to start nginx and encrypt traffic, but
browsers will show a warning because they do not trust it automatically.

## Local HTTP mode

For local HTTP, select the local Compose profile:

```bash
docker compose --profile local up --build -d
```

Then open:

```text
http://127.0.0.1:5000
```

This mode is intended for local development and smoke testing. It publishes the
web container directly and avoids nginx/certificate setup before confirming
that the application starts.

The local profile stores EvoPIE data in `./data` by default. Set
`EVOPIE_DATA_DIR` to use a different host directory.

## Local self-signed HTTPS certificate

To test nginx HTTPS locally, create a self-signed certificate:

```bash
./scripts/create-local-certs.sh
```

The helper defaults to `localhost` and creates this certificate layout:

```text
./certs/live/localhost/fullchain.pem
./certs/live/localhost/privkey.pem
```

Then start the production profile with local HTTPS settings. HTTPS uses nginx,
so it runs through the production profile even when the certificate is local:

```bash
EVOPIE_DATA_DIR=./data \
EVOPIE_SERVER_NAME=localhost \
EVOPIE_CERT_DOMAIN=localhost \
EVOPIE_CERTS_DIR=./certs \
docker compose --profile production up --build -d
```

To generate a certificate for a different local name, set
`EVOPIE_CERT_DOMAIN` before running the helper:

```bash
EVOPIE_CERT_DOMAIN=local.evopie.test ./scripts/create-local-certs.sh
```

Then open:

```text
https://127.0.0.1:5000
```

The browser warning is expected. The certificate is self-signed and may not
match `127.0.0.1` unless it was generated for that name.

Do not commit generated certificate files or private keys.

## Production certificates

Production deployments should use certificates from a trusted authority. One
common option is Let's Encrypt with certbot:

```bash
sudo certbot certonly --standalone -d example.edu
```

After certbot finishes, provide the required production settings:

```bash
EVOPIE_DATA_DIR=/srv/evopie/data \
EVOPIE_SERVER_NAME=example.edu \
EVOPIE_CERT_DOMAIN=example.edu \
EVOPIE_CERTS_DIR=/etc/letsencrypt \
docker compose --profile production up --build -d
```

This exposes the following host files to nginx:

```text
/etc/letsencrypt/live/example.edu/fullchain.pem
/etc/letsencrypt/live/example.edu/privkey.pem
```

If certificates live somewhere else, set `EVOPIE_CERTS_DIR` to that directory.

## Enforced configuration

The production profile fails during Compose configuration if these values are
missing:

- `EVOPIE_DATA_DIR`
- `EVOPIE_SERVER_NAME`
- `EVOPIE_CERTS_DIR`

The nginx entrypoint also fails if the certificate or key file is missing.

## Configuration reference

- `EVOPIE_DATA_DIR`: host data directory. Required for production.
- `EVOPIE_SERVER_NAME`: nginx `server_name`. Required for production.
- `EVOPIE_CERT_DOMAIN`: certificate directory under `live/`; defaults to
  `EVOPIE_SERVER_NAME` when HTTPS is enabled.
- `EVOPIE_CERTS_DIR`: host directory mounted to `/etc/nginx/certs`. Required
  for production.

Advanced deployments can set full certificate paths inside the nginx container:

```bash
EVOPIE_SSL_CERTIFICATE=/etc/nginx/certs/live/example/fullchain.pem
EVOPIE_SSL_CERTIFICATE_KEY=/etc/nginx/certs/live/example/privkey.pem
```

## Security notes

Local HTTP mode does not provide encryption. Production deployments should use
HTTPS and provide certificates from a trusted authority.

Self-signed certificates are for local testing only. Browsers will warn because
they are not signed by a trusted certificate authority.
