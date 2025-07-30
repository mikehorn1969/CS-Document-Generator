from app import app, db
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from app.models import ServiceStandard, ServiceArrangement, ServiceContract as ContractModel
from app.c7query import  getC7candidate
from app.chquery import getCHRecord
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import select
import pandas as pd
from io import BytesIO


@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html', sid=session.get('sid', ''))


@app.route('/setsid', methods=["GET", "POST"])
def save_sid():
    if request.method == 'POST':
        sid = request.form.get('sid', '').strip()
        if sid:
            session['sid'] = sid.upper()  # Save Service ID to session
            
        else:
            error = "Please enter a valid Service ID."
            
    # For GET requests, render a simple form or redirect
    return redirect(url_for('index'))


@app.route('/clearsession', methods=["GET"])
def clear_session():
    session.clear()
    return redirect(url_for('index'))


@app.route('/colleaguedata', methods=["GET"])
def colleaguedata():
    """
    Handles GET requests to load and prepare contract data for the colleague view.
    This function attempts to retrieve contract data in the following order:
    1. From the session (if previously saved).
    2. From the database using the session's 'sid'.
    3. From an external C7 source if not found in session or database.
    If data is loaded from C7, it maps and formats relevant fields, including calculating the contract duration based on start and end dates. The contract data is then stored in the session and passed to the 'colleague.html' template for rendering.
    Returns:
        Rendered HTML template 'colleague.html' with contract data context.
    """
    
    if request.method == "GET":
        # Load existing contract data if available
        contract = {}
        sid = session.get('sid')
        # is there a saved contract in the session?
        saved_contract = session.get('sessionContract', {})
        
        # If not, try to load from the database
        if not saved_contract:
            saved_contract = ContractModel.query.filter_by(sid=sid).first()    

        # if there is no saved contract, try to load from C7
        if not saved_contract: 
            c7contractdata = getC7candidate(session.get('sid', ''))
            if not c7contractdata:
                c7contractdata = {}
            else:
                contract['sid'] = c7contractdata.get("sid", "").upper()
                contract['servicename'] = c7contractdata.get("servicename", "")
                contract['companyaddress'] = c7contractdata.get("companyaddress", "")
                contract['companyemail'] = c7contractdata.get("companyemail", "")
                contract['companyphone'] = c7contractdata.get("companyphone", "")
                contract['companyregistrationnumber'] = c7contractdata.get("companynumber", "")
                contract['companyname'] = c7contractdata.get("companyname", "")
                contract['contactname'] = c7contractdata.get("contactname", "")
                contract['contactaddress'] = c7contractdata.get("contactaddress", "")
                contract['contactemail'] = c7contractdata.get("contactemail", "")
                contract['contactphone'] = c7contractdata.get("contactphone", "")
                contract['contacttitle'] = c7contractdata.get("contacttitle", "")
                contract['jobtitle'] = c7contractdata.get("jobtitle", "")
                contract['companyname'] = c7contractdata.get("companyname", "")
                contract['fees'] = c7contractdata.get("fees", 0.0)
                contract['feecurrency'] = c7contractdata.get("feecurrency", "GBP")
                contract['charges'] = c7contractdata.get("charges", 0.0)
                contract['chargecurrency'] = c7contractdata.get("chargecurrency", "GBP")
                contract['requirementid'] = c7contractdata.get("requirementid", 0)
                contract['candidateid'] = c7contractdata.get("candidateid", 0)
                contract['placementid'] = c7contractdata.get("placementid", 0)
                contract['candidatename'] = c7contractdata.get("candidatename", "")
                contract['candidateaddress'] = c7contractdata.get("candidateaddress", "")
                contract['candidateemail'] = c7contractdata.get("candidateemail", "")
                contract['candidatephone'] = c7contractdata.get("candidatephone", "")
                contract['candidateltdname'] = c7contractdata.get("candidateltdname", "")
                contract['candidateltdregno'] = c7contractdata.get("candidateltdregno", "")
                contract['description'] = c7contractdata.get("description", "")
                contract['companyid'] = c7contractdata.get("companyid", 0)
                contract['contactid'] = c7contractdata.get("contactid", 0)  
                contract['noticeperiod'] = 4 # Default to 4 weeks, can be changed later
                contract['noticeperiod_unit'] = "weeks"  # Default to weeks, can be changed later

                start_date = c7contractdata.get("startdate", "")[:10]  # Ensure date is in YYYY-MM-DD format
                end_date = c7contractdata.get("enddate", "")[:10]  # Ensure date is in YYYY-MM-DD format
                duration = "0 days" # Default duration

                if start_date and end_date:
                
                    dt_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                    dt_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

                    delta = relativedelta(dt_end_date, dt_start_date)

                    parts = []
                    if delta.years > 0:
                        parts.append(f"{delta.years} year{'s' if delta.years > 1 else ''}") 
                    if delta.months > 0:
                        parts.append(f"{delta.months} month{'s' if delta.months > 1 else ''}")
                    if delta.days > 0:
                        weeks = delta.days // 7
                        parts.append(f"{weeks} week{'s' if weeks > 1 else ''}")
                        remaining_days = delta.days % 7
                        if remaining_days > 0:
                            parts.append(f"{remaining_days} day{'s' if remaining_days > 1 else ''}")
                    elif delta.days:
                        parts.append(f"{delta.days} day{'s' if delta.days > 1 else ''}")

                    duration = ", ".join(parts) if parts else "0 days" 
                
                contract['startdate'] = start_date
                contract['enddate'] = end_date
                contract['duration'] = duration
        else:
            # Update existing record using contract dictionary 
            fields = ["companyaddress", "companyemail", "companyphone", "companyregistrationnumber",
                      "companyname", "contactname", "contactaddress", "contactemail", "contactphone",
                      "contacttitle", "jobtitle", "fees", "feecurrency", "charges", "chargecurrency",
                      "requirementid", "candidateid", "placementid", "candidatename", "candidateaddress", "candidateemail",
                      "candidatephone", "candidateltdname", "candidateltdregno", "description", "companyid",
                      "contactid", "noticeperiod", "noticeperiod_unit", "duration", "startdate", "enddate"
                     ]

            contract = {
                field: getattr(saved_contract, field)
                for field in fields
                if hasattr(saved_contract, field)
            }

    session['sessionContract'] = contract

    return render_template(
        'colleague.html', contractdata=contract)


@app.route('/savecolleaguedata', methods=["POST"])
def savecolleaguedata():
    """
    Handles the saving of colleague contract data from a POST request.
    This function processes form data submitted via POST, retrieves or creates a contract record in the database,
    and updates its fields with values from the session's 'sessionContract' dictionary. If the contract does not
    exist, it creates a new record; otherwise, it updates the existing one. After saving changes to the database,
    it renders the 'colleague.html' template with the contract data.
    Returns:
        flask.Response: Rendered HTML template with contract data.
    Raises:
        Exception: Any exception during database operations is caught and stored as an error message.
    """

    if request.method == "POST":
        if 'btSave' in request.form:
            try:
                contract = session.get('sessionContract', {})
                sid = session.get('sid')
                if not sid: 
                    error = "Service ID is not set in the session."
                    return render_template('colleague.html', contractdata=contract, error=error) 
                
                # Try to find existing company in DB
                contractdb = ContractModel.query.filter_by(sid=sid).first()
                if not contractdb:
                    # Create new company record
                    contractdb = ContractModel( 
                        sid = contract.get("sid", "").upper(),
                        servicename = contract.get("servicename", "") )
                    db.session.add(contractdb)
                
                # Update existing record using contract dictionary 
                fields = ["companyaddress", "companyemail", "companyphone", "companyregistrationnumber",
                          "companyname", "contactname", "contactaddress", "contactemail", "contactphone",
                          "contacttitle", "jobtitle", "fees", "feecurrency", "charges", "chargecurrency",
                          "requirementid", "candidateid", "placementid", "candidatename", "candidateaddress", "candidateemail",
                          "candidatephone", "candidateltdname", "candidateltdregno", "description", "companyid",
                          "contactid", "noticeperiod", "noticeperiod_unit", "duration"
                         ]

                # Set defaults if necessary
                defaults = {
                    "fees": 0.0,
                    "charges": 0.0,
                    "requirementid": 0,
                    "candidateid": 0,
                    "companyid": 0,
                    "contactid": 0,
                    "noticeperiod": 4,
                    "noticeperiod_unit": "weeks",
                    "feecurrency": "GBP",
                    "chargecurrency": "GBP"
                }

                for field in fields:
                    value = contract.get(field, defaults.get(field, ""))
                    setattr(contractdb, field, value)

                # Handle dates separately         
                start_date = contract.get("startdate", "")  # Ensure date is in YYYY-MM-DD format
                end_date = contract.get("enddate", "") # Ensure date is in YYYY-MM-DD format  
                                     
                contractdb.startdate = parse_date(start_date)
                contractdb.enddate = parse_date(end_date)
                 
                db.session.commit()
            except Exception as e:
                error = str(e)
        
    return redirect(url_for('index'))
        

@app.route('/servicestandards', methods=['GET', 'POST'])
def set_servicestandards():

    sid = session.get('sid', '')
    standards = []
    
    if request.method == 'POST':
        stdids = request.form.getlist('id')
        ssns = request.form.getlist('ssn')
        descriptions = request.form.getlist('service-description')

        # You can zip and process them here:
        standards = list(zip(stdids, ssns, descriptions))

        # Example: print or save them
        for stdid, ssn, desc in standards:
            if ssn:
                rawDesc = desc.strip().strip('"')    
                record = None
                if stdid and stdid.isdigit():
                    record = ServiceStandard.query.get(int(stdid))  
                if record:
                    record.ssn = ssn.strip()
                    record.description = rawDesc
                else:   
                    if ssn.strip() and desc.strip():
                        db.session.add(ServiceStandard(sid=sid, ssn=ssn.strip(), description=rawDesc))
        
        db.session.commit()

        return redirect(url_for('index'))
    
    if request.method == "GET":
        if sid:
            standards = ServiceStandard.query.filter_by(sid=sid).all()
    
    # Store standards in session for later use
    session['serviceStandards'] = [s.to_dict() for s in standards]

    return render_template('standards.html', standards=standards)


@app.route('/delete/<int:stdid>', methods=['POST'])
def delete_standard(stdid):
    standard = ServiceStandard.query.get_or_404(stdid)
    db.session.delete(standard)
    db.session.commit()
    return redirect(url_for('set_servicestandards'))


@app.route('/servicearrangements', methods=['GET', 'POST'])
def manage_servicearrangements():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    sid = session.get('sid', '')
    
    if request.method == 'POST':
        for day in days:
            row = ServiceArrangement.query.filter_by(sid=sid,day=day).first()
            if not row:
                row = ServiceArrangement(sid=sid, day=day)

                db.session.add(row)

            if day in "Saturday Sunday":
                row.defaultserviceperiod = request.form.get(f'{day}_default', 'As agreed if required')
                row.atservicebase = request.form.get(f'{day}_base', 'As agreed if required')
                row.atclientlocation = request.form.get(f'{day}_client', 'As agreed if required')
                row.atotherlocation = request.form.get(f'{day}_other', 'Prior approval required')
            else:
                row.defaultserviceperiod = request.form.get(f'{day}_default', 'As specified 0800 - 1800')
                row.atservicebase = request.form.get(f'{day}_base', 'As specified')
                row.atclientlocation = request.form.get(f'{day}_client', 'As specified')
                row.atotherlocation = request.form.get(f'{day}_other', 'Prior approval required')

        db.session.commit()
        return redirect(url_for('index'))

    stmt = select(ServiceArrangement).where(ServiceArrangement.sid == sid)

    # Execute the query using session
    results = db.session.execute(stmt).scalars().all()

    # Build the dictionary    
    arrangements = {row.day: row for row in results}

    # Store arrangements in session for later use
    session['serviceArrangements'] = [s.to_dict() for s in results]
    
    return render_template('arrangements.html', arrangements=arrangements)


@app.route('/clientcontract', methods=['GET', 'POST'])
def prepare_contract():

    sid = session.get('sid', '')
    return render_template('clientcontract.html',sid=sid)


@app.route('/download_excel')
def download_excel():
    # Get session data
    service_standards = session.get('ServiceStandards', [])
    contract = session.get('sessionContract', {})
    arrangements = session.get('serviceArrangements', {})

    # Build rows
    data_rows = []
    for standard in service_standards:
        row = {}

        # Flatten standard fields
        if isinstance(standard, dict):
            row.update(standard)
        else:
            row['standard'] = str(standard)  # fallback if it's not a dict

        # Merge contract data
        row.update(contract)

        # Merge arrangement fields (optional flattening)
        for day, values in arrangements.items():
            if isinstance(values, dict):
                for k, v in values.items():
                    row[f"{day}_{k}"] = v
            else:
                row[day] = values

        data_rows.append(row)

    # Create DataFrame
    df = pd.DataFrame(data_rows)

    # Write to Excel in-memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Contract Export')

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="contract_export.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


def parse_date(value: str):
    try:
        # Parse the date string
        dt = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")

        # return as a date object        
        date_only = dt.date()
        return date_only
    
    except (ValueError, TypeError):
        return None
