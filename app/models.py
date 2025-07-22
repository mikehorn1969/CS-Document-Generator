from app import db

class ServiceStandard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ssn = db.Column(db.String(10))
    description = db.Column(db.String(255))

class ServiceArrangement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10))
    defaultserviceperiod = db.Column(db.String(255))
    atservicebase = db.Column(db.String(255))
    atclientlocation = db.Column(db.String(255))
    atotherlocation = db.Column(db.String(255))
