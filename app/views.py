from app import app, db
from flask import Flask, render_template, request, redirect, url_for, session
from app.models import ServiceStandard, ServiceArrangement, ServiceContract as ContractModel
from app.c7query import getC7Clients, getContactsByCompany, getC7Requirements, getC7RequirementCandidates, getC7candidate

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
    
    if request.method == "GET":
        # Load existing contract data if available
        contract = {}
        c7contractdata = getC7candidate(session.get('sid', ''))
        if not c7contractdata:
            c7contractdata = {}
        contract['sid'] = c7contractdata.get("serviceId", "").upper()
        contract['servicename'] = c7contractdata.get("serviceName", "")
        contract['companyaddress'] = c7contractdata.get("companyAddress", "")
        contract['companyemail'] = c7contractdata.get("companyEmail", "")
        contract['companyphone'] = c7contractdata.get("companyPhone", "")
        contract['companyregistrationnumber'] = c7contractdata.get("companyNumber", "")
        contract['companyname'] = c7contractdata.get("companyName", "")
        contract['contactname'] = c7contractdata.get("contactName", "")
        contract['contactaddress'] = c7contractdata.get("contactAddress", "")
        contract['contactemail'] = c7contractdata.get("contactEmail", "")
        contract['contactphone'] = c7contractdata.get("contactPhone", "")
        contract['contacttitle'] = c7contractdata.get("contactTitle", "")


    if request.method == "POST":
        if 'btSave' in request.form:
            try:
                # Try to find existing company in DB
                contractdb = ContractModel.query.filter_by(sid=session['sid']).first()
                if not contractdb:
                    # Create new company record
                    contractdb = ContractModel(
                        sid = contract.get("serviceId", "").upper(),
                        servicename = contract.get("servicename", "") )
                    db.session.add(contractdb)
                
                # Update existing record using contract dictionary (no trailing commas!)
                contractdb.companyaddress = contract.get("companyaddress", "")
                contractdb.companyemail = contract.get("companyemail", "")
                contractdb.companyphone = contract.get("companyphone", "")
                contractdb.companyregistrationnumber = contract.get("companyregistrationnumber", "")
                contractdb.companyname = contract.get("companyname", "")
                contractdb.contactname = contract.get("contactname", "")
                contractdb.contactaddress = contract.get("contactaddress", "")
                contractdb.contactemail = contract.get("contactemail", "")
                contractdb.contactphone = contract.get("contactphone", "")
                contractdb.contacttitle = contract.get("contacttitle", "")
                db.session.commit()
            except Exception as e:
                error = str(e)
        
    return render_template(
        'colleague.html', contractdata=contract)
        

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

