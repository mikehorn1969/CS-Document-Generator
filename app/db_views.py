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

class ServiceContract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.String(10))
    servicename = db.Column(db.String(100))
    description = db.Column(db.String(255))
    startdate = db.Column(db.Date)
    duration = db.Column(db.Integer)  # Duration in months
    durationunit = db.Column(db.String(10))  # e.g., 'months', 'years'
    enddate = db.Column(db.Date)
    companyid = db.Column(db.Integer)
    companyname = db.Column(db.String(255))
    companyregistrationnumber = db.Column(db.String(50))
    companyaddress = db.Column(db.String(255))
    companyphone = db.Column(db.String(50)) 
    companyemail = db.Column(db.String(100))
    contactid = db.Column(db.Integer)
    contactname = db.Column(db.String(100))
    contacttitle = db.Column(db.String(50))
    contactemail = db.Column(db.String(100))
    contactphone = db.Column(db.String(50))
    contactaddress = db.Column(db.String(255))