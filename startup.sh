#!/bin/bash
# Startup script for Azure App Service
# Launches gunicorn with the wsgi module that sets up sys.path correctly

exec gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app
