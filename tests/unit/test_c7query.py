# test_c7query.py

import sys
import os
from datetime import date, datetime
import pytest

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from app.c7query import getC7ContactsByCompany, getC7RequirementCandidates, getC7Company, getC7Candidate, getC7contract  
from app.helper import load_config

def test_loadConfig():
    
    result = load_config()

    assert result != {}, "loadConfig returned empty config"


def test_getContactsByCompany():

    company_name = "Bellrock Property & Facilities Management Limited"
    result = getC7ContactsByCompany(company_name)

    assert result != [], "No contacts returned"



def test_getC7RequirementCandidates():

    requirementId = 260
    result = getC7RequirementCandidates(requirementId)
    
    assert result != [], "No candidates returned"


def test_getC7Candidate():

    service_id = "9233"

    result = getC7Candidate(service_id)
                        
    assert result != [], "No candidate returned"

    assert result.get("registration_number") != None, "No candidate Ltd RegNo returned"
    

def test_getC7Company():

    company_id = 5074

    result = getC7Company(company_id)
    
    assert result.get("CompanyId") == company_id, "Incorrect company returned"

    # MSA signed date might not exist for all companies, so we just check the result is valid
    assert result is not None, "No result returned"
    
def test_getC7Contract():
    

    companyId = 5076
    contactId = 5358
    candidateId = 5905
    placementId = 229
    currentcontract = False
    """ 
    companyId = 5074
    contactId = 5286
    candidateId = 8954
    placementId = 227
    currentcontract = True
    """

    result = getC7contract(candidateId)
    
    assert result.get("placementid") == placementId, "Incorrect placementId returned"
    assert result.get("companyid") == companyId, "Incorrect companyId returned"
    assert result.get("contactid") == contactId, "Incorrect contactId returned"
    assert result.get("candidateId") == candidateId, "Incorrect candidateId returned"

    placementStartDate = result.get("startdate")
    assert placementStartDate is not None, "No start date returned"
    # Convert string date to date object before comparison

    start_date_obj = datetime.strptime(placementStartDate, "%d/%m/%Y").date()
    if not currentcontract:        
        assert start_date_obj > date.today(), "Start date should be greater than today"
    else:
        assert start_date_obj <= date.today(), "Start date should be less than or equal to today"


