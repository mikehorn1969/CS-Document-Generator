from __future__ import annotations
import requests, json
from app.classes import Config
from app.helper import load_config, formatName, debugMode
from typing import Optional, Dict, Any
import os
from datetime import datetime


def getCHRecord(companyNo):
    
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} getCHRecord: Fetching record for CompanyNo {companyNo}")
    
    subscription_key = os.environ.get("CH_KEY", None)
    if not subscription_key:
        cfg = load_config()
        subscription_key = cfg["CH_KEY"]
    
    sCompanyNo = companyNo.strip()
    url = f"https://api.companieshouse.gov.uk/company/{sCompanyNo}"

    if isinstance(subscription_key, dict):
        subscription_key = subscription_key.get("CH_KEY", "")
    response = requests.get(url, auth=(subscription_key, ""))

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")


def searchCH(companyName):

    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} searchCH: Searching for company '{companyName}'")

    subscription_key = os.environ.get("CH_KEY", None)
    if not subscription_key:
        cfg = load_config()
        subscription_key = cfg["CH_KEY"]

    companyName = companyName.strip()
    url = f"https://api.company-information.service.gov.uk/search/companies?q={companyName}"

    if isinstance(subscription_key, dict):
        subscription_key = subscription_key.get("CH_KEY", "")
    response = requests.get(url, auth=(subscription_key, ""))

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")
    

def validateCH(ch_number: str, ch_name: str, director: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate a Companies House entry and (optionally) confirm a director.
    Returns a dict with keys: Valid, Narrative, CompanyNumber, Is Director, Director, Jurisdiction, Status.
    """
    
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} validateCH: Validating company '{ch_name}' with number '{ch_number}' and director '{director}'")
    
    # --- config --------------------------------------------------------------
    subscription_key = os.environ.get("CH_KEY", None)
    nameapi_key = os.environ.get("NAMEAPI_KEY", None)
    if not subscription_key or not nameapi_key:
        cfg = load_config()
        subscription_key = cfg["CH_KEY"]    
        nameapi_key = cfg["NAMEAPI_KEY"]
 
    # --- helpers -------------------------------------------------------------
    def make_result(*, valid: bool, narrative: str = "", is_director: bool = False,
                    jurisdiction: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        return {
            "Valid": valid,
            "Narrative": narrative,
            "CompanyNumber": reg_number,
            "Address": reg_address,
            "Is Director": is_director,
            "Director": director,
            "Jurisdiction": jurisdiction,
            "Status": status,
        }

    def fmt_officer_name(raw: str) -> Optional[str]:
        # CH officer names look like "SURNAME, FORENAMES"
        raw = (raw or "").strip().upper()
        if not raw or "," not in raw:
            return None
        surname, forenames = [p.strip() for p in raw.split(",", 1)]
        if not forenames:
            return None
        first_forename = forenames.split()[0]
        return f"{first_forename} {surname}"


    # --- main code -----------------------------------------------------------
    reg_number = ch_number.strip() if ch_number else ""
    ltd_name_input = ch_name.strip() if ch_name else ""
    ltd_name_upper = ltd_name_input.upper()
    reg_address = ""
    director_input = director.strip().upper() if director else None

    # --- 1) find the company by name + number -------------------------------
    ch_result = searchCH(ltd_name_input)
    items = ch_result.get("items", [])

    match = next(
        (
            item for item in items
            if item.get("title", "").upper() == ltd_name_upper
            and item.get("company_number") == reg_number
        ),
        None,
    )

    if not match:
        return make_result(
            valid=False,
            narrative=(f"Company {ch_name} not found with registered number {ch_number}. Check number. Check spelling of name; is the company filed as LTD or LIMITED?")
        )

    reg_address = match.get("address_snippet")

    # --- 2) pull full record and check status -------------------------------
    company_record = getCHRecord(reg_number)
    jurisdiction = company_record.get("jurisdiction")
    company_status = company_record.get("company_status")

    if company_status != "active":
        return make_result(valid=False, narrative=f"{ch_name} is not Active", jurisdiction=jurisdiction, status=company_status)

    # --- 3) if a director is supplied, verify they are an active director ----

    if director_input:

        search_director = formatName(director_input) 

        officers_url = f"https://api.companieshouse.gov.uk/company/{reg_number}/officers?filter=active"
        resp = requests.get(officers_url, auth=(subscription_key, ""))
        resp.raise_for_status()
        officers_json = resp.json()

        is_director = False
        arr_officers = []
        for item in officers_json.get("items", []):
            if item.get("officer_role") != "director":
                continue
            formatted = fmt_officer_name(item.get("name", ""))
            if formatted is None:
                # name in unexpected format; just skip it
                continue
            arr_officers.append({"string": formatted, "fieldType": "FULLNAME"})

        if arr_officers:
            nameapi_url = f"https://api.nameapi.org/rest/v5.3/matcher/personmatcher?apiKey={nameapi_key}"
            body_dict = {
                "context": {
                    "priority": "REALTIME",
                    "properties": []
                },
                "inputPerson1": {
                    "type": "NaturalInputPerson",
                    "personName": {
                        "nameFields": [
                            {
                                "string": search_director,
                                "fieldType": "FULLNAME"
                            }
                        ]
                    }
                },
                "inputPerson2": {
                    "type": "NaturalInputPerson",
                    "personName": {
                        "nameFields": arr_officers  # <-- should be a list of dicts
                    }
                }
            }
            header_dict = {
                "Content-Type": "application/json"
            }

            nameapi_body = json.dumps(body_dict)
            nameapi_response = requests.post(nameapi_url, data=nameapi_body, headers=header_dict)
            nameapi_response.raise_for_status() 
            nameapi_result = nameapi_response.json()

            is_director = nameapi_result.get("matchType") in "EQUAL,MATCHING,SIMILAR,RELATION" # Tech Debt: may need to remove RELATION ?

        if not is_director:
            return make_result(
                valid=False,
                narrative=f"{search_director} not listed as a director of {ch_name}",
                jurisdiction=jurisdiction,
                status=company_status,
            )

        # found matching active director – fall through to success
        return make_result(valid=True, narrative="", is_director=True, jurisdiction=jurisdiction, status=company_status)

    # --- success (no director check requested) ------------------------------
    return make_result(valid=True, narrative="", is_director=False, jurisdiction=jurisdiction, status=company_status)


def getCHbasics(ltd_name, reg_number):
    """
    returns registered address and jurisdiction 
    """
    
    if debugMode():
        print(f"{datetime.now().strftime('%H:%M:%S')} getCHbasics: Getting basics for company '{ltd_name}' with number '{reg_number}'")
    
    return_address = ""
    return_jurisdiction = ""
    ch_result = searchCH(ltd_name)

    for key, value in ch_result.items():
        if key == "items":
            for item in value:
                if (
                    item.get('title') == ltd_name.upper() and
                    item.get('company_number') == reg_number
                ):
                    return_address = item.get('address_snippet')
                    break

    # Use company number to get jurisdiction from CH record
    company_record = getCHRecord(reg_number)

    # Extract jurisdiction
    found = False
    for key, value in company_record.items():
        if key == "jurisdiction":
            return_jurisdiction = value
            found = True            
        if found:
            break   

    return return_address, return_jurisdiction

