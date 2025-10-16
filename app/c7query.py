# c7query.py - Colleague 7 API queries

import requests
from app.classes import Company, Contact, Requirement, Candidate, C7User
from app.helper import load_config, formatName, debugMode
import re
from datetime import date, datetime
from app.chquery import searchCH, getCHbasics 
from dateutil.relativedelta import relativedelta 
from typing import Optional, cast


def getC7Company(company_id):
    """
    Fetch company details from C7 by CompanyId. Includes custom fields and formatted address.
    """
    
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} getC7Company: Fetching data for CompanyId {company_id}")
    
    cfg = load_config()
    user_id = cfg["C7_USERID"]
    hdr = cast(dict[str, str], cfg["C7_HDR"])

    request_body = {
        "userId": user_id,
        "allColumns": False,
        "columns": ["CompanyId","CompanyName","CompanyEmail","TelephoneNumber","MSA Signed","Company Registration Number","AddressLine1","AddressLine2","AddressLine3","City","Postcode"],
        "includeArchived": True,
        "parameters": [{
            "fieldName": "CompanyId",
            "fieldValue": company_id
        }]
    }

    url = "https://coll7openapi.azure-api.net/api/Company/AdvancedSearch"

    response = requests.post(url, headers=hdr, json=request_body)
    if response.status_code != 200:
        return {"status_code": response.status_code, "error": response.text}

    # Parse JSON first
    response_json = response.json()
    
    # Check if we got results and take the first one
    if not response_json or len(response_json) == 0:
        return {"error": "No company found with the given ID"}
    
    company_data = response_json[0]  # Take the first result
    
    # Extract and clean up address    
    RawAddress = (company_data.get("AddressLine1") or "") + ", " + (company_data.get("AddressLine2") or "") + ", " + (company_data.get("AddressLine3") or "") + ", " + (company_data.get("City") or "") + ", " + (company_data.get("Postcode") or "")
    # Clean up address by removing empty elements and fixing comma issues
    address_parts = [part.strip() for part in RawAddress.split(',') if part.strip()]
    CompanyAddress = ", ".join(address_parts)
    
    # Add CompanyAddress to the response object
    company_data["CompanyAddress"] = CompanyAddress

    return company_data


def getC7Contact(contact_id):

    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} getC7Contact: Fetching data for ContactId {contact_id}")

    # bail early if no contact_id
    if contact_id == '' or contact_id is None:
        return {}
    
    cfg = load_config()
    user_id = cfg["C7_USERID"]
    hdr = cast(dict[str, str], cfg["C7_HDR"])

    url = f"https://coll7openapi.azure-api.net/api/Contact/Get?UserId={user_id}&ContactId={contact_id}&IncludeArchivedRecords=false"

    response = requests.get(url, headers=hdr)

    # Parse JSON
    response_json = response.json()

    # Extract desired fields
    # companyname, name, address, emailaddress, phone, title

    RawAddress = (response_json.get("AddressLine1") or "") + ", " + (response_json.get("AddressLine2") or "") + ", " + (response_json.get("AddressLine3") or "") + ", " + (response_json.get("City") or "") + ", " + (response_json.get("Postcode") or "")
    # Clean up address by removing empty elements and fixing comma issues
    address_parts = [part.strip() for part in RawAddress.split(',') if part.strip()]
    ContactAddress = ", ".join(address_parts)

    result = {
        "CompanyName": (response_json.get("CompanyName")),
        "ContactName": response_json.get("FullName"),
        "ContactAddress": ContactAddress,
        "ContactEmail": response_json.get("EmailAddress") or "",
        "ContactPhone": response_json.get("TelephoneNumber") or "",
        "ContactTitle": response_json.get("JobTitle") or ""
        }

    return result


def getC7ContactsByCompany(CompanyName):

    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} getC7ContactsByCompany: Searching contacts for CompanyName {CompanyName}")

    cfg = load_config()
    user_id = cfg["C7_USERID"]
    hdr = cast(dict[str, str], cfg["C7_HDR"])

    url = f"https://coll7openapi.azure-api.net/api/Contact/AdvancedSearch"
    body ={
        "userId": user_id,
        "allColumns": False,
        "columns": ["ContactId", "CompanyName", "Forenames", "Surname", "AddressLine1", "AddressLine2", "AddressLine3", 
                    "City", "Postcode", "EmailAddress", "ContactNumber", "JobTitle"],
        "includeArchived": False,
        "parameters": [{
            "fieldName": "CompanyName",
            "fieldValue": CompanyName 
        }]
    }

    response = requests.post(url, headers=hdr , json=body)
    response_json = response.json()

    contacts = []
    for item in response_json:
        ContactId = item.get("ContactId", "")
        CompanyName = item.get("CompanyName", "")
        Forenames = item.get("Forenames", "")
        Surname = item.get("Surname", "")
        AddressLine1 = item.get("AddressLine1", "")
        AddressLine2 = item.get("AddressLine2", "")
        Addressline3 = item.get("AddressLine3", "")
        City = item.get("City", "")
        Postcode = item.get("Postcode", "")
        EmailAddress = item.get("EmailAddress", "")
        TelephoneNumber = item.get("ContactNumber", "")
        JobTitle = item.get("JobTitle", "")

        ContactName = (Forenames or "") + " " + (Surname  or "")
        RawAddress = (AddressLine1 or "") + ", " + (AddressLine2 or "") + ", " + (Addressline3 or "") + ", " + (City or "") + ", " + (Postcode or "")
        
        # Clean up address by removing empty elements and fixing comma issues
        address_parts = [part.strip() for part in RawAddress.split(',') if part.strip()]
        ContactAddress = ", ".join(address_parts)    # strip extra commas where an address field was empty
        new_contact = Contact(CompanyName, ContactName, ContactAddress, EmailAddress, TelephoneNumber, JobTitle)

        contacts.append({
            "ContactId": ContactId,
            "CompanyName": CompanyName,
            "ContactName": ContactName,
            "ContactAddress": ContactAddress,
            "ContactEmail": EmailAddress,
            "ContactPhone": TelephoneNumber,
            "ContactTitle": JobTitle
        })

    return contacts


def getC7Requirements(company_name,contact_name):

    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} getC7Requirements: Searching requirements for CompanyName {company_name} and ContactName {contact_name}")
    
    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cast(dict[str, str], cfg["C7_HDR"])

    try:               
        url = f"https://coll7openapi.azure-api.net/api/Requirement/Search?UserId={user_id}&CompanyName={company_name}&ContactName={contact_name}"
        
        if isinstance(hdr, dict):
            response = requests.get(url, headers=hdr)
            response_json = response.json()
        else:
            response_json = {}
            
        requirements = []
        for item in response_json:

            """ # ignore dead requirements
            if item.get("statusCode") in notStatus:
                continue """

            RequirementId = item.get("requirementId", "")
            CompanyName = item.get("companyName", "")
            ContactName = item.get("contactName", "")
            Description = item.get("entityDescription", "")
            JobTitle = item.get("jobTitle", "")

            myDesc = f"{RequirementId} - {Description}"

            new_requirement = Requirement(RequirementId, CompanyName, ContactName, Description, JobTitle)

            requirements.append({
                "RequirementId": RequirementId,
                "CompanyName": CompanyName,
                "ContactName": ContactName,
                "Description": myDesc,
                "JobTitle": JobTitle
            })

        return requirements

    except Exception as e:
        return e


def getC7RequirementCandidates(requirementId):

    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} getC7RequirementCandidates: Fetching candidates for RequirementId {requirementId}")
    
    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cast(dict[str, str], cfg["C7_HDR"])

    url = f"https://coll7openapi.azure-api.net/api/Requirement/GetRequirementCandidates?UserId={user_id}&RequirementId={requirementId}"

    response = requests.get(url, headers=hdr)

    # Read and decode response
    response_json = response.json()

    # Extract desired fields
    candidates = []
    for item in response_json:
        candidateId = item.get("candidateId", "")
        Name = str(item.get("Name", ""))
        #Name = Name.split(":")[0]
        
        # create a new Company instance
        new_candidate = Candidate(candidateId, Name)

        candidates.append({
            "candidateId": candidateId,
            "Name": Name
        })

    return candidates


def searchC7Candidate(candidate_name):

    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} searchC7Candidate: Searching for candidate {candidate_name}")

    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cast(dict[str, str], cfg["C7_HDR"])

    C7_candidate_name = candidate_name.split(",").strip()
    candidate_search_url = f"https://coll7openapi.azure-api.net/api/Candidate/Search?UserId={user_id}&Surname={C7_candidate_name}"
    found_candidate = requests.get(candidate_search_url, headers=hdr)
    candidate_record = {}

    if found_candidate.status_code == 200:
        candidate_json = found_candidate.json()
        candidate_id = candidate_json[0]
        candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Get?UserId={user_id}&candidateId={candidate_id}"
        candidate_response = requests.get(candidate_url, headers=hdr)

        candidate_record = candidate_response.json()
        
    return(candidate_record)


def getC7contract(candidate_id):
    
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} getC7contract: Fetching contract data for CandidateId {candidate_id}")
    
    # Initialize variables
    candidate_address = ""
    candidate_phone = ""
    candidate_email = "" 
    candidate_reg_number= ""
    candidate_ltd_name= ""
    candidate_surname= ""
    candidate_name= ""
    candidate_jurisdiction= ""
    candidate_reg_address= ""
    service_id= ""
    job_title= ""
    company_name= ""
    company_address= ""
    company_email= ""
    company_phone = ""
    company_number= ""
    company_jurisdiction= ""
    contact_name= ""
    contact_address= ""
    contact_email= ""
    contact_phone= ""
    contact_title= ""
    job_title= ""
    f_start_date= ""
    f_end_date= ""
    notice_period= ""
    notice_period_unit= ""
    fees= ""
    charges= ""
    description= ""
    companyId= ""
    contactId= ""
    requirement_id= ""
    experience_placement_id = ""       
    placedby = ""
    dm_jobtitle = ""
    dm_name = ""
    dm_email = ""
    dm_phone = ""
    company_msa_signed = ""

    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cast(dict[str, str], cfg["C7_HDR"])

    candidate_record = getC7Candidate(candidate_id)

    candidate_phone = candidate_record.get('phone', '')
    candidate_email = candidate_record.get('email', '')
    candidate_reg_number = candidate_record.get('registration_number', '')
    candidate_ltd_name = candidate_record.get('ltd_name', '')   
    candidate_address = candidate_record.get('address', '') 
    candidate_reg_address = candidate_record.get('candidateregaddress', '')
    candidate_jurisdiction = candidate_record.get('jurisdiction', '')   

    candidate_fullname = candidate_record.get('name', '')
    candidate_surname = candidate_fullname.split(",")[0].strip()    
    candidate_forenames = candidate_fullname.split(",")[1].strip()    
    candidate_name = f"{candidate_forenames} {candidate_surname}"
    if len(candidate_surname.split(":")) != 1:
        service_id = candidate_surname.split(":")[1].strip()

    # Get candidate experience
    experience_url = f"https://coll7openapi.azure-api.net/api/Candidate/GetExperience?UserId={user_id}&candidateId={candidate_id}"
    candidate_experience = requests.get(experience_url, headers=hdr)
    
    # move on to the next experience if no result - unlikely ?
    if candidate_experience.status_code == 200:
                        
        experience_results = candidate_experience.json()
        
        # loop through candidate experience records
        for experience in experience_results:
            
            experience_placement_id = experience.get('placementId', 0)                    
            
            # 0 = none CS placement, skip these
            if experience_placement_id == 0:
                continue

            # Start date will be today or in the future, skip anything earlier    
            start_date = datetime.strptime(experience.get('placementStartDate', ''), "%Y-%m-%d %H:%M:%S.%f").date()            
            if start_date < date.today():
                continue

            contactId = experience.get('contactId', 0)

            print(f"DEBUG: Placement ID: {experience_placement_id}")
            print(f"DEBUG: Start Date: {start_date}")
            print(f"DEBUG: Contact ID: {contactId}")
            
            # get company contact data                   
            contact_url = f"https://coll7openapi.azure-api.net/api/Contact/Get?UserId={user_id}&ContactId={contactId}"
            contact_response = requests.get(contact_url, headers=hdr)
            
            if contact_response.status_code == 200:
                contact_data = contact_response.json()
                contact_name = (contact_data.get("FullName") or "")
                contact_address = (contact_data.get("Address") or "")
                contact_email = contact_data.get("EmailAddress", "")
                contact_phone = contact_data.get("ContactNumber", "")
                contact_title = contact_data.get("JobTitle", "")

            job_title = experience.get('placementJobTitle', '')
            company_name = experience.get('placementCompanyName', '')
            placedby = experience.get('placementPlacedBy', '')

            # get company data

            company_search_url = f"https://coll7openapi.azure-api.net/api/Company/Search?UserId={user_id}&CompanyName={company_name}"
            company_result = requests.get(company_search_url, headers=hdr)
            if company_result.status_code == 200:

                companyId = company_result.json()[0]
                company_data = getC7Company(companyId)

                if company_data:                    
                    company_email = company_data.get("CompanyEmail", "")
                    company_phone = company_data.get("TelephoneNumber", "") 
                    company_number = company_data.get("CUSTOM_Company Registration Number", "")  
                    company_msa_signed = company_data.get("CUSTOM_MSA Signed", "") 
                    
                    # serch Companies House API using name and company number (fetch company number from CH if it's missing) 
                    # populate registered address when a match is found
                    if company_number == None:
                        ch_result = searchCH(company_name)
                        # break using flag once key is found
                        foundit = False
                        for key, value in ch_result.items():
                            if key == "items":
                                for item in value:
                                    if ( item.get('title') == company_name.upper() ):
                                        foundit = True
                                        company_number = item.get('company_number')
                                    if foundit:
                                        break
                            if foundit:
                                break

                    company_jurisdiction = ""
                    company_address = ""
                    if (company_name and company_number):
                        company_address, company_jurisdiction = getCHbasics(company_name, company_number)
                        if company_jurisdiction == "england-wales":
                            company_jurisdiction = "England and Wales"
                    else:
                        RawAddress = (company_data.get("AddressLine1") or "") + ", " + (company_data.get("AddressLine2") or "") + ", " + (company_data.get("AddressLine3") or "") + ", " + (company_data.get("City") or "") + ", " + (company_data.get("Postcode") or "")
                        # Clean up: remove repeated commas and any surrounding whitespace
                        company_address = re.sub(r'\s*,\s*(?=,|$)', '', RawAddress)  # remove empty elements
                        company_address = re.sub(r',+', ',', company_address)       # collapse multiple commas into one
                        company_address = company_address.strip(', ').strip()       # final tidy-up
                        company_jurisdiction = "England and Wales"
                                            
            # Ensure placement dates are in YYYY-MM-DD format
            start_date = datetime.strptime(experience.get('placementStartDate', '')[:10], "%Y-%m-%d")
            f_start_date = start_date.strftime("%d/%m/%Y")
            end_date = datetime.strptime(experience.get('placementEndDate', '')[:10], "%Y-%m-%d")
            f_end_date = end_date.strftime("%d/%m/%Y")
            notice_period = experience.get('noticePeriod', 0)
            notice_period_unit = experience.get('noticePeriodUOM', '')
            fees = experience.get('placementPayRate', 0.0)
            charges = experience.get('placementChargeRate', 0.0)
            description = experience.get('jobTitle', '')            
            
            placedbyuser = loadC7Users(placedby)

            if placedbyuser:
                dm_name = placedbyuser.username
                dm_jobtitle = placedbyuser.jobTitle
                dm_email = placedbyuser.emailAddress

            # break out of experience loop once we have processed the relevant placement
            break

        # Return gathered data as JSON  
        # Technical Debt: currencies are hard coded    
        return {
                "candidateaddress": candidate_address,
                "candidatephone": candidate_phone,
                "candidateemail": candidate_email,   
                "candidateltdregno": candidate_reg_number,
                "candidateltdname": candidate_ltd_name,
                "candidateregaddress": candidate_reg_address,
                "candidatesurname": candidate_surname,
                "candidateName": candidate_name,
                "candidatejurisdiction": candidate_jurisdiction,
                "sid": service_id,
                "servicename": job_title,
                "companyname": company_name,
                "companyaddress": company_address,
                "companyemail": company_email,
                "companyphone": company_phone,    
                "companynumber": company_number,
                "companyjurisdiction": company_jurisdiction,
                "contactname": contact_name,
                "contactaddress": contact_address,
                "contactemail": contact_email,
                "contactphone": contact_phone,
                "contacttitle": contact_title,
                "jobtitle": job_title,
                "startdate": f_start_date, 
                "enddate": f_end_date,
                "noticeperiod": notice_period,
                "noticeperiodunit": notice_period_unit,
                "fees": fees,
                "feecurrency": "GBP",
                "charges": charges,
                "chargecurrency": "GBP",  
                "candidateId": candidate_id,                    
                "description": description,
                "companyid": companyId,
                "contactid": contactId,
                "requirementid": requirement_id,
                "placementid": experience_placement_id,
                "dmname": dm_name,
                "dmtitle": dm_jobtitle,
                "dmemail": dm_email,
                "dmphone": dm_phone,
                "companymsasigned": company_msa_signed
            }


def gatherC7data(session_contract):
    
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} gatherC7data: Gathering contract data from C7")

    contract = {}
    c7contractdata = {}

    if session_contract:
        candidate_id = session_contract.get("candidateId", 0)     
        c7contractdata = getC7contract(candidate_id)

    if c7contractdata and isinstance(c7contractdata, dict):                   
        contract['sid'] = c7contractdata.get("sid", "")
        contract['servicename'] = c7contractdata.get("servicename", "")
        contract['companyaddress'] = c7contractdata.get("companyaddress", "")
        contract['companyemail'] = c7contractdata.get("companyemail", "")
        contract['companyphone'] = c7contractdata.get("companyphone", "")
        contract['companyname'] = c7contractdata.get("companyname", "")
        contract['companyregistrationnumber'] = c7contractdata.get("companynumber", "")            
        contract['companyjurisdiction'] = c7contractdata.get("companyjurisdiction","")
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
        contract['candidateId'] = c7contractdata.get("candidateId", 0)
        contract['placementid'] = c7contractdata.get("placementid", 0)
        contract['candidateName'] = formatName(c7contractdata.get("candidateName", ""))
        contract['candidateaddress'] = c7contractdata.get("candidateaddress", "")
        contract['candidateemail'] = c7contractdata.get("candidateemail", "")
        contract['candidatephone'] = c7contractdata.get("candidatephone", "")
        contract['candidateltdname'] = c7contractdata.get("candidateltdname", "")
        contract['candidateltdregno'] = c7contractdata.get("candidateltdregno", "")
        contract['candidatejurisdiction'] = c7contractdata.get("candidatejurisdiction", "")
        contract['candidateregaddress'] = c7contractdata.get("candidateregaddress", "")
        contract['description'] = c7contractdata.get("description", "")
        contract['companyid'] = c7contractdata.get("companyid", 0)
        contract['contactid'] = c7contractdata.get("contactid", 0)  
        contract['noticeperiod'] = 4 # Default to 4 weeks, can be changed later
        contract['noticeperiod_unit'] = "weeks"  # Default to weeks, can be changed later
        contract['dmname'] = c7contractdata.get("dmname", "")
        contract['dmtitle'] = c7contractdata.get("dmtitle", "")
        contract['dmemail'] = c7contractdata.get("dmemail", "")
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

    return contract


def getC7Candidate(candidate_id, search_term: Optional[str] = None) -> dict: 

    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} getC7Candidate: Fetching data for CandidateId {candidate_id} with search term '{search_term}'")


    candidate_name = ""
    candidate_phone = ""
    candidate_email = ""
    candidate_surname = ""
    candidate_reg_number = None
    candidate_ltd_name = None
    candidate_jurisdiction = ""
    candidate_address = ""
    candidate_reg_address = ""
    msa_signed_date = None

    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cast(dict[str, str], cfg["C7_HDR"])

    candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Get?UserId={user_id}&candidateId={candidate_id}"
    candidate_response = requests.get(candidate_url, headers=hdr)

    # move on to next candidate if no record found - very unlikely?
    if candidate_response.status_code != 200:
        return {candidate_response.status_code: candidate_response.text}
        
    candidate_data = candidate_response.json()

    # SEARCH_TERM is optional - if provided, only return data if surname matches
    # it is only passed when searching for a candidate
    if search_term is None or ( search_term.lower() in candidate_data.get('Surname', '').lower() ):

        candidate_name = f"{candidate_data.get('Surname', '')}, {candidate_data.get('Forenames', '')}"
        candidate_phone = candidate_data.get('MobileNumber', '')
        candidate_email = candidate_data.get('EmailAddress', '')
        candidate_surname = candidate_data.get('Surname', '')
        RawAddress = (candidate_data.get("AddressLine1") or "") + ", " + (candidate_data.get("AddressLine2") or "") + ", " + \
                        (candidate_data.get("AddressLine3") or "") + ", " + (candidate_data.get("City") or "") + ", " + \
                        (candidate_data.get("County") or "") + ", " + (candidate_data.get("Postcode") or "")
        # Clean up address by removing empty elements and fixing comma issues
        address_parts = [part.strip() for part in RawAddress.split(',') if part.strip()]
        candidate_address = ", ".join(address_parts)
        
        # Extract custom fields
        for field in candidate_data["CustomFields"]:
            if field["Name"] == "MSA Signed":
                msa_signed_date = field["Value"]
            elif field["Name"] == "CompanyRegistrationNumber":
                candidate_reg_number = field["Value"]
            elif field["Name"] == "NameOfLimitedCompany":
                candidate_ltd_name = field["Value"]
            if msa_signed_date and candidate_reg_number and candidate_ltd_name:
                break

        # for candiate-specific calls, search Companies House API using name and company number
        # populate registered address when a match is found
        if search_term is None and (candidate_ltd_name and candidate_reg_number):
            candidate_reg_address, candidate_jurisdiction = getCHbasics(candidate_ltd_name.strip(), candidate_reg_number.strip())
            if candidate_jurisdiction == "england-wales":
                candidate_jurisdiction = "England and Wales"
            
    return {
        "candidateId": candidate_id,
        "name": candidate_name,
        "phone": candidate_phone,
        "email": candidate_email,
        "address": candidate_address,
        "surname": candidate_surname,
        "registration_number": candidate_reg_number,
        "ltd_name": candidate_ltd_name,
        "candidateregaddress": candidate_reg_address,
        "jurisdiction": candidate_jurisdiction.capitalize(),
        "msasigned": msa_signed_date
    }


def loadC7Users(C7UserId: str) -> C7User | None:
    
    if C7User.count() == 0:

        UserId = ""
        Email = ""
        UserName = ""
        JobTitle = ""
        
        if debugMode():
            print(f"{datetime.now().strftime('%H:%M:%S')} loadC7Users: Fetching all users")
        
        cfg = load_config()
        user_id = cfg["C7_USERID"]
        hdr = cast(dict[str, str], cfg["C7_HDR"])

        url = f"https://coll7openapi.azure-api.net/api/User/Get?UserId={user_id}"
        response = requests.get(url, headers=hdr)

        if response.status_code != 200:
            return None

        response_json = response.json()

        # Extract desired fields
        # userid, email, username & jobtitle
        for item in response_json:
            UserId = item.get("Userid", "")
            Email = item.get("EmailAddress", "")
            UserName = item.get("Username", "")
            JobTitle = item.get("JobTitle", "")

            # create a new User instance
            new_user = C7User(UserId, Email, UserName, JobTitle)

    return C7User.find_by("userid", C7UserId)


def getC7Candidates(query):
    
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} getC7Candidates: Searching candidates with query '{query}'")    
    
    # load config
    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cast(dict[str, str], cfg["C7_HDR"])

    # Build request
    payload = []
    try:
        candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Search?UserId={user_id}&Surname={query}"            
        candidate_search_response = requests.get(candidate_url, headers=hdr)                   
        if candidate_search_response.status_code == 200:
            payload = candidate_search_response.json()
    except:        
        return []
    
    return payload


def loadC7Clients() -> list[Company] | None:
    
    if Company.count() == 0:

        company_id = ""
        company_name = ""
        company_address = ""
        company_email = ""
        company_phone = ""
        company_number = ""
        company_jurisdiction = ""

        if debugMode():
            print(f"{datetime.now().strftime('%H:%M:%S')} loadC7Clients: Fetching all clients")
        
        cfg = load_config()
        user_id = cfg["C7_USERID"]
        hdr = cast(dict[str, str], cfg["C7_HDR"])
        body ={
            "userId": user_id,
            "allColumns": False,
            "columns": ["CompanyName","CompanyID"],
            "includeArchived": False,
            "parameters": [{
                "fieldName": "DateCreated",
                "fieldValue": "1 Jan 2010"
            }]
        }

        url = "https://coll7openapi.azure-api.net/api/Company/AdvancedSearch"
        response = requests.post(url, headers=hdr, json=body)

        if response.status_code != 200:
            return None

        response_json = response.json()

        # Extract desired fields
        # userid, email, username & jobtitle
        for item in response_json:
            company_id = item.get("CompanyID", "")
            company_name = item.get("CompanyName", "")
            company_address = item.get("CompanyAddress", "")
            company_email = item.get("CompanyEmail", "")
            company_phone = item.get("CompanyPhone", "")
            company_number = item.get("CompanyNumber", "")
            company_jurisdiction = item.get("CompanyJurisdiction", "")

            # create a new User instance
            new_client = Company(company_id, company_name, company_address, company_email, company_phone, company_number, company_jurisdiction)

    return Company.get_all_companies()