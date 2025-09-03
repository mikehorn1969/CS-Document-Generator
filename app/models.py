from app import db
from sqlalchemy import Numeric

# Service Standard Model - typically 8 standard per service ID (sid)
class ServiceStandard(db.Model):
    stdid = db.Column(db.Integer, primary_key=True, name='stdid')
    sid = db.Column(db.String(10))
    ssn = db.Column(db.String(10))
    description = db.Column(db.String(255))

    def to_dict(self):
        return {
            "stdid": self.stdid,
            "sid": self.sid,
            "ssn": self.ssn,
            "description": self.description
        }

# Service Arrangement Model - one per weekday for each service ID (sid)
class ServiceArrangement(db.Model):
    arrid = db.Column(db.Integer, primary_key=True, name='arrid')
    sid = db.Column(db.String(10))
    day = db.Column(db.String(10))
    defaultserviceperiod = db.Column(db.String(255))
    atservicebase = db.Column(db.String(255))
    atclientlocation = db.Column(db.String(255))
    atotherlocation = db.Column(db.String(255))

    def to_dict(self):
        return {
            "arrid": self.arrid,
            "sid": self.sid,
            "day": self.day,
            "defaultserviceperiod": self.defaultserviceperiod,
            "atservicebase": self.atservicebase,
            "atclientlocation": self.atclientlocation,
            "atotherlocation": self.atotherlocation
        }

# Service Contract Model - one per service ID (sid), stores data not held in Colleague
class ServiceContract(db.Model):
    conid = db.Column(db.Integer, primary_key=True, name='conid')
    sid = db.Column(db.String(10))    
    specialconditions = db.Column(db.Text)
    
    
    
    


