from app import app, db
from flask import Flask, render_template, request, redirect, url_for, session
from app.models import ServiceStandard, ServiceArrangement
from app.c7query import getC7Clients, getContactsByCompany, getC7Requirements, getC7RequirementCandidates
from app.chquery import getCHRecord
from app.classes import Company, Contact, Requirement, Candidate

@app.route('/', methods=["GET", "POST"])
def index():
    
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
    candidate_fields = ['candidateId', 'candidateName', 'companyNumber']
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
            return redirect(url_for('index'))

        if 'btContact' in request.form:
            selected_contact = request.form.get('contact')
            session['selected_contact'] = selected_contact
            session['selected_requirement'] = ''
            return redirect(url_for('index'))
        
        if 'btRequirement' in request.form:
            selected_requirement = request.form.get('requirement')
            session['selected_requirement'] = selected_requirement
            session['selected_candidate'] = ''
            return redirect(url_for('index'))
        
        if 'btCandidate' in request.form:
            selected_candidate = request.form.get('candidate')
            session['selected_candidate'] = selected_candidate
            return redirect(url_for('index'))
        
        if 'btCHLookup' in request.form:            
            ch_no = request.form.get('ch_no', '').strip()
            if ch_no:
                try:
                    result = getCHRecord(ch_no)
                    ch_record = {k: result.get(k,'') for k in ch_fields}
                except Exception as e:
                    error = str(e)
            else:
                error = "Please enter a company number."

    # Only show client details and contacts if a company is selected
    if selected_company:
        contacts = getContactsByCompany(selected_company)
        contact_names = [contact.get("ContactName") for contact in contacts]

        try:
            result = Company.find_by("companyname", selected_company)
            client_record = {k: result.__getattribute__(k) for k in client_fields}
        except Exception as e:
            error = str(e)


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


    return render_template(
        'index.html',
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
        candidate_record=candidate_record
    )


@app.route('/c7data')
def capture_c7data():
    return 'c7data'

@app.route('/chdata')
def check_chdata():
    return 'chdata'

@app.route('/servicestandards', methods=['GET', 'POST'])
def set_servicestandards():
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
    
    # Query all rows to view on form
    standards = ServiceStandard.query.all()
    return render_template('main.html', standards=standards)


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




    
