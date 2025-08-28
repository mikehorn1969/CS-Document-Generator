from app import app, db
from flask import Flask, abort, render_template, request, redirect, url_for, session, send_file, flash, jsonify
from app.models import ServiceStandard, ServiceArrangement, ServiceContract as ContractModel
from app.c7query import  searchC7Candidate, getC7Clients, getContactsByCompany, gather_data, getC7Candidate
from app.chquery import validateCH, searchCH
from app.classes import Config, Company
from app.helper import loadConfig, formatName, uploadToSharePoint
from datetime import datetime
from sqlalchemy import select
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter
import requests
import time
from typing import List
#from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext

@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html', sid=session.get('sid', ''))


@app.route('/searchcandidates')
def search_candidates():
    q = request.args.get("q", "").strip()
    results = fetch_candidates(q)
    session["candidateName"] = results[0].get("candidateName") if results else None
    return jsonify(results)
    

@app.route('/searchclients')
def search_clients():
    q = request.args.get("q", "").strip()
    results = fetch_clients(q)
    return jsonify(results)


@app.route('/searchcontacts')
def search_contacts():
    qclient = request.args.get('client','').strip()
    qcontact = request.args.get("q", "").strip()
    results = fetch_contacts(qclient,qcontact)
    return jsonify(results)

          
@app.route('/clearsession', methods=["POST"])
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
    session_contract = session.get('sessionContract') or None
    if not session_contract:
        flash("Get a Candidate/Service Provider before continuing.", "error")
        return redirect(url_for('index'))
    else:
        contract = {}
        # Load existing contract data if available
        contract = gather_data(session_contract)
        if contract:
            session['sessionContract'] = contract
            session["candidateName"] = contract.get("candidateName", "")

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

    if 'btSave' in request.form:
        
            sid = session.get('sid')
            contract = session.get('sessionContract', {})
            
            if contract:
                # validate data against CH records
                # 1. Candidate
                sid = contract.get("sid", sid)
                ch_candidatename = contract.get("candidateName").split("(")
                ch_candidatename = ch_candidatename[0]
                ch_result = validateCH(contract.get("candidateltdregno"), contract.get("candidateltdname"), ch_candidatename)

                if not ch_result.get("Valid", False):
                    # Show pop-up on next render and stop here
                    flash(ch_result.get("Narrative",""), "error")
                    return redirect(url_for("colleaguedata"))

                # 2. Client - only where clientname is present
                client_companyname = contract.get("companyregistrationnumber")

                if client_companyname:
                    ch_result = validateCH(client_companyname, contract.get("companyname"))

                    if not ch_result.get("Valid", False):
                        # Show pop-up on next render and stop here
                        flash(ch_result.get("Narrative",""), "error")
                        return redirect(url_for("colleaguedata"))

            
            # If sid is present that means we have a placed Service Provider
            if sid:                             
                # Try to find existing company in DB        
                contractdb = {}
                contractdb = ContractModel.query.filter_by(sid=sid).first()

                # Create new company record if not found
                if not contractdb:
                    # Create new company record
                    new_sid = contract.get("sid", "") if sid else "MSA"
                    contractdb = ContractModel()
                    db.session.add(contractdb)
                    setattr(contractdb, "sid", new_sid.upper())
                    setattr(contractdb, "servicename", contract.get("servicename", ""))

                # Update existing record using contract dictionary 
                fields = ["companyname", "companyaddress", "companyemail", "companyphone", "companyregistrationnumber", "companyjurisdiction",
                            "sid", "servicename",
                            "contactname", "contactaddress", "contactemail", "contactphone", "contacttitle", 
                            "jobtitle", "charges", "chargecurrency", 
                            "requirementid", "candidateId", "placementid", "candidatename", "candidateaddress", "candidateemail",
                            "candidatephone", "candidateltdname", "candidateltdregno", "candidatejurisdiction", "description", "companyid",
                            "contactid", "noticeperiod", "noticeperiod_unit", "duration"
                            ]

                # Set defaults if necessary
                defaults = {
                    "fees": 0.0,
                    "charges": 0.0,
                    "requirementid": 0,
                    "candidateId": 0,
                    "companyid": 0,
                    "contactid": 0,
                    "noticeperiod": 4,
                    "noticeperiod_unit": "weeks",
                    "feecurrency": "GBP",
                    "chargecurrency": "GBP"
                }

                for field in fields:
                    # Tech Debt: unify candidateName casing
                    if field == "candidatename":
                        value = contract.get("candidateName", defaults.get(field, ""))
                    else:
                        value = contract.get(field, defaults.get(field, ""))
                    setattr(contractdb, field, value)

                # Handle dates separately  
                if ( contract.get("startdate") and contract.get("enddate") ):
                    start_date = datetime.strptime(contract.get("startdate", ""), "%d/%m/%Y")                
                    end_date  = datetime.strptime(contract.get("enddate", ""), "%d/%m/%Y")
                
                    setattr(contractdb,"startdate",start_date)
                    setattr(contractdb,"enddate", end_date)
                    
                db.session.commit()
                    
    return redirect(url_for('index'))
        

@app.route('/servicestandards', methods=['GET', 'POST'])
def set_servicestandards():

    session_contract = session.get('sessionContract') or None
    if not session_contract:
        flash("Pick a Candidate/Service Provider before continuing.", "error")
        return redirect(url_for('index'))
    else:
        contract = {}
        # Load existing contract data if available
        contract = gather_data(session_contract)
        if contract:
            session['sessionContract'] = contract
            session["candidateName"] = contract.get("candidateName", "")

    standards = []
    
    if request.method == 'POST':
        # Gather standards data
        stdids = request.form.getlist('id')
        ssns = request.form.getlist('ssn')
        descriptions = request.form.getlist('service-description')

        # Zip and process them here:
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
                        new_standard = ServiceStandard()
                        new_standard.sid = sid
                        new_standard.ssn = ssn.strip()
                        new_standard.description = rawDesc
                        db.session.add(new_standard)
        
        db.session.commit()

        # Store standards in session for later use
        #session['serviceStandards'] = [s.to_dict() for s in standards]
        session['serviceStandards'] = [
            {'id': stdid, 'ssn': ssn, 'description': desc.strip().strip('"')}
            for stdid, ssn, desc in standards
        ]
        return redirect(url_for('index'))
    
    if request.method == "GET":
        service_id = contract.get("sid", "")
        
        if service_id:
            # Tech debt - use select query method
            standards = ServiceStandard.query.filter_by(sid=service_id).all()
    
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

    session_contract = session.get('sessionContract') or None
    if not session_contract:
        flash("Pick a Candidate/Service Provider before continuing.", "error")
        return redirect(url_for('index'))
    else:
        contract = {}
        # Load existing contract data if available
        contract = gather_data(session_contract)
        if contract:
            session['sessionContract'] = contract
            session["candidateName"] = contract.get("candidateName", "")
            service_id = contract.get("sid", "")

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']   
    if request.method == 'POST':
        for day in days:
            # Tech debt: use select query
            row = ServiceArrangement.query.filter_by(sid=service_id,day=day).first()
            if not row:
                row = ServiceArrangement()
                row.sid = service_id
                row.day = day
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

        raw = request.form.get('SpecialConditions')
        specialconditions = raw.strip() if isinstance(raw, str) else ''

        contract_record = db.session.scalar(
            select(ContractModel).where(ContractModel.sid == service_id)
        )
        if contract_record is None:
            abort(404, f"No contract found for sid={service_id!r}")

        contract_record.specialconditions = specialconditions
        db.session.commit()

        session['specialConditions'] = specialconditions

        return redirect(url_for('index'))

    arr_stmt = select(ServiceArrangement).where(ServiceArrangement.sid == service_id)

    # Execute the query using session
    arr_records = db.session.execute(arr_stmt).scalars().all()

    # Build the dictionary    
    arrangements = {row.day: row for row in arr_records}

    if service_id:
        contract_stmt = select(ContractModel).where(ContractModel.sid == service_id)   
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

    export_columns = ["ClientName", "ClientAddress", "Jursidiction", "ClientCompanyNo",                       
                      "ServiceID", "ServiceName", "ClientCharge", 
                      "ContactName", "ContactTitle", "ContactEmail", "ContactPhone", "ContactAddress",  
                      "ServiceStart", "ServiceEnd", "Duration", 
                      "NoticePeriod", "NoticeUOM"]
    
    for raw_field, column_name in zip(fields, export_columns):

        if raw_field == "companyjurisdiction":
            tmp_field = contract.get(raw_field,"")
            if tmp_field.strip().lower() == "england-wales":
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

    row["SpecialConditions"] = special_conditions

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
                row[f"ACL{day_string}"] = v
            elif k == 'atotherlocation':
                row[f"AOL{day_string}"] = v
            elif k == 'atservicebase':
                row[f"ASB{day_string}"] = v
            elif k == 'defaultserviceperiod':
                row[f"DSP{day_string}"] = v
                
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
    contract = session.get('sessionContract', {})
    return render_template('spmsa.html', contract=contract)


@app.route('/candidate_validate_ch', methods=['POST'])
def candidate_validate_ch():
    company_number = request.form.get('CandidateLtdNo', '')
    company_name = request.form.get('CandidateLtdCo', '')
    result = validateCH(company_number, company_name)
    if result is None:
        # Return an empty JSON object or a message
        return jsonify({'error': 'No result found'}), 404
    return jsonify(result)


@app.route('/download_sp_msa', methods=['POST'])
def download_sp_msa():

    # Get session data
    contract = session.get('sessionContract', {})
    if not contract:
        flash("Set a Service Provider before continuing.", "error")
        return redirect(url_for('index'))

    agreement_date = request.form.get('AgreementDate', '')
    
    f_agreement_date = datetime.strptime(agreement_date, "%Y-%m-%d").date()
    f_agreement_date = f_agreement_date.strftime("%d/%m/%Y")

    # Build rows
    data_rows = []
    row = {}
    row["AgreementDate"] = f_agreement_date
    fields = ["candidateName", "candidateltdname", "candidatejurisdiction", "candidateltdregno", "candidateaddress"]
    
    export_columns = ["CandidateName", "CandidateLtdName", "CandidateJurisdiction", "CandidateLtdRegNo", "CandidateAddress"]
    
    # Populate row with contract fields    
    # making any neccessary substitutions
    for raw_field, column_name in zip(fields, export_columns):
        if ( raw_field == "candidatejurisdiction" and contract.get(raw_field,'').strip().lower() == "england-wales" ):
            field = "England and Wales"
        elif ( raw_field == "candidatename" ):
            field = formatName(contract.get(raw_field,''))
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


@app.route('/clientmsa', methods=['GET', 'POST'])
def prepare_client_msa():
    contract = session.get('sessionContract', {})
    return render_template('clientmsa.html', contract=contract)


@app.route('/download_client_msa', methods=['POST'])
def download_client_msa():
        
    # Get session data
    contract = session.get('sessionContract', {})
    agreement_date = request.form.get('AgreementDate', '')
    f_agreement_date = ''

    if agreement_date != '':
        f_agreement_date = datetime.strptime(agreement_date, "%Y-%m-%d").date()
        f_agreement_date = f_agreement_date.strftime("%d/%m/%Y")

    # Build rows
    data_rows = []
    row = {}
    row["AgreementDate"] = f_agreement_date
    fields = ["companyname", "companyregistrationnumber", "companyjurisdiction", "companyaddress"]

    export_columns = ["ClientName", "CompanyNumber", "Jurisdiction", "CompanyAddress"]

    # Populate row with contract fields
    # making any neccessary substitutions
    for raw_field, column_name in zip(fields, export_columns):
        if ( raw_field == "companyjurisdiction" and contract.get(raw_field,'').strip().lower() == "england-wales" ):
            field = "England and Wales"
        elif ( raw_field == "candidatename" ):
            field = formatName(contract.get(raw_field,''))
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
    
    # Tech Debt: load credentials from config

    site_url = "https://jjag.sharepoint.com/sites/InternalTeam"

    cert_settings = {
        'client_id': '51d03106-4726-442c-86db-70b32fa7547f', 
        'thumbprint': "6B36FBFC86FB1C019EB6496494B9195E6D179DDB",
        'cert_path': 'mycert.pem'
    }
    #ctx = ClientContext(site_url).with_credentials(UserCredential(username, password))
    ctx = ClientContext(site_url).with_client_certificate('changespecialists.co.uk', **cert_settings)

    target_url = f"{site_url}/Shared Documents/Mike/Uploads"
    download_name=f"{contract.get('companyname')} Client MSA.xlsx"

    # returns target_file.serverRelativeUrl
    file_bytes = final_output.getvalue()
    uploaded_file = uploadToSharePoint(file_bytes, download_name, target_url, ctx)

    if uploaded_file:    
        return "Success", 200
    else:
        return send_file(
            final_output,
            as_attachment=True,
            download_name=f"{contract.get('companyname')} Client MSA.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


@app.route('/chfetch', methods=['POST'])
def get_company_number():
    ltd_name = request.form.get('clientname','')
    data = {}
    if ltd_name:
        ch_result = searchCH(ltd_name)
        items = ch_result.get("items", [])
        match = next((item for item in items if item.get('title') == ltd_name.upper()), None)
        if match:
            data = {
                "regnumber": match.get("company_number", ""),
                "address": match.get("address_snippet", "")
            }
    return jsonify(data)
    

# --- Tiny in-memory cache to reduce API calls while typing ---
CACHE_TTL = 60  # seconds
_cache: dict[str, tuple[float, List[dict]]] = {}


def _cache_get(q: str) -> List[dict] | None:
    now = time.time()
    if q in _cache:
        ts, data = _cache[q]
        if now - ts <= CACHE_TTL:
            return data
        else:
            _cache.pop(q, None)
    return None


def _cache_set(q: str, data: List[dict]) -> None:
    _cache[q] = (time.time(), data)


def fetch_candidates(query: str) -> List[dict]:
    """
    Call the Colleague7 API to fetch candidates matching the query.
    """
    if not query:
        return []

    # Check cache first
    qkey = query.lower().strip()
    cached = _cache_get(qkey)
    if cached is not None:
        return cached

    # load config
    if Config.find_by_name("C7 Key") is None:
        loadConfig()

    user_id = Config.find_by_name("C7 Userid")
    hdr = Config.find_by_name("C7 HDR")

    # Build request
    payload = []
    try:
        candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Search?UserId={user_id}&Surname={query}"            
        candidate_search_response = requests.get(candidate_url, headers=hdr)                   
        if candidate_search_response.status_code == 200:
            payload = candidate_search_response.json()
    except:        
        return []
    
    # Normalise to list[str] — tweak this for your API’s schema
    results = []
    
    for candidate_id in payload:

        candidate_data = getC7Candidate(candidate_id, query)
        if not candidate_data:
            continue

        candidate_dict = {
            "candidateId": candidate_data.get("candidateId",0) or candidate_data.get("candidateid",0),
            "candidateName": candidate_data.get("name",""),
            "candidateEmail": candidate_data.get("email",""),
            "candidatePhone": candidate_data.get("phone",""),
            "candidateLtdName": candidate_data.get("ltd_name",""),
            "candidateLtdRegNo": candidate_data.get("registration_number",""),
            "candidateJurisdiction": candidate_data.get("jurisdiction",""),
            "candidateAddress": candidate_data.get("address",""),
        }

        results.append(candidate_dict)

    # Update cache
    _cache_set(qkey, results)
    return results


def fetch_clients(query: str) -> List[dict]:
    """
    Normalise clients into a list of strings.
    """
    if not query:
        return []

    # Check cache first
    qkey = query.lower().strip()
    cached = _cache_get(qkey)
    if cached is not None:
        return cached

    payload = []
    if Company.count() == 0:
        payload = getC7Clients()
    else:
        payload = Company.get_all_companies()
    
    results: List[dict] = []

    if isinstance(payload,list):
        if len(payload) == 0:
            return[]
        for client in payload:
            if client.companyname.lower().startswith(qkey):
                results.append(client.companyname)

    # Update cache
    _cache_set(qkey, results)
    return results


def fetch_contacts(qclient: str, qcontact: str) -> List[dict]:
    """
    Normalise client contacts into a list of strings.
    """
    if not qclient:
        return []

    # Check cache first
    qkey = qcontact.lower().strip()
    cached = _cache_get(qkey)
    if cached is not None:
        return cached

    payload = getContactsByCompany(qclient)
    results: List[dict] = []

    if isinstance(payload, list):
        if len(payload) == 0:
            return []

        for clientcontact in payload:
            contact_data = {}
            if clientcontact.get("ContactName", "").lower().startswith(qkey):   
                contact_data["ContactName"] = clientcontact.get("ContactName", "")
                contact_data["ContactEmail"] = clientcontact.get("ContactEmail", "")
                contact_data["ContactPhone"] = clientcontact.get("ContactPhone", "")
                results.append(contact_data)

    # Update cache
    _cache_set(qkey, results)
    return results

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


@app.route('/client_validate_ch', methods=['POST'])
def client_validate_ch():
    company_number = request.form.get('company_number', '')
    company_name = request.form.get('company_name', '')
    result = validateCH(company_number, company_name)
    if result is None:
        # Return an empty JSON object or a message
        return jsonify({'error': 'No result found'}), 404
    return jsonify(result)


@app.route('/candidatefetch', methods=['POST'])
def candidatefetch():
    candidate_name = request.form.get('CandidateName', '')
    if candidate_name:
        result = searchC7Candidate(candidate_name)

        if not result:
            return jsonify({'error': 'No candidates found'}), 404
        
    return jsonify(result)


@app.post("/contract/candidate")
def set_contract_candidate():
    data = request.get_json(force=True) or {}
    cand_id = data.get("candidateId")
    if not cand_id:
        return jsonify(error="candidateId required"), 400

    contract = session.get("sessionContract", {})
    contract["candidateId"] = cand_id
    session["sessionContract"] = contract
    session["candidateName"] = data.get("candidateName")
    session.modified = True
    return ("", 204)
