from app import db
from sqlalchemy import Numeric

class ServiceStandard(db.Model):
    id = db.Column(db.Integer, primary_key=True, name='service_standard_id')
    sid = db.Column(db.String(10))
    ssn = db.Column(db.String(10))
    description = db.Column(db.String(255))

class ServiceArrangement(db.Model):
    id = db.Column(db.Integer, primary_key=True, name='service_arrangement_id')
    sid = db.Column(db.String(10))
    day = db.Column(db.String(10))
    defaultserviceperiod = db.Column(db.String(255))
    atservicebase = db.Column(db.String(255))
    atclientlocation = db.Column(db.String(255))
    atotherlocation = db.Column(db.String(255))

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

    
    


