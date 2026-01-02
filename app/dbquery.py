# dbquery.py
from datetime import datetime
from flask import session
from app.models import ServiceArrangement, ServiceStandard
from app.helper import execute_db_query_with_retry, debugMode
from sqlalchemy import select, func
from app import db

def loadServiceStandards(service_id):

    from app import db_connected
    from flask import current_app
    import logging
    
    if not db_connected:
        logging.warning("loadServiceStandards: Database not connected, returning empty list")
        if debugMode():
            print("Database not connected yet, returning empty list")
        return []   
    
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} loadServiceStandards: Fetching standards for Service ID {service_id}")
        print(f"{datetime.now().strftime('%H:%M:%S')} loadServiceStandards: service_id type: {type(service_id)}, value: '{service_id}'")
        # Debug: Check what engine we're actually using
        print(f"{datetime.now().strftime('%H:%M:%S')} loadServiceStandards: Database URL: {db.engine.url}")
    
    logging.info(f"loadServiceStandards: Fetching standards for service_id='{service_id}'")
    
    if not service_id:                
        if debugMode():
            print(f"{datetime.now().strftime('%H:%M:%S')} loadServiceStandards: No Service ID provided")
        return []
    
    # Use case-insensitive comparison for Azure SQL Server compatibility
    stmt = select(ServiceStandard).where(func.upper(ServiceStandard.sid) == func.upper(service_id))
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} loadServiceStandards: SQL statement: {stmt}")
    logging.info(f"loadServiceStandards: Executing query for sid='{service_id}'")
    standards = execute_db_query_with_retry(stmt, "loadServiceStandards")
    logging.info(f"loadServiceStandards: Query returned {len(standards) if standards else 0} records")

    # Store SP standards in session for later use
    if service_id != "CS" and standards:    
        session['serviceStandards'] = [s.to_dict() for s in standards]

    return standards


def loadServiceArrangements(service_id):
    
    from app import db_connected
    from flask import current_app
    
    if not db_connected:
        if debugMode():
            print("Database not connected yet, returning empty list")
        return []   
    
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} loadServiceArrangements: Fetching arrangements for Service ID {service_id}")
        # Debug: Check what engine we're actually using
        print(f"{datetime.now().strftime('%H:%M:%S')} loadServiceArrangements: Database URL: {db.engine.url}")
    
    if not service_id:
        return []

    # Use case-insensitive comparison for Azure SQL Server compatibility
    stmt = select(ServiceArrangement).where(func.upper(ServiceArrangement.sid) == func.upper(service_id))
    arrangements = execute_db_query_with_retry(stmt, "loadServiceArrangements")

    # Store arrangements in session for later use
    if arrangements:
        session['serviceArrangements'] = [a.to_dict() for a in arrangements]

    return arrangements