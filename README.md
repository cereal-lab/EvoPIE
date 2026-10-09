# EvoPIE - Evolutionary Peer Instruction Environment

## Synopsis
This web application supports asynchronous peer instruction.
Server side is currently handled by Python/Flask app and also exposes a RESTful API for future development toward single page web app format.


## Acknowledgement
This material is based in part upon work supported by the National Science Foundation under awards #2012967. Any opinions, findings, and conclusions or recommendation expressed in this work are those of the authors and do not necessarily reflect the views of the National Science Foundation.

## Repository structure:
Folder | Description
------ | -----------
deployment  |   archive of scripts and Dockerfiles from previous field tests
docs        |   you will never guess
evopie      |   main application
nginx       |   Dockerfiles for nginx container
testing     |   mix of scripts and other tools used to test the system

## How to build / deploy the server
Check out the main branch of our GitHub repository: 
```bash
git clone https://github.com/cereal-lab/EvoPIE.git
```

Docker Compose uses profiles so deployment intent is explicit. For local
startup without nginx or TLS, run:

```bash
docker compose --profile local up --build -d
```

The local profile builds from your current checkout and stores EvoPIE data in
`./data` by default. To store database and uploaded data elsewhere, set
`EVOPIE_DATA_DIR` before starting the services.

For active local development, Compose Watch is also available. It syncs source
changes into the running containers and restarts the affected service. This
requires a recent Docker Compose version with watch support:

```bash
docker compose --profile local up --build --watch
```

The watch configuration should ignore the same generated and local-only paths
listed in `.dockerignore`. You can check that manually with:

```bash
./scripts/check-compose-watch-ignore.py
```

The preferred convenience command runs that check before starting watch mode:

```bash
just local-watch
```

Compose Watch runs attached to the terminal. Docker Compose does not allow
combining `--watch` with detached mode.

For production HTTPS deployment, provide the required deployment settings.
Production builds fetch the upstream repository in the application Dockerfiles
and use `master` by default. To deploy a different branch, tag, or commit, set
`EVOPIE_GIT_REF`.

```bash
EVOPIE_DATA_DIR=/srv/evopie/data \
EVOPIE_SERVER_NAME=example.edu \
EVOPIE_CERTS_DIR=/etc/letsencrypt \
EVOPIE_GIT_REF=master \
docker compose --profile production up --build -d
```

The database defaults to `/app/data/db.sqlite` inside the containers. To use a
different database URI, set `EVOPIE_DATABASE_URI`.

See [Docker TLS certificate setup](docs/docker-tls.md) for local HTTP,
the local certificate helper, and production certificate notes.

Build the docker containers and run them with one of the profiles above.
(Note the space since docker-compose is now deprecated and replaced by the command compose in docker)

