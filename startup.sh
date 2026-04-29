#!/bin/bash
# Startup script for Azure App Service
# Rebuilds dependencies on Azure so native wheels match the App Service runtime,
# then launches gunicorn with the wsgi module that sets up sys.path correctly.

set -e

cd /home/site/wwwroot

PACKAGE_DIR=".python_packages/lib/site-packages"
STAMP_FILE=".python_packages/.requirements-sha"
REQ_HASH=$(sha256sum requirements.txt | awk '{print $1}')

if [ ! -f "$STAMP_FILE" ] || [ "$(cat "$STAMP_FILE")" != "$REQ_HASH" ]; then
	rm -rf "$PACKAGE_DIR"
	mkdir -p "$PACKAGE_DIR"
	python -m pip install --upgrade --no-cache-dir --target="$PACKAGE_DIR" -r requirements.txt
	printf "%s" "$REQ_HASH" > "$STAMP_FILE"
fi

exec gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app
