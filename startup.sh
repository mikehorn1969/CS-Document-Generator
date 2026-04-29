#!/bin/bash
# Startup script for Azure App Service
# Sets PYTHONPATH to include pre-installed packages and launches gunicorn

export PYTHONPATH="/home/site/wwwroot/.python_packages/lib/site-packages:$PYTHONPATH"
gunicorn --bind 0.0.0.0:8000 --workers 4 run:app
