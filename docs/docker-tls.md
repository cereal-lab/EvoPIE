# Docker TLS certificate setup

EvoPIE's Docker deployment runs the Flask application behind nginx. The web
container speaks plain HTTP inside the Docker network, and nginx accepts the
browser connection on port 5000.

Nginx requires an explicit mode. Set `EVOPIE_NGINX_MODE=http` for local HTTP or
`EVOPIE_NGINX_MODE=https` for TLS. HTTPS mode also requires
`EVOPIE_SERVER_NAME`.

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

For local HTTP, set the nginx mode before starting Compose:

```bash
EVOPIE_NGINX_MODE=http docker compose up --build -d
```

Then open:

```text
http://127.0.0.1:5000
```

This mode is intended for local development and smoke testing. It avoids the
need to generate certificates before confirming that the application starts.

## Local self-signed HTTPS certificate

To test nginx HTTPS locally, create a self-signed certificate:

```bash
./scripts/create-local-certs.sh
```

The helper creates this local certificate layout:

```text
./certs/live/evopie.cse.usf.edu/fullchain.pem
./certs/live/evopie.cse.usf.edu/privkey.pem
```

Then start Compose in HTTPS mode:

```bash
EVOPIE_NGINX_MODE=https \
EVOPIE_SERVER_NAME=evopie.cse.usf.edu \
EVOPIE_CERT_DOMAIN=evopie.cse.usf.edu \
EVOPIE_CERTS_DIR=./certs \
docker compose up --build -d
```

To generate a certificate for a different local name, set
`EVOPIE_CERT_DOMAIN` before running the helper:

```bash
EVOPIE_CERT_DOMAIN=localhost ./scripts/create-local-certs.sh
```

Then open:

```text
https://127.0.0.1:5000
```

The browser warning is expected. The certificate is self-signed and its common
name is `evopie.cse.usf.edu`, not `127.0.0.1`.

Do not commit generated certificate files or private keys.

## Production certificates

Production deployments should use certificates from a trusted authority. One
common option is Let's Encrypt with certbot:

```bash
sudo certbot certonly --standalone -d evopie.cse.usf.edu
```

After certbot finishes, enable TLS, set the server name, and mount the
certificate directory:

```bash
EVOPIE_NGINX_MODE=https \
EVOPIE_SERVER_NAME=evopie.cse.usf.edu \
EVOPIE_CERT_DOMAIN=evopie.cse.usf.edu \
EVOPIE_CERTS_DIR=/etc/letsencrypt \
docker compose up --build -d
```

This exposes the following host files to nginx:

```text
/etc/letsencrypt/live/evopie.cse.usf.edu/fullchain.pem
/etc/letsencrypt/live/evopie.cse.usf.edu/privkey.pem
```

If certificates live somewhere else, set `EVOPIE_CERTS_DIR` to that directory.

## Configuration reference

- `EVOPIE_NGINX_MODE`: required; use `http` or `https`.
- `EVOPIE_SERVER_NAME`: nginx `server_name`; required for HTTPS and defaults
  to `localhost` for HTTP.
- `EVOPIE_CERT_DOMAIN`: certificate directory under `live/`; defaults to
  `EVOPIE_SERVER_NAME` when HTTPS is enabled.
- `EVOPIE_CERTS_DIR`: host directory mounted to `/etc/nginx/certs`; defaults
  to `./certs`.

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
