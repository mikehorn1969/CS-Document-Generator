# test_c7query.py

import pytest
from app.c7query import getC7ContactsByCompany, getC7RequirementCandidates, getC7Company, getC7Candidate 
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
    

if __name__ == '__main__':
    test_getC7Candidate()

def test_getC7Company():

    company_id = 5074

    result = getC7Company(company_id)
    
    assert result.get("CompanyId") == company_id, "Incorrect company returned"

    # MSA signed date might not exist for all companies, so we just check the result is valid
    assert result is not None, "No result returned"
    