#!/bin/bash
# Startup script for Azure App Service
# Rebuilds dependencies on Azure so native wheels match the App Service runtime,
# then launches gunicorn with the wsgi module that sets up sys.path correctly.

set -e

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
	python -m pip install --upgrade --no-cache-dir --target="$PACKAGE_DIR" -r requirements.txt
	printf "%s" "$REQ_HASH" > "$STAMP_FILE"
else
	echo "[startup] reusing existing dependency directory"
fi

echo "[startup] validating runtime imports"
PYTHONPATH="/home/site/wwwroot/$PACKAGE_DIR:$PYTHONPATH" python - <<'PY'
import importlib
import sys
import traceback

modules = ["flask_sqlalchemy", "azure.identity"]

for module_name in modules:
	try:
		module = importlib.import_module(module_name)
		module_version = getattr(module, "__version__", "unknown")
		print(f"[startup] import ok: {module_name}=={module_version}")
	except Exception as exc:
		print(f"[startup] import failed: {module_name}: {exc}", file=sys.stderr)
		traceback.print_exc()
		sys.exit(1)

print("[startup] all import checks passed")
PY

echo "[startup] launching gunicorn"

exec gunicorn --bind 0.0.0.0:8000 --workers 4 wsgi:app
