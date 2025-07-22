# init_db.py

from db_views import app, db, ServiceStandard

def init_database():
    with app.app_context():
        db.create_all()
        print("✅ Database initialised and tables created.")

        # Optional: Confirm table creation by adding a test row
        if not ServiceStandard.query.first():
            sample = ServiceStandard(ssn='TEST123', description='Example Service')
            db.session.add(sample)
            db.session.commit()
            print("✅ Test record inserted.")

        # Optional: Show all rows
        all_rows = ServiceStandard.query.all()
        print(f"✅ Found {len(all_rows)} rows in ServiceStandard table.")

if __name__ == '__main__':
    init_database()
