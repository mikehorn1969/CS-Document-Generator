from app import db
from sqlalchemy import Integer, String, Text, Identity

# Service Standard Model - typically 8 standard per service ID (sid)
class ServiceStandard(db.Model):

    __tablename__ = "ServiceStandard"      # <- exact table name in SQL Server
    __table_args__ = {"schema": "dbo"}     # <- schema name in SQL Server

    stdid = db.Column(Integer, Identity(start=1, increment=1), primary_key=True, name='stdid')
    sid = db.Column(String(10))
    ssn = db.Column(String(10))
    description = db.Column(String(255))

    def to_dict(self):
        return {
            "stdid": self.stdid,
            "sid": self.sid,
            "ssn": self.ssn,
            "description": self.description
        }

# Service Arrangement Model - one per weekday for each service ID (sid)
class ServiceArrangement(db.Model):
    
    __tablename__ = "ServiceArrangement"      # <- exact table name in SQL Server
    __table_args__ = {"schema": "dbo"}       # <- schema name in SQL Server

    arrid = db.Column(Integer, Identity(start=1, increment=1), primary_key=True, name='arrid')
    sid = db.Column(String(10))
    day = db.Column(String(10))
    defaultserviceperiod = db.Column(String(255))
    atservicebase = db.Column(String(255))
    atclientlocation = db.Column(String(255))
    atotherlocation = db.Column(String(255))

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

    __tablename__ = "ServiceContract"      # <- exact table name in SQL Server
    __table_args__ = {"schema": "dbo"}     # <- schema name in SQL Server

    conid = db.Column(Integer, Identity(start=1, increment=1), primary_key=True, name='conid')
    sid = db.Column(String(10))    
    specialconditions = db.Column(Text)



    


