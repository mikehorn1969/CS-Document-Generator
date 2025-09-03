from app import app, db
from app.models import ServiceStandard, ServiceArrangement, ServiceContract
from dotenv import load_dotenv

load_dotenv()

def print_service_contracts():
    contracts = ServiceContract.query.all()
    print(f"Found {len(contracts)} service contracts:")
    for c in contracts:
        print(f"ID: {c.conid}, SID: {c.sid}, Special Conditions: {c.specialconditions}")


def print_service_standards():
    standards = ServiceStandard.query.all()
    print(f"Found {len(standards)} service standards:")
    for s in standards:
        # s.sid = "BRG003"
        # db.session.execute(
        #     db.update(ServiceStandard).where(ServiceStandard.stdid == s.stdid).values(sid=s.sid)
        # )
        # db.session.commit()
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