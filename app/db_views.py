from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Numeric

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///service_standards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ServiceStandard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ssn = db.Column(db.String(100))
    description = db.Column(db.String(255))

class ServiceContract(db.Model):
    id = db.Column(db.Integer, primary_key=True, name='service_contract_id')
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
    dmname = db.Column(db.String(100))
    dmtitle = db.Column(db.String(50)) 
    dmemail = db.Column(db.String(100))
    dmphone = db.Column(db.String(50))
    specialconditions = db.Column(db.Text)
    noticeperiod = db.Column(db.Integer)  # Notice period in days
    noticeperiod_unit = db.Column(db.String(10))  # e.g., 'days', 'months'
    fees = db.Column(Numeric(10,2))  # Fees and payment terms
    feecurrency = db.Column(db.String(3),default='GBP')  # ISO 4217 currency code
    charges = db.Column(Numeric(10,2))  # Charges and payment terms
    chargecurrency = db.Column(db.String(3),default='GBP')  # ISO 4217 currency code
    requirementid = db.Column(db.Integer)
    candidateid = db.Column(db.Integer)
    placementid = db.Column(db.Integer) 
    candidatename = db.Column(db.String(100))
    candidateaddress = db.Column(db.String(255))
    candidateemail = db.Column(db.String(100))
    candidatephone = db.Column(db.String(50))
    candidateltdname = db.Column(db.String(100))
    candidateltdregno = db.Column(db.String(50))
    jobtitle = db.Column(db.String(100))