#!/bin/bash
# Startup script for Azure App Service
# Rebuilds dependencies on Azure so native wheels match the App Service runtime,
# validates imports, then launches gunicorn.

set -e
set -o pipefail

trap 'echo "[startup] failed at line ${LINENO} with exit code $?" >&2' ERR

cd /home/site/wwwroot

PACKAGE_DIR=".python_packages/lib/site-packages"
STAMP_FILE=".python_packages/.requirements-sha"
REQ_HASH=$(sha256sum requirements.txt | awk '{print $1}')

echo "[startup] startup.sh running from $(pwd)"
echo "[startup] requirements hash: $REQ_HASH"

if [ ! -d "$PACKAGE_DIR" ] || [ ! -f "$PACKAGE_DIR/flask_sqlalchemy/__init__.py" ] || [ ! -f "$STAMP_FILE" ] || [ "$(cat "$STAMP_FILE")" != "$REQ_HASH" ]; then
	echo "[startup] installing dependencies into $PACKAGE_DIR"
	rm -rf "$PACKAGE_DIR"
	mkdir -p "$PACKAGE_DIR"
	set +e
	python -m pip install --upgrade --no-cache-dir --target="$PACKAGE_DIR" -r requirements.txt
	PIP_EXIT_CODE=$?
	set -e
	echo "[startup] pip install exit code: $PIP_EXIT_CODE"
	if [ "$PIP_EXIT_CODE" -ne 0 ]; then
		echo "[startup] dependency install failed"
		exit "$PIP_EXIT_CODE"
	fi
	printf "%s" "$REQ_HASH" > "$STAMP_FILE"
	echo "[startup] dependency install complete"
else
	echo "[startup] reusing existing dependency directory"
fi

echo "[startup] launching gunicorn"

exec gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app
