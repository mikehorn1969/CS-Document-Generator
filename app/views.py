from app import app, db
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from app.models import ServiceStandard, ServiceArrangement, ServiceContract as ContractModel
from app.c7query import  getC7candidate, searchC7Candidate
from app.chquery import searchCH
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import select
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter


@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html', sid=session.get('sid', ''))


@app.route('/setsid', methods=["GET", "POST"])
def save_sid():
    """
    Handles POST requests to save a candidate's Service ID (SID) and surname in the session.
    If a surname is provided in the form data, attempts to find the candidate's surname and SID
    using the `searchC7Candidate` function and saves them to the session if found.
    If no surname is provided, attempts to find a contract record by SID using the `ContractModel`.
    If found, saves the candidate's name and SID to the session.
    Finally, redirects the user to the 'index' route.
    """
    
    if request.method == 'POST':
        sid_input = request.form.get('sid', '').strip()
        surname_input = request.form.get('surname','').strip()
        
        if surname_input:
            found_surname, found_sid = searchC7Candidate(surname_input)
            if found_surname:
                session['candidate_surname'] = found_surname
            if found_sid:
                session['sid'] = found_sid.upper()  # Save Service ID to session
        elif sid_input:
            contract_stmt = select(ContractModel).where(ContractModel.sid == sid_input.upper())
            contract_record = db.session.execute(contract_stmt).scalar_one_or_none()
            if contract_record:                
                session['candidate_surname'] = contract_record.candidatesurname #wibble        
            session['sid'] = sid_input.upper()

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
    
    contract = {}
    sid = session.get('sid') or None
    candidate_surname = session.get('candidate_surname') or None

    if sid or candidate_surname:
        # Load existing contract data if available
        contract = {}        
        c7contractdata = getC7candidate(sid,candidate_surname)
        if c7contractdata:                   
            contract['sid'] = c7contractdata.get("sid", "")
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
            contract['candidatejurisdiction'] = c7contractdata.get("candidatejurisdiction", "")
            contract['description'] = c7contractdata.get("description", "")
            contract['companyid'] = c7contractdata.get("companyid", 0)
            contract['contactid'] = c7contractdata.get("contactid", 0)  
            contract['noticeperiod'] = 4 # Default to 4 weeks, can be changed later
            contract['noticeperiod_unit'] = "weeks"  # Default to weeks, can be changed later
            
            start_date = c7contractdata.get("startdate", "")
            end_date = c7contractdata.get("enddate", "")
            duration = "0 days" # Default duration

            # calculate duration
            if start_date and end_date:
                                
                start_date_obj = datetime.strptime(start_date, "%d/%m/%Y").date()
                end_date_obj  = datetime.strptime(end_date, "%d/%m/%Y").date()
                delta = relativedelta(end_date_obj, start_date_obj)

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
                contractdb = {}
                # Try to find existing company in DB
                if sid:                                     
                    contractdb = ContractModel.query.filter_by(sid=sid).first()

                if not contractdb:
                    # Create new company record
                    new_sid = contract.get("sid", "") if sid else "MSA"
                    contractdb = ContractModel( 
                        sid = new_sid.upper(),
                        servicename = contract.get("servicename", "") )
                    db.session.add(contractdb)
                
                # Update existing record using contract dictionary 
                fields = ["companyaddress", "companyemail", "companyphone", "companyregistrationnumber",
                          "companyname", "contactname", "contactaddress", "contactemail", "contactphone",
                          "contacttitle", "jobtitle", "charges", "chargecurrency", "charges", "chargecurrency",
                          "requirementid", "candidateid", "placementid", "candidatename", "candidateaddress", "candidateemail",
                          "candidatephone", "candidateltdname", "candidateltdregno", "candidatejurisdiction", "description", "companyid",
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
                if ( contract.get("startdate") and contract.get("enddate") ):
                    start_date = datetime.strptime(contract.get("startdate", ""), "%d/%m/%Y")                
                    end_date  = datetime.strptime(contract.get("enddate", ""), "%d/%m/%Y")
                
                    contractdb.startdate = start_date 
                    contractdb.enddate = end_date
                 
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

        # Store standards in session for later use
        #session['serviceStandards'] = [s.to_dict() for s in standards]
        session['serviceStandards'] = [
            {'id': stdid, 'ssn': ssn, 'description': desc.strip().strip('"')}
            for stdid, ssn, desc in standards
        ]
        return redirect(url_for('index'))
    
    if request.method == "GET":
        if sid:
            # Tech debt - use select query method
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
            # Tech debt: use select query
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

        contract_stmt = select(ContractModel).where(ContractModel.sid == sid)
        contract_record = db.session.execute(contract_stmt).scalar_one_or_none()
        
        contract_record.specialconditions = request.form.get('SpecialConditions', '').strip()
        # Tech debt: store special conditions in session
        session['specialConditions'] = contract_record.specialconditions if contract_record else ''
            
        db.session.commit()

        
        # Tech debt: store special conditions in session
        session['specialConditions'] = contract_record.specialconditions if contract_record else ''

        return redirect(url_for('index'))

    arr_stmt = select(ServiceArrangement).where(ServiceArrangement.sid == sid)

    # Execute the query using session
    arr_records = db.session.execute(arr_stmt).scalars().all()

    # Build the dictionary    
    arrangements = {row.day: row for row in arr_records}

    contract_stmt = select(ContractModel).where(ContractModel.sid == sid)   
    contract_record = db.session.execute(contract_stmt).scalar_one_or_none()

    # Store arrangements in session for later use
    session['serviceArrangements'] = [s.to_dict() for s in arr_records]
 
    return render_template('arrangements.html', arrangements=arrangements, contract=contract_record)


@app.route('/clientcontract', methods=['GET', 'POST'])
def prepare_client_contract():

    sid = session.get('sid', '')
    return render_template('clientcontract.html',sid=sid)


@app.route('/download_client_contract', methods=['POST'])
def download_client_contract():
    # Get session data
    service_standards = session.get('serviceStandards', [])
    contract = session.get('sessionContract', {})
    arrangements = session.get('serviceArrangements', {})
    agreement_date = request.form.get('AgreementDate', '')
    
    f_agreement_date = datetime.strptime(agreement_date, "%Y-%m-%d").date()
    f_agreement_date = f_agreement_date.strftime("%d/%m/%Y")

    special_conditions = session.get('specialConditions', '').strip()
    sid = session.get('sid', '')

    # Build rows
    data_rows = []
    row = {}
    row['AgreementDate'] = f_agreement_date

    # Populate row with contract fields
    # making any neccessary substituions
    fields = ["companyname", "companyaddress", "companyjurisdiction", "companyregistrationnumber", 
              "sid", "servicename", "charges", 
              "contactname", "contacttitle", "contactemail", "contactphone", "contactaddress", 
              "startdate", "enddate", "duration", 
              "noticeperiod", "noticeperiod_unit"]

    export_columns = ["ClientName", "ClientAddress", "Jursidiction" ,"ClientCompanyNo"
                      "ServiceID", "ServiceName", "ClientCharge", 
                      "ContactName", "ContactTitle", "ContactEmail", "ContactPhone", "ContactAddress",  
                      "ServiceStart", "ServiceEnd", "Duration", 
                      "NoticePeriod", "NoticeUOM"]
    
    for raw_field, column_name in zip(fields, export_columns):
        if ( raw_field == "companyjurisdiction" and contract.get(raw_field,'').strip().lower() == "england-wales" ):
            field = "England and Wales"
        else:
            field = contract.get(raw_field, '')
        # Tech debt: hard coded AD details
        if (raw_field == "dmname" ):
            field = "Julian Brown"
        if (raw_field == "dmtitle" ):
            field = "Practice Director"
        if (raw_field == "dmemail" ):
            field = "julian.brown@changespecialists.co.uk"
        if (raw_field == "dmphone" ):
            field = "07123 123456"    

        row[column_name] = field

    row["specialconditions"] = special_conditions

    std_fields = ["ssn", "description"]
    std_export_columns = ["SSN", "SSDescription"]
    
    # Flatten service standards
    for i in range(10):
                
        # add the standard fields
        if i < len(service_standards):
            standard = service_standards[i]        
        else: 
            standard = {}

        for field, column_name in zip(std_fields, std_export_columns):
            f_column_name = f"{column_name}{i}"

            if standard:
                row[f_column_name] = standard.get(field, '')
            else:
                row[f_column_name] = ''

    # Flatten arrangements
    for arr in arrangements:
        day_string = arr['day'][:3]  # Get first 3 letters of the day
        for k, v in arr.items():
            if k == 'atclientlocation':
                row[f"ACL_{day_string}"] = v
            elif k == 'atotherlocation':
                row[f"AOL_{day_string}"] = v
            elif k == 'atservicebase':
                row[f"ASB_{day_string}"] = v
            elif k == 'defaultserviceperiod':
                row[f"DSP_{day_string}"] = v
                
    data_rows.append(row)

    # Create DataFrame
    df = pd.DataFrame(data_rows)

    # Write to Excel in-memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

    output.seek(0)
    wb = load_workbook(output)
    ws = wb['Sheet1']

    # add table
    df_rows = len(df) + 1
    df_cols = len(df.columns)
    df_range = f"A1:{get_column_letter(df_cols)}{df_rows}"

    table1 = Table(displayName="Table1", ref=df_range)
    table1.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium9", showRowStripes=False, showColumnStripes=False
    )
    ws.add_table(table1)

    # Save final output
    final_output = BytesIO()
    wb.save(final_output)
    final_output.seek(0)
    
    return send_file(
        final_output,
        as_attachment=True,
        download_name=f"{sid} Client contract data.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@app.route('/spmsa', methods=['GET', 'POST'])
def prepare_sp_msa():

    return render_template('spmsa.html')


@app.route('/download_sp_msa', methods=['POST'])
def download_sp_msa():

    # Get session data
    contract = session.get('sessionContract', {})
    agreement_date = request.form.get('AgreementDate', '')
    
    f_agreement_date = datetime.strptime(agreement_date, "%Y-%m-%d").date()
    f_agreement_date = f_agreement_date.strftime("%d/%m/%Y")

    # Build rows
    data_rows = []
    row = {}
    row["AgreementDate"] = f_agreement_date
    fields = ["candidatename", "candidateltdname", "candidatejurisdiction", "candidateltdregno", "candidateaddress"]
    
    export_columns = ["CandidateName", "CandidateLtdName", "CandidateJurisdiction", "CandidateLtdRegNo", "CandidateAddress"]
    
    # Populate row with contract fields    
    # making any neccessary substitutions
    for raw_field, column_name in zip(fields, export_columns):
        if ( raw_field == "candidatejurisdiction" and contract.get(raw_field,'').strip().lower() == "england-wales" ):
            field = "England and Wales"
        else:
            field = contract.get(raw_field, '')

        row[column_name] = field
            
    data_rows.append(row)

    # Create DataFrame
    df = pd.DataFrame(data_rows)

    # Write to Excel in-memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')

    output.seek(0)
    wb = load_workbook(output)
    ws = wb['Sheet1']

    # add table
    df_rows = len(df) + 1
    df_cols = len(df.columns)
    df_range = f"A1:{get_column_letter(df_cols)}{df_rows}"

    table1 = Table(displayName="Table1", ref=df_range)
    table1.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium9", showRowStripes=False, showColumnStripes=False
    )
    ws.add_table(table1)

    # Save final output
    final_output = BytesIO()
    wb.save(final_output)
    final_output.seek(0)

    return send_file(
        final_output,
        as_attachment=True,
        download_name=f"{contract.get('candidateltdname')} Service Provider MSA.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


def parse_date(value: str):
    try:
        # Parse the date string
        
        if len(value) >= 9:
            dt = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")
        else:
            dt = datetime.strptime(value, "%a, %d %b")
        # return as a date object        
        date_only = dt.date()
        return date_only
    
    except (ValueError, TypeError):
        return None


def list_to_dict(prefix_list):
    result = {}
    for item in prefix_list:
        if ": " in item:
            key, value = item.split(": ", 1)
            result[key] = value
    return result
