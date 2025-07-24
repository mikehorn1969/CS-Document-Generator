# query_service_standards.py

from app import app, db
from app.models import ServiceContract

with app.app_context():
    rows = ServiceContract.query.all()
    for row in rows:
        print(f"ID: {row.id}, SID: {row.sid}, Company Name: {row.companyname}"
              )
