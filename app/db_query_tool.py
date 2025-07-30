from app import app, db
from app.models import ServiceStandard, ServiceArrangement, ServiceContract

def print_service_contracts():
    contracts = ServiceContract.query.all()
    print(f"Found {len(contracts)} service contracts:")
    for c in contracts:
        print(f"ID: {c.conid}, SID: {c.sid}, Candidate Name: {c.candidatename}, Service Name: {c.servicename}, Company: {c.companyname}")

def print_service_standards():
    standards = ServiceStandard.query.all()
    print(f"Found {len(standards)} service standards:")
    for s in standards:
        print(f"ID: {s.stdid}, SID: {s.sid}, SSN: {s.ssn}, Description: {s.description}")

def print_service_arrangements():
    arrangements = ServiceArrangement.query.all()
    print(f"Found {len(arrangements)} service arrangements:")
    for a in arrangements:
        print(f"ID: {a.arrid}, SID: {a.sid}, Day: {a.day}, Default Period: {a.defaultserviceperiod}")

if __name__ == "__main__":
    with app.app_context():
        print("Service Contracts:")
        print_service_contracts()
        print("\nService Standards:")
        print_service_standards()
        print("\nService Arrangements:")
        print_service_arrangements()