from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os, secrets

# Initialise the app
app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, '..', 'service_standards.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Load the config
app.config.from_object('config')
app.secret_key = secrets.token_hex(32)

# Load the views

from app import views, models
