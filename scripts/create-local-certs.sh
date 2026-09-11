#!/bin/sh
set -eu

CERT_DOMAIN="${EVOPIE_CERT_DOMAIN:-localhost}"
CERTS_DIR="${EVOPIE_CERTS_DIR:-./certs}"
CERT_DIR="$CERTS_DIR/live/$CERT_DOMAIN"

mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout "$CERT_DIR/privkey.pem" \
  -out "$CERT_DIR/fullchain.pem" \
  -subj "/CN=$CERT_DOMAIN"

cat <<EOF
Created local self-signed certificate files:

  $CERT_DIR/fullchain.pem
  $CERT_DIR/privkey.pem

Start HTTPS mode with:

  EVOPIE_SERVER_NAME=$CERT_DOMAIN \\
  EVOPIE_CERT_DOMAIN=$CERT_DOMAIN \\
  EVOPIE_CERTS_DIR=$CERTS_DIR \\
  docker compose --profile production up --build -d
EOF
