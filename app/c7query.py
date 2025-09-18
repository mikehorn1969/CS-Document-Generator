# c7query.py - Colleague 7 API queries

import requests, string
from app import db
from app.classes import Company, Contact, Config, Requirement, Candidate, C7User
from app.helper import load_config, formatName
import re
from datetime import datetime
from app.chquery import searchCH, getCHbasics 
from dateutil.relativedelta import relativedelta 
from typing import Optional
from sqlalchemy import select
from app.models import ServiceArrangement, ServiceStandard
from flask import Flask, session

def getC7Company(company_id):
    
    cfg = load_config()
    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

    url = f"https://coll7openapi.azure-api.net/api/Company/Get?UserId={user_id}&CompanyId={company_id}&IncludeArchivedRecords=false"

    response = requests.get(url, headers=hdr)

    # Parse JSON
    response_json = response.json()
    
    # Extract desired fields
    # companyname, address
    RawAddress = (response_json.get("AddressLine1") or "") + ", " + (response_json.get("AddressLine2") or "") + ", " + (response_json.get("AddressLine3") or "") + ", " + (response_json.get("City") or "") + ", " + (response_json.get("Postcode") or "")
    CompanyAddress = re.sub(r',+', ',', RawAddress)    # strip extra commas where an address field was empty

    result = {
        "CompanyName": response_json.get("CompanyName"),
        "CompanyAddress": CompanyAddress
    }

    return result



def getC7Contact(contact_id):

    cfg = load_config()
    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

    url = f"https://coll7openapi.azure-api.net/api/Contact/Get?UserId={user_id}&ContactId={contact_id}&IncludeArchivedRecords=false"

    response = requests.get(url, headers=hdr)

    # Parse JSON
    response_json = response.json()

    # Extract desired fields
    # companyname, name, address, emailaddress, phone, title

    ContactName = (response_json.get("forenames") or "") + " " + (response_json.get("surname") or "")
    RawAddress = (response_json.get("AddressLine1") or "") + ", " + (response_json.get("AddressLine2") or "") + ", " + (response_json.get("AddressLine3") or "") + ", " + (response_json.get("City") or "") + ", " + (response_json.get("Postcode") or "")
    ContactAddress = re.sub(r',+', ',', RawAddress)    # strip extra commas where an address field was empty

    result = {
        "CompanyName": (response_json.get("CompanyName")),
        "ContactName": ContactName,
        "ContactAddress": ContactAddress,
        "ContactEmail": response_json.get("EmailAddress") or "",
        "ContactPhone": response_json.get("TelephoneNumber") or "",
        "ContactTitle": response_json.get("Title") or ""
        }

    return result


def loadC7ContactData():
     
    cfg= load_config()
    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"] 
    
    url = f"https://coll7openapi.azure-api.net/api/Contact/AdvancedSearch"

    # Request headers
    hdr = hdr
    body ={
        "userId": user_id,
        "allColumns": False,
        "columns": ["ContactId", "CompanyName", "Forenames", "Surname", "AddressLine1", "AddressLine2", "AddressLine3", 
                    "City", "Postcode", "EmailAddress", "TelephoneNumber", "Title"],
        "includeArchived": False,
        "parameters": [{
            "fieldName": "DateCreated",
            "fieldValue": "1 Jan 2010" 
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
        TelephoneNumber = item.get("TelephoneNumber", "")
        Title = item.get("Title", "")

        ContactName = (Forenames or "") + " " + (Surname  or "")
        RawAddress = (AddressLine1 or "") + ", " + (AddressLine2 or "") + ", " + (Addressline3 or "") + ", " + (City or "") + ", " + (Postcode or "")
        
        ContactAddress = re.sub(r',+', ',', RawAddress)    # strip extra commas where an address field was empty
        new_contact = Contact(CompanyName, ContactName, ContactAddress, EmailAddress, TelephoneNumber, Title)

        contacts.append({
            "ContactId": ContactId,
            "CompanyName": CompanyName,
            "ContactName": ContactName,
            "ContactAddress": ContactAddress,
            "ContactEmail": EmailAddress,
            "ContactPhone": TelephoneNumber,
            "ContactTitle": Title
        })

    return contacts


def loadC7Clients():
    
    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]


    url = f"https://coll7openapi.azure-api.net/api/Company/AdvancedSearch"
    body ={
        "userId": user_id,
        "allColumns": False,
        "columns": ["CompanyId", "CompanyName", "AddressLine1", "AddressLine2", "AddressLine3", 
                    "City", "Postcode", "telephoneNumber", "companyEmail", "registrationNumber",
                    "CompanyRegistrationNumber"],
        "includeArchived": False,
        "parameters": [{
            "fieldName": "DateCreated",
            "fieldValue": "1 Jan 2010" 
        }]
    }

    response = requests.post(url, headers=hdr , json=body)

    # Read and decode response
    response_json = response.json()

    # Extract desired fields
    # companyname, name, address, emailaddress, phone    
    for item in response_json:
        CompanyId = item.get("CompanyId", "")
        AddressLine1 = item.get("AddressLine1", "")
        AddressLine2 = item.get("AddressLine2", "")
        AddressLine3 = item.get("AddressLine3", "")
        City = item.get("City", "")
        CompanyEmail = item.get("CompanyEmail", "")
        CompanyId = item.get("CompanyId", "")
        CompanyName = item.get("CompanyName", "")
        Postcode = item.get("Postcode", "")
        TelephoneNumber = item.get("TelephoneNumber", "")
        RegistrationNumber = item.get("CUSTOM_Company Registration Number", "")
    
        Jurisdiction = ""
        if (CompanyName and RegistrationNumber):
            CompanyAddress, Jurisdiction = getCHbasics(CompanyName, RegistrationNumber)
        else:
            RawAddress = (AddressLine1 or "") + ", " + (AddressLine2 or "") + ", " + (AddressLine3 or "") + ", " + (City or "") + ", " + (Postcode or "")
            CompanyAddress = re.sub(r',+', ',', RawAddress)    # strip extra commas where an address field was empty

        # create a new Company instance
        new_company = Company(CompanyId, CompanyName, CompanyAddress, CompanyEmail, TelephoneNumber, RegistrationNumber, Jurisdiction) 

    return Company.get_all_companies()        
    

def getContactsByCompany(CompanyName):

    cfg = load_config()
    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

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
        
        ContactAddress = re.sub(r',+', ',', RawAddress)    # strip extra commas where an address field was empty
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

    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

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
    
    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

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

    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

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
    
    # Initialize variables
    candidate_address = ""
    candidate_phone = ""
    candidate_email = "" 
    candidate_reg_number= ""
    candidate_ltd_name= ""
    candidate_surname= ""
    candidate_name= ""
    candidate_jurisdiction= ""
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

    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

    candidate_record = getC7Candidate(candidate_id)

    candidate_phone = candidate_record.get('phone', '')
    candidate_email = candidate_record.get('email', '')
    candidate_reg_number = candidate_record.get('registration_number', '')
    candidate_ltd_name = candidate_record.get('ltd_name', '')
    candidate_address = candidate_record.get('address', '')
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
            
            job_title = experience.get('placementJobTitle', '')
            company_name = experience.get('placementCompanyName', '')
            placedby = experience.get('placementPlacedBy', '')
            payload = []

            if C7User.count() == 0:
                payload = loadC7Users()
            else:
                payload = C7User.get_all_users()

            if isinstance(payload,list):
                if len(payload) != 0:
                            
                    foundit = False
                    for user in payload:
                        if user.userid == placedby:
                            dm_jobtitle = user.jobTitle
                            dm_name = user.username
                            dm_email = user.emailAddress
                            foundit = True
                        if foundit:
                            break

            # find requirements that match company & job title
            requirement_url = f"https://coll7openapi.azure-api.net/api/Requirement/Search?UserId={user_id}&CompanyName={company_name}&JobTitle={job_title}"
            requirements = requests.get(requirement_url, headers=hdr)

            # move to next experience if requirement not found
            if requirements.status_code != 200:
                continue
            
            requirement_result = requirements.json()                    
            
            # loop through requirements that match company & job title
            for requirement in requirement_result:
                
                # if the requirement most recent placement ID matches the experience placement id, then we have found our requirement
                if requirement.get('MostRecentPlacementId', 0) == experience_placement_id:
                
                    notice_period = experience.get('noticePeriod', 0)
                    notice_period_unit = experience.get('noticePeriodUOM', '')
                    fees = experience.get('placementPayRate', 0.0)
                    charges = experience.get('placementChargeRate', 0.0)
                    description = requirement.get('JobTitleAndDescription', '')
                    requirement_id = requirement.get('requirementId', 0)

                    # get company data
                    companyId = requirement.get('companyId', '')
                    company_url = f"https://coll7openapi.azure-api.net/api/Company/Get?UserId={user_id}&CompanyId={companyId}"
                    company_response = requests.get(company_url, headers=hdr)

                    if company_response.status_code == 200:
                        company_data = company_response.json()                                
                        
                        company_email = company_data.get("CompanyEmail", "")
                        company_phone = company_data.get("TelephoneNumber", "") 
                        company_number = company_data.get("RegistrationNumber", "")

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
                        else:
                            RawAddress = (company_data.get("AddressLine1") or "") + ", " + (company_data.get("AddressLine2") or "") + ", " + (company_data.get("AddressLine3") or "") + ", " + (company_data.get("City") or "") + ", " + (company_data.get("Postcode") or "")
                            # Clean up: remove repeated commas and any surrounding whitespace
                            company_address = re.sub(r'\s*,\s*(?=,|$)', '', RawAddress)  # remove empty elements
                            company_address = re.sub(r',+', ',', company_address)       # collapse multiple commas into one
                            company_address = company_address.strip(', ').strip()       # final tidy-up
                            company_jurisdiction = "england-wales"
                                                
                    # get company contact data
                    contactId = requirement.get('contactId', '')
                    contact_url = f"https://coll7openapi.azure-api.net/api/Contact/Get?UserId={user_id}&ContactId={contactId}"
                    contact_response = requests.get(contact_url, headers=hdr)
                    
                    if contact_response.status_code == 200:
                        contact_data = contact_response.json()
                        contact_name = (contact_data.get("FullName") or "")
                        contact_address = (contact_data.get("Address") or "")
                        contact_email = contact_data.get("EmailAddress", "")
                        contact_phone = contact_data.get("ContactNumber", "")
                        contact_title = contact_data.get("JobTitle", "")

                    # Ensure placement dates are in YYYY-MM-DD format
                    start_date = datetime.strptime(experience.get('placementStartDate', '')[:10], "%Y-%m-%d")
                    f_start_date = start_date.strftime("%d/%m/%Y")
                    end_date = datetime.strptime(experience.get('placementEndDate', '')[:10], "%Y-%m-%d")
                    f_end_date = end_date.strftime("%d/%m/%Y")
            

        # Return gathered data as JSON  
        # Technical Debt: currencies are hard coded    
        return {
                "candidateaddress": candidate_address,
                "candidatephone": candidate_phone,
                "candidateemail": candidate_email,   
                "candidateltdregno": candidate_reg_number,
                "candidateltdname": candidate_ltd_name,
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
                "dmphone": dm_phone 
            }


def loadCandidates():

    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

    candidate_list = []

    for target in string.ascii_uppercase:

        candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Search?UserId={user_id}&Surname={target}"    

        candidate_search_response = requests.get(candidate_url, headers=hdr)

        search_results = candidate_search_response.json()

        for candidate in search_results:

            candidate_id = candidate
            candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Get?UserId={user_id}&candidateId={candidate_id}"
            candidate_response = requests.get(candidate_url, headers=hdr)

            # move on to next candidate if no record found - very unlikely?
            if candidate_response.status_code != 200:
                continue
            
            candidate_data = candidate_response.json()
            new_row = candidate_data.get("forenames") + " " + candidate_data.get("surname")

            

            candidate_list.append(new_row)
        
    return candidate_list


def gather_data(session_contract):
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


def getC7Candidate(candidate_id, search_term: Optional[str] = None):

    candidate_name = ""
    candidate_phone = ""
    candidate_email = ""
    candidate_surname = ""
    candidate_reg_number = ""
    candidate_ltd_name = ""
    candidate_jurisdiction = ""
    candidate_address = ""

    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

    candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Get?UserId={user_id}&candidateId={candidate_id}"
    candidate_response = requests.get(candidate_url, headers=hdr)

    # move on to next candidate if no record found - very unlikely?
    if candidate_response.status_code == 200:
        
        candidate_data = candidate_response.json()

        # SEARCH_TERM is optional - if provided, only return data if surname matches
        # it is only passed when searching for a candidate
        if search_term is None or ( search_term.lower() in candidate_data.get('Surname', '').lower() ):

            candidate_name = f"{candidate_data.get('Surname', '')}, {candidate_data.get('Forenames', '')}"
            candidate_phone = candidate_data.get('MobileNumber', '')
            candidate_email = candidate_data.get('EmailAddress', '')
            candidate_surname = candidate_data.get('Surname', '')

            # Find the value for CompanyRegistrationNumber
            candidate_reg_number = next(
                (field["Value"] for field in candidate_data["CustomFields"] if field["Name"] == "CompanyRegistrationNumber"),
                    None
                )
            candidate_ltd_name = next(
                (field["Value"] for field in candidate_data["CustomFields"] if field["Name"] == "NameOfLimitedCompany"),
                    None
                )
            
            # serch Companies House API using name and company number
            # populate registered address when a match is found
            if (candidate_ltd_name and candidate_reg_number):
                candidate_address, candidate_jurisdiction = getCHbasics(candidate_ltd_name.strip(), candidate_reg_number.strip())
            else:                    
                candidate_jurisdiction = "england-wales"

    return {
        "candidateId": candidate_id,
        "name": candidate_name,
        "phone": candidate_phone,
        "email": candidate_email,
        "surname": candidate_surname,
        "registration_number": candidate_reg_number,
        "ltd_name": candidate_ltd_name,
        "address": candidate_address,
        "jurisdiction": candidate_jurisdiction
    }


def loadC7Users():
    
    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

    url = f"https://coll7openapi.azure-api.net/api/User/Get?UserId={user_id}"        
    response = requests.get(url, headers=hdr)

    # Read and decode response
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

    return C7User.get_all_users()


def loadServiceStandards(service_id):
        
    if not service_id:                
        return
    
    stmt = select(ServiceStandard).where(ServiceStandard.sid == service_id)
    standards = db.session.execute(stmt).scalars().all()

    # Store SP standards in session for later use
    if service_id != "CS":    
        session['serviceStandards'] = [s.to_dict() for s in standards]

    return standards


def loadServiceArrangements(service_id):
    if not service_id:
        return

    stmt = select(ServiceArrangement).where(ServiceArrangement.sid == service_id)
    arrangements = db.session.execute(stmt).scalars().all()

    # Store arrangements in session for later use
    session['serviceArrangements'] = [a.to_dict() for a in arrangements]

    return arrangements


def getC7Candidates(query):
    
    # load config
    cfg = load_config()

    user_id = cfg["C7_USERID"]
    hdr = cfg["C7_HDR"]

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