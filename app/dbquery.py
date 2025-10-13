# dbquery.py
from datetime import datetime
from flask import session
from app.models import ServiceArrangement, ServiceStandard
from app.helper import execute_db_query_with_retry, debugMode
from sqlalchemy import select
from app import db

def loadServiceStandards(service_id):
        
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} loadServiceStandards: Fetching standards for Service ID {service_id}")
        
    if not service_id:                
        if debugMode():
            print(f"{datetime.now().strftime('%H:%M:%S')} loadServiceStandards: No Service ID provided")
        return []
    
    stmt = select(ServiceStandard).where(ServiceStandard.sid == service_id)
    standards = execute_db_query_with_retry(stmt, "loadServiceStandards")

    # Store SP standards in session for later use
    if service_id != "CS" and standards:    
        session['serviceStandards'] = [s.to_dict() for s in standards]

    return standards


def loadServiceArrangements(service_id):
    
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} loadServiceArrangements: Fetching arrangements for Service ID {service_id}")
    
    if not service_id:
        return []

    stmt = select(ServiceArrangement).where(ServiceArrangement.sid == service_id)
    arrangements = execute_db_query_with_retry(stmt, "loadServiceArrangements")

    # Store arrangements in session for later use
    if arrangements:
        session['serviceArrangements'] = [a.to_dict() for a in arrangements]

    return arrangements