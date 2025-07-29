from app import app, db
from flask import Flask, render_template, request, redirect, url_for, session
from app.models import ServiceStandard, ServiceArrangement, ServiceContract as ContractModel
from app.c7query import getC7Clients, getContactsByCompany, getC7Requirements, getC7RequirementCandidates, getC7candidate
from app.chquery import getCHRecord
from app.classes import Company, Contact, Requirement, Candidate
from datetime import datetime
from dateutil.relativedelta import relativedelta


@app.route('/', methods=["GET", "POST"])
def index():
    return render_template('index.html', sid=session.get('sid', '').upper())


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
        else:
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
            contract['jobtitle'] = c7contractdata.get("jobTitle", "")
            
            contract['companyname'] = c7contractdata.get("companyName", "")
            
            
            contract['fees'] = c7contractdata.get("fees", 0.0)
            contract['feecurrency'] = c7contractdata.get("feecurrency", "GBP")
            contract['charges'] = c7contractdata.get("charges", 0.0)
            contract['chargecurrency'] = c7contractdata.get("chargecurrency", "GBP")
            contract['requirementid'] = c7contractdata.get("requirementId", 0)
            contract['candidateid'] = c7contractdata.get("candidateId", 0)
            contract['placementid'] = c7contractdata.get("placementId", 0)
            contract['candidatename'] = c7contractdata.get("candidateName", "")
            contract['candidateaddress'] = c7contractdata.get("candidateAddress", "")
            contract['candidateemail'] = c7contractdata.get("candidateEmail", "")
            contract['candidatephone'] = c7contractdata.get("candidatePhone", "")
            contract['candidateltdname'] = c7contractdata.get("candidateLtdName", "")
            contract['candidateltdregno'] = c7contractdata.get("candidateLtdRegno", "")
            contract['description'] = c7contractdata.get("description", "")
            contract['companyid'] = c7contractdata.get("companyId", 0)
            contract['contactid'] = c7contractdata.get("contactId", 0)  

            contract['noticeperiod'] = 4 # Default to 4 weeks, can be changed later
            contract['noticeperiodunit'] = "weeks"  # Default to weeks, can be changed later

            start_date = c7contractdata.get("startDate", "")
            end_date = c7contractdata.get("endDate", "")

            if start_date and end_date:
            
                dt_start_date = datetime.strptime(start_date + "000", "%Y-%m-%d %H:%M:%S.%f").date()
                dt_end_date = datetime.strptime(end_date + "000", "%Y-%m-%d %H:%M:%S.%f").date()

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

