#!/bin/sh
set -eu

if [ -z "${EVOPIE_SERVER_NAME:-}" ]; then
  echo "EVOPIE_SERVER_NAME is required for production HTTPS." >&2
  exit 1
fi

: "${EVOPIE_UPSTREAM:=web:5000}"
: "${EVOPIE_CERT_DOMAIN:=$EVOPIE_SERVER_NAME}"
: "${EVOPIE_SSL_CERTIFICATE:=/etc/nginx/certs/live/$EVOPIE_CERT_DOMAIN/fullchain.pem}"
: "${EVOPIE_SSL_CERTIFICATE_KEY:=/etc/nginx/certs/live/$EVOPIE_CERT_DOMAIN/privkey.pem}"

if [ ! -f "$EVOPIE_SSL_CERTIFICATE" ]; then
  echo "Missing TLS certificate: $EVOPIE_SSL_CERTIFICATE" >&2
  exit 1
fi

if [ ! -f "$EVOPIE_SSL_CERTIFICATE_KEY" ]; then
  echo "Missing TLS certificate key: $EVOPIE_SSL_CERTIFICATE_KEY" >&2
  exit 1
fi

cat > /etc/nginx/conf.d/evopie.conf <<EOF
upstream evopie {
    server $EVOPIE_UPSTREAM;
}

server {
    listen 5000 ssl;
    server_name $EVOPIE_SERVER_NAME;

    ssl_certificate $EVOPIE_SSL_CERTIFICATE;
    ssl_certificate_key $EVOPIE_SSL_CERTIFICATE_KEY;
    error_page 497 301 =307 https://\$host:\$server_port\$request_uri;

    location / {
        proxy_pass http://evopie;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$http_host;
        proxy_redirect http:// \$scheme://;
    }
}
EOF

exec nginx -g 'daemon off;'
