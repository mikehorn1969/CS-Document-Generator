# test_c7query.py

import pytest
from app.c7query import loadConfig, getC7Contacts, getC7Clients, getContactsByCompany, getC7RequirementCandidates, getC7candidate




def test_loadConfig():
    
    result = loadConfig() 

    assert(result == "C7 Config Loaded"), "loadConfig failed"


def test_getC7Contacts():

    result = getC7Contacts()
    
    assert result != [], "No contacts returned"



def test_getC7Clients():

    result = getC7Clients()
  
    assert result != [], "No companies returned"



def test_getContactsByCompany():

    company_name = "Bellrock Property and Facilities Management"
    result = getContactsByCompany(company_name)

    assert result != [], "No contacts returned"



def test_getC7RequirementCandidates():

    requirementId = 260
    result = getC7RequirementCandidates(requirementId)
    
    assert result != [], "No candidates returned"


def test_getC7Candidate():

    service_id = "BRG003"

    result = getC7candidate(service_id)
                        
    assert result != [], "No candidate returned"
    
    print(result)

if __name__ == '__main__':
    test_getC7Candidate()