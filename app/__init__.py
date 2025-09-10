from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os, secrets
import dotenv

# Initialise the app
app = Flask(__name__)

# Load the config
# Select config class based on environment variable
dotenv.load_dotenv()
config_mode = os.environ.get('FLASK_CONFIG', 'DevelopmentConfig')
app.config.from_object(f'config.{config_mode}')

app.secret_key = secrets.token_hex(32)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, '..', 'service_standards.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Load the views

from app import views, models

print("DEBUG =", app.config['DEBUG'])
print("ENV =", app.config['ENV'])
print("Using config class:", config_mode)


  
