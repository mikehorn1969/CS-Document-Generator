# c7query.py - Colleague 7 API queries

import requests, string
from app.classes import Company, Contact, Config, Requirement, Candidate
from app.helper import loadConfig
import re
from flask import session 


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


def getC7candidate(service_id):
    if Config.find_by_name("C7 Key") is None:
        loadConfig()

    subscription_key = Config.find_by_name("C7 Key")
    user_id = Config.find_by_name("C7 Userid")

    try:
        SEARCH_TERM = service_id.lower()
        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key,
            'Cache-Control': 'no-cache'
        }

        # no wildcard search in C7, so we have to search by letter
        # this will search for all candidates with surnames starting with each letter of the alphabet
        for letter in string.ascii_uppercase:
            
            candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Search?UserId={user_id}&Surname={letter}"
            candidate_search_response = requests.get(candidate_url, headers=headers)
            
            if candidate_search_response.status_code != 200:
                continue
            
            search_results = candidate_search_response.json()
            
            for candidate in search_results:

                candidate_id = candidate
                candidate_url = f"https://coll7openapi.azure-api.net/api/Candidate/Get?UserId={user_id}&CandidateId={candidate_id}"
                candidate_response = requests.get(candidate_url, headers=headers)
                if candidate_response.status_code != 200:
                    continue
                
                candidate_data = candidate_response.json()
                if SEARCH_TERM not in candidate_data.get('Surname', '').lower():
                    continue

                candidate_name = f"{candidate_data.get('Forenames', '')} {candidate_data.get('Surname', '')}"
                AddressLine1 = candidate_data.get("AddressLine1", "")
                AddressLine2 = candidate_data.get("AddressLine2", "")
                Addressline3 = candidate_data.get("AddressLine3", "")
                City = candidate_data.get("City", "")
                Postcode = candidate_data.get("Postcode", "")
                RawAddress = (AddressLine1 or "") + ", " + (AddressLine2 or "") + ", " + (Addressline3 or "") + ", " + (City or "") + ", " + (Postcode or "")            
                # Clean up: remove repeated commas and any surrounding whitespace
                candidate_address = re.sub(r'\s*,\s*(?=,|$)', '', RawAddress)  # remove empty elements
                candidate_address = re.sub(r',+', ',', candidate_address)      # collapse multiple commas into one
                candidate_address = candidate_address.strip(', ').strip()      # final tidy-up

                # Find the value for CompanyRegistrationNumber
                candidate_reg_number = next(
                    (field["Value"] for field in candidate_data["CustomFields"] if field["Name"] == "CompanyRegistrationNumber"),
                        None
                    )
                candidate_ltd_name = next(
                    (field["Value"] for field in candidate_data["CustomFields"] if field["Name"] == "NameOfLimitedCompany"),
                        None
                    )
                
                # Get candidate experience   
                experience_url = f"https://coll7openapi.azure-api.net/api/Candidate/GetExperience?UserId={user_id}&CandidateId={candidate_id}"
                candidate_experience = requests.get(experience_url, headers=headers)
                
                if candidate_experience.status_code != 200:
                    continue
                
                experience_results = candidate_experience.json()
                
                for experience in experience_results:
                    
                    experience_placement_id = experience.get('placementId', 0)                    
                    
                    if experience_placement_id == 0:
                        continue
                    
                    job_title = experience.get('placementJobTitle', '')
                    company_name = experience.get('placementCompanyName', '')

                    # debugging
                    #if "bellrock" not in company_name.lower():
                    #    continue    
                    
                    requirement_url = f"https://coll7openapi.azure-api.net/api/Requirement/Search?UserId={user_id}&CompanyName={company_name}&JobTitle={job_title}"
                    requirements = requests.get(requirement_url, headers=headers)
                    
                    if requirements.status_code != 200:
                        continue
                    
                    requirement_result = requirements.json()                    
                    
                    for requirement in requirement_result:
                        
                        requirment_placement_id = requirement.get('MostRecentPlacementId', 0)
                        
                        if requirment_placement_id == experience_placement_id:
                        
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
                                contactId = requirement.get('contactId', '')
                                contact_url = f"https://coll7openapi.azure-api.net/api/Contact/Get?UserId={user_id}&ContactId={contactId}"
                                contact_response = requests.get(contact_url, headers=headers)
                            
                            if contact_response.status_code == 200:
                                contact_data = contact_response.json()
                                                            
                            # Return as JSON
                            return {
                                "serviceId": session.get('sid', ''),
                                "serviceName": requirement.get('JobTitleAndDescription', ''),
                                "companyName": company_name,
                                "companyAddress": company_address,
                                "companyEmail": company_data.get("CompanyEmail", ""),
                                "companyPhone": company_data.get("TelephoneNumber", ""),    
                                "companyNumber": company_data.get("RegistrationNumber", ""),
                                "contactName": (contact_data.get("FullName") or ""),
                                "contactAddress": (contact_data.get("Address") or ""),
                                "contactEmail": contact_data.get("EmailAddress", ""),
                                "contactPhone": contact_data.get("ContactNumber", ""),
                                "contactTitle": contact_data.get("JobTitle", ""),
                                "jobTitle": job_title,
                                "startDate": experience.get('placementStartDate', ''),
                                "endDate": experience.get('placementEndDate', ''), 
                                "companyName": company_data.get('CompanyName', ''),
                                "noticePeriod": experience.get('noticePeriod', 0),
                                "noticePeriodUnit": experience.get('noticePeriodUOM', ''),
                                "fees": experience.get('placementPayRate', 0.0),
                                "feeCurrency": 'GBP',
                                "charges": experience.get('placementChargeRate', 0.0),
                                "chargeCurrency": 'GBP',  
                                "candidateId": candidate_id,
                                "candidateName": candidate_name,
                                "description": requirement.get('JobTitleAndDescription', ''),
                                "companyId": companyId,
                                "contactId": contactId,
                                "requirementId": requirement.get('requirementId', 0),
                                "placementId": experience_placement_id,                                
                                "candidateAddress": candidate_address,
                                "candidatePhone": candidate_data.get('MobileNumber', ''),
                                "candidateEmail": candidate_data.get('EmailAddress', ''),   
                                "candidateLtdRegno": candidate_reg_number,
                                "candidateLtdName": candidate_ltd_name 
                            }
        return None

    except Exception as e:
        return {"error": str(e)}

