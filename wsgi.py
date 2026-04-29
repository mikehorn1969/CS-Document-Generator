"""
WSGI entry point for Azure App Service.
Explicitly adds .python_packages to sys.path before importing the app.
"""
import sys
import os

# Add pre-installed packages to Python path before any imports
packages_path = os.path.join(os.path.dirname(__file__), '.python_packages', 'lib', 'site-packages')
if os.path.exists(packages_path):
    sys.path.insert(0, packages_path)

# Now import and return the app
from run import app

if __name__ == '__main__':
    app.run()
