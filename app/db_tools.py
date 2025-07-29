# init_db.py

from db_views import app, db, ServiceStandard, ServiceContract  

def init_database():
    with app.app_context():
        db.create_all()
        print("✅ Database initialised and tables created.")

        
        # Optional: Show all rows
        all_rows = ServiceStandard.query.all()
        print(f"✅ Found {len(all_rows)} rows in ServiceStandard table.")

        all_contracts = ServiceContract.query.all()
        print(f"✅ Found {len(all_contracts)} rows in ServiceContract table.")




def query_service_contracts():
    with app.app_context():
        contracts = ServiceContract.query.all()
        for contract in contracts:
            print(f"SID: {contract.sid}, Service Name: {contract.servicename}, "
                  f"Company: {contract.companyname}, Start Date: {contract.startdate}, "
                  f"End Date: {contract.enddate}, Fees: {contract.fees}, Charges: {contract.charges}")



if __name__ == '__main__':
    init_database()
    query_service_contracts()
