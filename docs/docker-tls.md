# Docker TLS certificate setup

EvoPIE's Docker deployment runs the Flask application behind nginx. The web
container speaks plain HTTP inside the Docker network, and nginx accepts the
browser connection on port 5000.

The current nginx configuration enables HTTPS:

```nginx
listen 5000 ssl;
```

Because SSL/TLS is enabled, nginx must load a certificate and a matching
private key before it can start.

## Why certificates are required

A TLS certificate lets a browser verify a server name and negotiate encrypted
traffic. A typical nginx setup needs two files:

- `fullchain.pem`: the public certificate chain sent to browsers.
- `privkey.pem`: the private key proving the server owns that certificate.

For production, these files normally come from a trusted certificate authority,
such as Let's Encrypt. For local testing, they can be self-signed. A
self-signed certificate is enough to start nginx and encrypt traffic, but
browsers will show a warning because they do not trust it automatically.

## Current expected layout

The nginx config currently uses the `evopie.cse.usf.edu` certificate name:

```nginx
ssl_certificate /etc/nginx/certs/live/evopie.cse.usf.edu/fullchain.pem;
ssl_certificate_key /etc/nginx/certs/live/evopie.cse.usf.edu/privkey.pem;
```

Docker Compose mounts the host certificate directory into nginx at
`/etc/nginx/certs`. With the default Compose settings, nginx expects these host
files:

```text
/etc/letsencrypt/live/evopie.cse.usf.edu/fullchain.pem
/etc/letsencrypt/live/evopie.cse.usf.edu/privkey.pem
```

If those files do not exist, the nginx container exits during startup.

## Local self-signed certificate

For local testing, create a certificate directory in the repository and point
Compose at it with `EVOPIE_CERTS_DIR`:

```bash
mkdir -p ./certs/live/evopie.cse.usf.edu

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./certs/live/evopie.cse.usf.edu/privkey.pem \
  -out ./certs/live/evopie.cse.usf.edu/fullchain.pem \
  -subj "/CN=evopie.cse.usf.edu"

EVOPIE_CERTS_DIR=./certs docker compose up --build -d
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

After certbot finishes, the default Compose mount should expose the files to
nginx:

```text
/etc/letsencrypt/live/evopie.cse.usf.edu/fullchain.pem
/etc/letsencrypt/live/evopie.cse.usf.edu/privkey.pem
```

If certificates live somewhere else, set `EVOPIE_CERTS_DIR` before starting
Compose:

```bash
export EVOPIE_CERTS_DIR=/path/to/letsencrypt
```

## Known limitations

This document describes the current nginx behavior. The nginx config still
assumes the `evopie.cse.usf.edu` server name and certificate layout. Deploying
under another domain currently requires editing `nginx/nginx.conf` or adding a
new nginx configuration.

Future improvements could add a local HTTP mode, Compose profiles, or nginx
configuration templating so non-production deployments do not need production
certificate assumptions.
