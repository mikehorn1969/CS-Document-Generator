# c7query.py - Colleague 7 API queries

import requests, string
from app.classes import Company, Contact, Config, Requirement, Candidate
from app.helper import loadConfig
import re
from datetime import datetime
from chquery import searchCH, getCHRecord

def getC7Company(company_id):
    
    if Config.find_by_name("C7 Key") is None:
        loadConfig()

    subscription_key = Config.find_by_name("C7 Key")
    user_id = Config.find_by_name("C7 Userid")

    try:

        url = f"https://coll7openapi.azure-api.net/api/Company/Get?UserId={user_id}&CompanyId={company_id}&IncludeArchivedRecords=false"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'Ocp-Apim-Subscription-Key': subscription_key,
        }

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

    except Exception as e:
        print(e)


def getC7Contact(contact_id):

    if Config.find_by_name("C7 Key") is None:
        loadConfig()

    subscription_key = Config.find_by_name("C7 Key")
    user_id = Config.find_by_name("C7 Userid")

    try:

        url = f"https://coll7openapi.azure-api.net/api/Contact/Get?UserId={user_id}&ContactId={contact_id}&IncludeArchivedRecords=false"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'Ocp-Apim-Subscription-Key': subscription_key,
        }

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

    except Exception as e:
        print(e)


def getC7Contacts():
     
    if Config.find_by_name("C7 Key") is None:
        loadConfig()

    subscription_key = Config.find_by_name("C7 Key")
    user_id = Config.find_by_name("C7 Userid")

    try:       
        url = f"https://coll7openapi.azure-api.net/api/Contact/AdvancedSearch"

        # Request headers
        hdr ={
        'Cache-Control': 'no-cache',
        'Ocp-Apim-Subscription-Key': subscription_key,
        }
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

    except Exception as e:
        return e
    

def getC7Clients():
    
    if Config.find_by_name("C7 Key") is None:
        loadConfig()

    subscription_key = Config.find_by_name("C7 Key")
    user_id = Config.find_by_name("C7 Userid")

    try:       
        url = f"https://coll7openapi.azure-api.net/api/Company/AdvancedSearch"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'Ocp-Apim-Subscription-Key': subscription_key,
        }
        body ={
            "userId": user_id,
            "allColumns": False,
            "columns": ["CompanyId", "CompanyName", "AddressLine1", "AddressLine2", "AddressLine3", 
                        "City", "Postcode", "telephoneNumber", "companyEmail", "registrationNumber"],
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
        # companyname, name, address, emailaddress, phone, title    
        companies = []
        for item in response_json:
            AddressLine1 = item.get("AddressLine1", "")
            AddressLine2 = item.get("AddressLine2", "")
            AddressLine3 = item.get("AddressLine3", "")
            City = item.get("City", "")
            CompanyEmail = item.get("CompanyEmail", "")
            CompanyId = item.get("CompanyId", "")
            CompanyName = item.get("CompanyName", "")
            Postcode = item.get("Postcode", "")
            RegistrationNumber = item.get("RegistrationNumber", "")
            TelephoneNumber = item.get("TelephoneNumber", "")
        
            RawAddress = (AddressLine1 or "") + ", " + (AddressLine2 or "") + ", " + (AddressLine3 or "") + ", " + (City or "") + ", " + (Postcode or "")
            CompanyAddress = re.sub(r',+', ',', RawAddress)    # strip extra commas where an address field was empty
                
            # create a new Company instance
            new_contact = Company(CompanyName, CompanyAddress, CompanyEmail, TelephoneNumber, RegistrationNumber)

            companies.append({
                "CompanyId": CompanyId,
                "CompanyName": CompanyName,
                "CompanyAddress": CompanyAddress,
                "CompanyEmail": CompanyEmail,                
                "CompanyPhone": TelephoneNumber,
                "CompanyNumber": RegistrationNumber
            })

        return companies

    except Exception as e:
        return e
    

def getContactsByCompany(CompanyName):

    if Config.find_by_name("C7 Key") is None:
        loadConfig()

    subscription_key = Config.find_by_name("C7 Key")
    user_id = Config.find_by_name("C7 Userid")

    try:       
        url = f"https://coll7openapi.azure-api.net/api/Contact/AdvancedSearch"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'Ocp-Apim-Subscription-Key': subscription_key,
        }
        body ={
            "userId": user_id,
            "allColumns": False,
            "columns": ["ContactId", "CompanyName", "Forenames", "Surname", "AddressLine1", "AddressLine2", "AddressLine3", 
                        "City", "Postcode", "EmailAddress", "TelephoneNumber", "Title"],
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

    except Exception as e:
        return e

def getC7Requirements(company_name,contact_name):

    if Config.find_by_name("C7 Key") is None:
        loadConfig()

    subscription_key = Config.find_by_name("C7 Key")
    user_id = Config.find_by_name("C7 Userid")
    notStatus = "Dead"

    try:               
        url = f"https://coll7openapi.azure-api.net/api/Requirement/Search?UserId={user_id}&CompanyName={company_name}&ContactName={contact_name}"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'Ocp-Apim-Subscription-Key': subscription_key,
        }
        
        response = requests.get(url, headers=hdr)
        response_json = response.json()

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
    
    if Config.find_by_name("C7 Key") is None:
        loadConfig()
        
    subscription_key = Config.find_by_name("C7 Key")
    user_id = Config.find_by_name("C7 Userid")

    try:       
        url = f"https://coll7openapi.azure-api.net/api/Requirement/GetRequirementCandidates?UserId={user_id}&RequirementId={requirementId}"

        hdr ={
        # Request headers
        'Cache-Control': 'no-cache',
        'Ocp-Apim-Subscription-Key': subscription_key,
        }
 
        response = requests.get(url, headers=hdr)

        # Read and decode response
        response_json = response.json()

        # Extract desired fields
        candidates = []
        for item in response_json:
            CandidateId = item.get("CandidateId", "")
            Name = str(item.get("Name", ""))
            #Name = Name.split(":")[0]
            
            # create a new Company instance
            new_candidate = Candidate(CandidateId, Name)

            candidates.append({
                "CandidateId": CandidateId,
                "Name": Name
            })

        return candidates

    except Exception as e:
        return e


def searchC7Candidate(surname):
    
    # Tech debt: create a fixture for all this
    if Config.find_by_name("C7 Key") is None:
        loadConfig()

    subscription_key = Config.find_by_name("C7 Key")
    user_id = Config.find_by_name("C7 Userid")
    headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Cache-Control': 'no-cache'
        }
    C7_surname = surname.strip()
    candidate_search_url = f"https://coll7openapi.azure-api.net/api/Candidate/Search?UserId={user_id}&Surname={C7_surname}"
    found_candidate = requests.get(candidate_search_url, headers=headers)
    
    if found_candidate.status_code == 200:
        candidate_json = found_candidate.json()
        candidate_id = candidate_json[0]
        candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Get?UserId={user_id}&CandidateId={candidate_id}"
        candidate_response = requests.get(candidate_url, headers=headers)

        candidate_record = candidate_response.json()
        surname_and_sid = candidate_record.get('Surname').split(":",1)
        surname = surname_and_sid[0].strip()        
        sid = surname_and_sid[1].strip() if len(surname_and_sid) > 1 else None

    return(surname,sid)    


def getC7candidate(service_id, surname):
    
    job_title = None
    company_name = None
    company_address = None
    company_email = None
    company_phone = None    
    company_number = None
    contact_name = None
    contact_address = None
    contact_email = None
    contact_phone = None
    contact_title = None
    job_title = None
    f_start_date = None 
    f_end_date = None
    notice_period = None
    notice_period_unit = None
    fees = None
    charges = None
    candidate_id = None
    candidate_name = None
    description = None
    companyId = None
    contactId = None
    requirement_id = None
    experience_placement_id = None                                

    if Config.find_by_name("C7 Key") is None:
        loadConfig()

    subscription_key = Config.find_by_name("C7 Key")
    user_id = Config.find_by_name("C7 Userid")

    try:
        SEARCH_TERM = service_id.upper() if service_id else surname.strip()
        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Cache-Control': 'no-cache'
        }

        # no wildcard search in C7, so we have to search by letter unless a (partial) surname is provided
        # this will search for all candidates with surnames starting with each letter of the alphabet
        if surname:
            target = surname.strip()
        else:
            target = string.ascii_uppercase

        for letter in target:
            # Use surname here if it's available, much quicker!
            if ( surname and target == surname.strip() ):
                candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Search?UserId={user_id}&Surname={target}"    
            else:
                candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Search?UserId={user_id}&Surname={letter}"
            candidate_search_response = requests.get(candidate_url, headers=headers)
            
            # move on to next letter if no results returned
            if candidate_search_response.status_code != 200:
                continue
            
            search_results = candidate_search_response.json()
            
            for candidate in search_results:

                candidate_id = candidate
                candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Get?UserId={user_id}&CandidateId={candidate_id}"
                candidate_response = requests.get(candidate_url, headers=headers)
                
                # move on to next candidate if no record found - very unlikely?
                if candidate_response.status_code != 200:
                    continue
                
                candidate_data = candidate_response.json()

                # SEARCH_TERM is either SID or SP surname, both should be in the candidate surname field for an active placement, so either will match
                # move on to next candidate if no match
                if SEARCH_TERM not in candidate_data.get('Surname', ''):
                    continue

                candidate_name = f"{candidate_data.get('Forenames', '')} {candidate_data.get('Surname', '')}"
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
                candidate_reg_number = candidate_reg_number.strip()
                candidate_ltd_name = candidate_ltd_name.strip()

                # serch Companies House API using name and company number
                # populate registered address when a match is found
                ch_result = searchCH(candidate_ltd_name)

                for key, value in ch_result.items():
                    if key == "items":
                        for item in value:
                            if (
                                item.get('title') == candidate_ltd_name.upper() and
                                item.get('company_number') == candidate_reg_number
                            ):
                                candidate_address = item.get('address_snippet')

                # Use company number to get jurisdiction from CH record
                company_record = getCHRecord(candidate_reg_number)

                for key, value in company_record.items():
                    if key == "jurisdiction":
                        candidate_jurisdiction = value

                # Get candidate experience   
                experience_url = f"https://coll7openapi.azure-api.net/api/Candidate/GetExperience?UserId={user_id}&CandidateId={candidate_id}"
                candidate_experience = requests.get(experience_url, headers=headers)
                
                # move on to the next experience if no result - unlikely ?
                if candidate_experience.status_code != 200:
                    continue
                
                experience_results = candidate_experience.json()
                
                # loop through candidate experience records
                for experience in experience_results:
                    
                    experience_placement_id = experience.get('placementId', 0)                    
                    
                    # 0 = none CS placement, skip these
                    if experience_placement_id == 0:
                        continue
                    
                    job_title = experience.get('placementJobTitle', '')
                    company_name = experience.get('placementCompanyName', '')

                    # find requirements that match company & job title
                    requirement_url = f"https://coll7openapi.azure-api.net/api/Requirement/Search?UserId={user_id}&CompanyName={company_name}&JobTitle={job_title}"
                    requirements = requests.get(requirement_url, headers=headers)
                    
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
                            company_response = requests.get(company_url, headers=headers)
                        
                            if company_response.status_code == 200:
                                company_data = company_response.json()                                
                                RawAddress = (company_data.get("AddressLine1") or "") + ", " + (company_data.get("AddressLine2") or "") + ", " + (company_data.get("AddressLine3") or "") + ", " + (company_data.get("City") or "") + ", " + (company_data.get("Postcode") or "")
                                # Clean up: remove repeated commas and any surrounding whitespace
                                company_address = re.sub(r'\s*,\s*(?=,|$)', '', RawAddress)  # remove empty elements
                                company_address = re.sub(r',+', ',', company_address)       # collapse multiple commas into one
                                company_address = company_address.strip(', ').strip()       # final tidy-up
                                company_email = company_data.get("CompanyEmail", "")
                                company_phone = company_data.get("TelephoneNumber", "") 
                                company_number = company_data.get("RegistrationNumber", "")
                                
                            # get company contact data
                            contactId = requirement.get('contactId', '')
                            contact_url = f"https://coll7openapi.azure-api.net/api/Contact/Get?UserId={user_id}&ContactId={contactId}"
                            contact_response = requests.get(contact_url, headers=headers)
                            
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
                return {
                    "candidateaddress": candidate_address,
                    "candidatephone": candidate_phone,
                    "candidateemail": candidate_email,   
                    "candidateltdregno": candidate_reg_number,
                    "candidateltdname": candidate_ltd_name,
                    "candidatesurname": candidate_surname,
                    "sid": service_id,
                    "servicename": job_title,
                    "companyname": company_name,
                    "companyaddress": company_address,
                    "companyemail": company_email,
                    "companyphone": company_phone,    
                    "companynumber": company_number,
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
                    "candidateid": candidate_id,
                    "candidatename": candidate_name,
                    "candidatejurisdiction": candidate_jurisdiction,
                    "description": description,
                    "companyid": companyId,
                    "contactid": contactId,
                    "requirementid": requirement_id,
                    "placementid": experience_placement_id                                
                }
        return None

    except Exception as e:
        return {"error": str(e)}

