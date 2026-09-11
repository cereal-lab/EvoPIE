#!/bin/sh
set -eu

if [ -z "${EVOPIE_NGINX_MODE:-}" ]; then
  echo "EVOPIE_NGINX_MODE is required." >&2
  echo "Use 'http' for local HTTP or 'https' for TLS." >&2
  exit 1
fi

: "${EVOPIE_SERVER_NAME:=localhost}"
: "${EVOPIE_CERT_DOMAIN:=$EVOPIE_SERVER_NAME}"
: "${EVOPIE_SSL_CERTIFICATE:=/etc/nginx/certs/live/$EVOPIE_CERT_DOMAIN/fullchain.pem}"
: "${EVOPIE_SSL_CERTIFICATE_KEY:=/etc/nginx/certs/live/$EVOPIE_CERT_DOMAIN/privkey.pem}"

case "$(printf '%s' "$EVOPIE_NGINX_MODE" | tr '[:upper:]' '[:lower:]')" in
  https)
    if [ ! -f "$EVOPIE_SSL_CERTIFICATE" ]; then
      echo "Missing TLS certificate: $EVOPIE_SSL_CERTIFICATE" >&2
      exit 1
    fi

    if [ ! -f "$EVOPIE_SSL_CERTIFICATE_KEY" ]; then
      echo "Missing TLS certificate key: $EVOPIE_SSL_CERTIFICATE_KEY" >&2
      exit 1
    fi

    LISTEN_DIRECTIVE="listen 5000 ssl;"
    TLS_DIRECTIVES="    ssl_certificate $EVOPIE_SSL_CERTIFICATE;
    ssl_certificate_key $EVOPIE_SSL_CERTIFICATE_KEY;
    error_page 497 301 =307 https://\$host:\$server_port\$request_uri;"
    ;;
  http)
    LISTEN_DIRECTIVE="listen 5000;"
    TLS_DIRECTIVES=""
    ;;
  *)
    echo "Invalid EVOPIE_NGINX_MODE value: $EVOPIE_NGINX_MODE" >&2
    echo "Use 'http' for local HTTP or 'https' for TLS." >&2
    exit 1
    ;;
esac

cat > /etc/nginx/conf.d/evopie.conf <<EOF
upstream evopie {
    server web:5000;
}

server {
    $LISTEN_DIRECTIVE
    server_name $EVOPIE_SERVER_NAME;
$TLS_DIRECTIVES

    location / {
        proxy_pass http://evopie;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$http_host;
        proxy_redirect http:// \$scheme://;
    }
}
EOF

exec nginx -g 'daemon off;'
