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

local-certs domain="localhost" certs_dir="./certs":
    EVOPIE_CERT_DOMAIN="{{domain}}" \
    EVOPIE_CERTS_DIR="{{certs_dir}}" \
    ./scripts/create-local-certs.sh

logs:
    docker compose logs -f

down:
    docker compose down
