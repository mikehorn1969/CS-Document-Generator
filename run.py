import os
import sys

# Ensure pre-installed packages are available when App Service loads run:app.
packages_path = os.path.join(os.path.dirname(__file__), '.python_packages', 'lib', 'site-packages')
if os.path.isdir(packages_path) and packages_path not in sys.path:
    sys.path.insert(0, packages_path)

from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


