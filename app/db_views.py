from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///service_standards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ServiceStandard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ssn = db.Column(db.String(100))
    description = db.Column(db.String(255))
