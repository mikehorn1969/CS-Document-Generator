from app import app, db
from flask import Flask, render_template, request, redirect, url_for, session
from app.models import ServiceStandard, ServiceArrangement, ServiceContract as ContractModel
from app.c7query import getC7Clients, getContactsByCompany, getC7Requirements, getC7RequirementCandidates
from app.chquery import getCHRecord
from app.classes import Company, Contact, Requirement, Candidate


@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html', sid=session.get('sid', ''))


@app.route('/setsid', methods=["GET", "POST"])
def save_sid():
    if request.method == 'POST':
        sid = request.form.get('sid', '').strip()
        if sid:
            session['sid'] = sid  # Save Service ID to session
            
        else:
            error = "Please enter a valid Service ID."
            
    # For GET requests, render a simple form or redirect
    return redirect(url_for('index'))


@app.route('/clearsession', methods=["GET"])
def clear_session():
    session.clear()
    return redirect(url_for('index'))


@app.route('/colleaguedata', methods=["GET", "POST"])
def colleaguedata():
    
    clients = getC7Clients()

    client_names = [client["CompanyName"] for client in clients]
    client_fields = ['companyname', 'address', 'emailaddress', 'phone', 'companyNumber']
    client_record = []


    contact_names = [] 
    contact_fields = ['name', 'title', 'address', 'emailaddress', 'phone']
    contact_record = []

    req_names = []
    req_fields = ['description', 'jobtitle']
    req_record = []

    candidate_names = []
    candidate_fields = ['candidateName', 'companyNumber', ]
    candidate_record = []

    ch_record = None
    ch_no = ""
    ch_fields = ['company_number', 'company_name', 'company_status']
    selected_company = session.get('selected_company', '')
    selected_contact = session.get('selected_contact', '')
    selected_requirement = session.get('selected_requirement', '')
    selected_candidate = session.get('selected_candidate', '')

    if request.method == "POST":
        if 'btCompany' in request.form:
            selected_company = request.form.get("company")
            session['selected_company'] = selected_company
            session['selected_contact'] = ''
            print(f"Selected company: {selected_company}, session sid: {session['sid']}")

            # save/update company in the database
            try:
                # Find client data from C7 API
                client_data = next((client for client in clients if client["CompanyName"] == selected_company), None)
                if client_data:
                    # Try to find existing company in DB
                    company = ContractModel.query.filter_by(sid=session['sid']).first()
                    if not company:
                        # Create new company record
                        company = ContractModel(
                        sid=session['sid'],    
                        companyname=client_data.get("CompanyName", ""),
                        companyaddress=client_data.get("CompanyAddress", ""),
                        companyemail=client_data.get("CompanyEmail", ""),
                        companyphone=client_data.get("CompanyPhone", ""),
                        companyregistrationnumber=client_data.get("CompanyNumber", "")
                        )
                        db.session.add(company)
                    else:
                        # Update existing record
                        company.companyaddress = client_data.get("CompanyAddress", "")
                        company.companyemail = client_data.get("CompanyEmail", "")
                        company.companyphone = client_data.get("CompanyPhone", "")
                        company.companyregistrationnumber = client_data.get("CompanyNumber", "")
                        
                    db.session.commit()
            except Exception as e:
                error = str(e)

            
        if 'btContact' in request.form:
            selected_contact = request.form.get('contact')
            session['selected_contact'] = selected_contact
            session['selected_requirement'] = ''
            return redirect(url_for('colleaguedata'))
        
        if 'btRequirement' in request.form:
            selected_requirement = request.form.get('requirement')
            session['selected_requirement'] = selected_requirement
            session['selected_candidate'] = ''
            return redirect(url_for('colleaguedata'))
        
        if 'btCandidate' in request.form:
            selected_candidate = request.form.get('candidate')
            session['selected_candidate'] = selected_candidate
            return redirect(url_for('colleaguedata'))
        
    # Only show client details and contacts if a company is selected
    if selected_company:
        contacts = getContactsByCompany(selected_company)
        contact_names = [contact.get("ContactName") for contact in contacts]

        
    # Only show contact details and requirements once a contact has been selected
    if selected_contact:
        requirements = getC7Requirements(selected_company, selected_contact)
        req_names = [requirement.get("Description") for requirement in requirements]

        try:
            result = Contact.find_by("name", selected_contact)            
            contact_record = {k: result.__getattribute__(k) for k in contact_fields}
        except Exception as e:
            error = str(e)


    # Only show candidates once a requirement has been selected
    if selected_requirement:
        id_part = selected_requirement.split(" - ",1)[0]
        candidates = getC7RequirementCandidates(id_part)
        candidate_names = [candidate.get("Name") for candidate in candidates]

        try:
            req_description = (selected_requirement,"-")[0]
            req_description = req_description.lstrip('0123456789- ')

            result = Requirement.find_by("description", req_description)            
            req_record = {k: result.__getattribute__(k) for k in req_fields}
        except Exception as e:
            error = str(e)


    # Only show candidates once a requirement has been selected
    if selected_candidate:
        candidate_name = selected_candidate

        try:
            result = Candidate.find_by("candidateName", candidate_name)            
            candidate_record = {k: result.__getattribute__(k) for k in candidate_fields}
        except Exception as e:
            error = str(e)

    contracts = []
    if 'sid' in session:
        contracts = ContractModel.query.filter_by(sid=session['sid']).all()
        if contracts:
            selected_company = contracts[0].companyname
            selected_contact = contracts[0].contactname
            

    return render_template(
        'colleague.html',
        client_names=client_names,
        selected_company=selected_company,
        contact_names=contact_names,
        selected_contact=selected_contact,
        requirements=req_names,
        selected_requirement=selected_requirement,
        candidate_names=candidate_names,
        selected_candidate=selected_candidate,
        ch_record=ch_record,
        ch_no=ch_no,
        ch_fields=ch_fields,
        client_fields=client_fields,
        client_record=client_record,
        contact_record=contact_record,
        contact_fields=contact_fields,
        req_fields=req_fields,
        req_record=req_record,
        candidate_fields=candidate_fields,
        candidate_record=candidate_record,
        contracts=contracts    
        )



@app.route('/servicestandards', methods=['GET', 'POST'])
def set_servicestandards():
    from app.models import ServiceStandard
    standards = ServiceStandard.query.filter_by(sid=session.get('sid')).all()

    if request.method == 'POST':
        ids = request.form.getlist('id')
        ssns = request.form.getlist('ssn')
        descriptions = request.form.getlist('service-description')

        # You can zip and process them here:
        standards = list(zip(ids, ssns, descriptions))

        # Example: print or save them
        for id_, ssn, desc in standards:
            if id_:
                rawDesc = desc.strip().strip('"')
                record = ServiceStandard.query.get(int(id_))                
                if record:
                    record.ssn = ssn.strip()
                    record.description = rawDesc
            else:   
                if ssn.strip() or desc.strip():
                    db.session.add(ServiceStandard(ssn=ssn.strip(), description=rawDesc))
        
        db.session.commit()
        return redirect(url_for('set_servicestandards'))
    

    return render_template('standards.html', standards=standards)


@app.route('/delete/<int:id>', methods=['POST'])
def delete_standard(id):
    standard = ServiceStandard.query.get_or_404(id)
    db.session.delete(standard)
    db.session.commit()
    return redirect(url_for('set_servicestandards'))


@app.route('/servicearrangements', methods=['GET', 'POST'])
def manage_servicearrangements():
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    if request.method == 'POST':
        for day in days:
            row = ServiceArrangement.query.filter_by(day=day).first()
            if not row:
                row = ServiceArrangement(day=day)
                db.session.add(row)

            row.defaultserviceperiod = request.form.get(f'{day}_default', '')
            row.atservicebase = request.form.get(f'{day}_base', '')
            row.atclientlocation = request.form.get(f'{day}_client', '')
            row.atotherlocation = request.form.get(f'{day}_other', '')

        db.session.commit()
        return redirect(url_for('manage_servicearrangements'))

    arrangements = {row.day: row for row in ServiceArrangement.query.all()}
    return render_template('arrangements.html', arrangements=arrangements)


@app.route('/preparecontract')
def prepare_contract():
    return 'Prepare merge template here'

