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

The local profile stores EvoPIE data in `./data` by default. To use a different
host directory, set `EVOPIE_DATA_DIR` before starting the services.

For production HTTPS, provide the required deployment settings:

```bash
EVOPIE_DATA_DIR=/srv/evopie/data \
EVOPIE_SERVER_NAME=example.edu \
EVOPIE_CERTS_DIR=/etc/letsencrypt \
docker compose --profile production up --build -d
```

The database defaults to `/app/data/db.sqlite` inside the containers. To use a
different database URI, set `EVOPIE_DATABASE_URI`.

See [Docker TLS certificate setup](docs/docker-tls.md) for local HTTP,
the local certificate helper, and production certificate notes.

Build the docker containers and run them with one of the profiles above.
(Note the space since docker-compose is now deprecated and replaced by the command compose in docker)

