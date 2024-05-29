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

Edit the docker-compose.yml file to update the volumes for "web"
```bash
version: '2.0'

services:
  web:
    build: ./evopie
    volumes:
      - /EvoPIE/2024-fall-alessio/data:/app/data
    environment:
      - EVOPIE_DATABASE_URI=sqlite:////app/data/db.sqlite
    expose:
      - 5000
    env_file:
      - ./evopie/.env.dev
    restart: always
  nginx:
    build: ./nginx
    ports:
      - "5000:5000"
    depends_on:
      - web
    restart: always
    volumes:
      - /etc/letsencrypt:/etc/nginx/certs
```

Build the docker containers and run them:
```bash
docker-compose up --build -d
```
