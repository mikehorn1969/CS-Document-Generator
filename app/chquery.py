import requests
from app.classes import Config
from app.helper import loadConfig

def getCHRecord(companyNo):

    if Config.find_by_name("CH Key") is None:
        loadConfig()
        
    subscription_key = Config.find_by_name("CH Key")

    if not subscription_key:
        raise ValueError("API key not found in config file.")

    url = f"https://api.companieshouse.gov.uk/company/{companyNo}"
  
    response = requests.get(url, auth=(subscription_key,""))

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")


def searchCH(companyName):

    if Config.find_by_name("CH Key") is None:
        loadConfig()
        
    subscription_key = Config.find_by_name("CH Key")

    if not subscription_key:
        raise ValueError("API key not found in config file.")

    url = f"https://api.company-information.service.gov.uk/search/companies?q={companyName}"

    response = requests.get(url, auth=(subscription_key,""))

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")
    

def validateCH(ch_number, ch_name, director ):

    if Config.find_by_name("CH Key") is None:
        loadConfig()
        
    subscription_key = Config.find_by_name("CH Key")

    if not subscription_key:
        raise ValueError("API key not found in config file.")

    reg_number = ch_number.strip()
    ltd_name = ch_name.strip()
    is_valid = False
    is_Director = False
    search_director = director.upper()
    
    # serch Companies House API using name and company number
    # populate registered address when a match is found
    ch_result = searchCH(ltd_name)

    for key, value in ch_result.items():
        if key == "items":
            for item in value:
                if (
                    item.get('title') == ltd_name.upper() and
                    item.get('company_number') == reg_number
                ):
                    is_valid = True
                    reg_address = item.get('address_snippet')

    # Use company number to get full CH record
    company_record = getCHRecord(reg_number)

    #	Company is ‘active’     
    
    for key, value in company_record.items():
        if key == "jurisdiction":
            jurisdiction = value
        if key == "company_status":
            company_status = value
        
    
    #	Confirm that the person in question is a Director 
    
    officers_url = f"https://api.companieshouse.gov.uk/company/{ch_number}/officers"
    officers = requests.get(officers_url, auth=(subscription_key,""))
    officers_json = officers.json()

    for item in officers_json.get("items", []):
        if item.get("resigned_on"):
            continue
        if item.get("officer_role") == "director":
            # CH names look like "SURNAME, FORENAMES"
            raw = item.get("name", "").strip().upper()
            try:
                surname, forenames = [p.strip() for p in raw.split(",", 1)]
                forename = forenames.split()[0]
                found_officer = f"{forename} {surname}"
            except ValueError:
                continue  # name in unexpected format; skip
            if found_officer == search_director:
                officer_name = found_officer
                is_Director = True
                break

    #	Review any warning notices eg. late filing     
    
    #warnings_url = f"https://api.companieshouse.gov.uk/company/{companyNo}/filing-history"
    #warnings = requests.get(warnings_url, auth=(subscription_key,""))

    return {"Valid": is_valid,
            "CompanyNumber": reg_number,
            "Is Director": is_Director,
            "Director": director,
            "Jurisdiction": jurisdiction,
            "Status": company_status


    }


if __name__ == '__main__':

    company_number = "08320269"   
    company_name = "CHANGE SPECIALISTS LTD"

    result = validateCH(company_number, company_name, "John Dean")
    
    for key, value in result.items():        
        print(key, ":", value)
        