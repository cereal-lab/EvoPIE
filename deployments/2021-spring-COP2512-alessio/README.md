2nd live test for EvoPIE, deployed to students in COP2512 taught by alessio at USF (online synchronous)

Notes
- docker-compose version was downgraded from 3.7 to 2.0 to match the deployment server
- archives of the squlite file + modified docker-compose.yml backed up on shared google drive
- folders gunicorn-* contain intermediary experiments on using first gunicorn and gunicorn + nginx and their corresponding dockerfiles. disreguard.
- docker-compose.yml and all required env and dockerfiles are now located at the root of project folder, as they should. These are the versions used for deployment.
- Command used to package and run the container on target servers;
```bash
cd /EvoPIE/2021-spring-COP2512-alessio
git clone https://github.com/cereal-lab/EvoPIE.git
cd EvoPIE
docker-compose up --build -d
docker-compose ps
```
