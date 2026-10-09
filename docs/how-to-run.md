# How to run EvoPIE

## Run locally with Pipenv

1. Install Python 3.8 and Pipenv.

2. Clone the repository.

   ```bash
   git clone https://github.com/cereal-lab/EvoPIE.git
   cd EvoPIE
   ```

3. Install the Python dependencies.

   ```bash
   pipenv sync
   ```

4. Set the Flask app entry point.

   ```bash
   export FLASK_APP=evopie/__init__.py
   ```

5. Initialize the local database.

   ```bash
   pipenv run flask DB-init
   ```

   This creates the database tables if they do not already exist. If you want
   to reset the local database instead, run:

   ```bash
   pipenv run flask DB-reboot
   ```

6. Run the updater.

   ```bash
   pipenv run python updater.py -1
   ```

   This runs the updater once and then exits. To keep the updater running while
   you work, run it in a separate terminal instead:

   ```bash
   pipenv run python updater.py 360
   ```

7. Start the web application.

   ```bash
   pipenv run flask run
   ```

8. Open EvoPIE in your browser.

   ```text
   http://127.0.0.1:5000
   ```

On an empty database, the first account created through the sign-up page
becomes an instructor account. Later accounts become student accounts.

## Deploy with Docker Compose

The current Docker Compose deployment is configured for `evopie.cse.usf.edu`.

If you want to deploy EvoPIE somewhere else, update the deployment settings
first. At minimum, review:

- `docker-compose.yml`
- `nginx/nginx.conf`

The current deployment expects:

- EvoPIE data in `/EvoPIE/data`
- the SQLite database at `/EvoPIE/data/db.sqlite`
- TLS certificates under `/etc/letsencrypt`
- certificate files for `evopie.cse.usf.edu`

The expected certificate files are:

```text
/etc/letsencrypt/live/evopie.cse.usf.edu/fullchain.pem
/etc/letsencrypt/live/evopie.cse.usf.edu/privkey.pem
```

1. Prepare the data directory.

   ```bash
   sudo mkdir -p /EvoPIE/data
   ```

2. If you are deploying an existing EvoPIE server, copy its database to:

   ```text
   /EvoPIE/data/db.sqlite
   ```

   If no database exists, EvoPIE can initialize an empty one during startup.

3. Make sure the TLS certificate files exist.

   Provision the certificate with certbot or another TLS certificate provider
   before starting Docker Compose.

4. Start the services.

   ```bash
   docker compose up --build -d
   ```

5. Check that the services are running.

   ```bash
   docker compose ps
   docker compose logs -f -t
   ```

6. Stop the services when needed.

   ```bash
   docker compose down
   ```

Important: the current Dockerfiles clone `master` from
`https://github.com/cereal-lab/EvoPIE.git` during image build. They do not run
the local checkout from which you invoke `docker compose`.
