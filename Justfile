default:
    @just --list

local-up:
    docker compose --profile local up --build -d

local-watch:
    just check-watch-ignore
    docker compose --profile local up --build --watch

check-watch-ignore:
    ./scripts/check-compose-watch-ignore.py

prod-up domain certs_dir data_dir git_ref="master":
    EVOPIE_SERVER_NAME="{{domain}}" \
    EVOPIE_CERT_DOMAIN="{{domain}}" \
    EVOPIE_CERTS_DIR="{{certs_dir}}" \
    EVOPIE_DATA_DIR="{{data_dir}}" \
    EVOPIE_GIT_REF="{{git_ref}}" \
    docker compose --profile production up --build -d

local-https-up domain="localhost" certs_dir="./certs" port="5443" upstream="host.docker.internal:5000":
    EVOPIE_SERVER_NAME="{{domain}}" EVOPIE_CERT_DOMAIN="{{domain}}" EVOPIE_CERTS_DIR="{{certs_dir}}" EVOPIE_HTTPS_PORT="{{port}}" EVOPIE_HTTPS_UPSTREAM="{{upstream}}" docker compose -p evopie-local-https -f docker-compose.https.yml up --build -d

local-https-down:
    docker compose -p evopie-local-https -f docker-compose.https.yml down

local-certs domain="localhost" certs_dir="./certs":
    EVOPIE_CERT_DOMAIN="{{domain}}" \
    EVOPIE_CERTS_DIR="{{certs_dir}}" \
    ./scripts/create-local-certs.sh

logs profile="local":
    docker compose --profile "{{profile}}" logs --tail=all -f

down:
    docker compose down
