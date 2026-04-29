#!/bin/bash
# Startup script for Azure App Service
# Dependencies are packaged during CI deployment.

set -e

cd /home/site/wwwroot
echo "[startup] launching gunicorn"

exec gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app
