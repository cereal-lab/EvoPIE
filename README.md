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
Install python packages: 
```bash
cd EvoPIE 
pipenv install
cd ..
```
Generate an empty data base:
```bash
cd EvoPIE
pipenv shell
flask DB-reboot
cd ..
```
Move the empyt DB to where the docker container will expect it: 
```bash
mv EvoPIE/evopie/DB_quizlib.sqlite ./
```
Edit docker-compose.yml to make it point to the DB file that we will be using.

Build the docker containers and run them:
```bash
docker-compose up --build -d
```
