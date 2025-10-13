# test_c7query.py

import pytest
from app.c7query import loadConfig, loadC7ContactData, loadC7ClientInformation, getC7ContactsByCompany, getC7RequirementCandidates, getC7contract




def test_loadConfig():
    
    result = loadConfig() 

    assert(result == "C7 Config Loaded"), "loadConfig failed"


def test_getC7Contacts():

    result = loadC7ContactData()
    
    assert result != [], "No contacts returned"



def test_getC7Clients():

    result = loadC7ClientInformation()
  
    assert result != [], "No companies returned"



def test_getContactsByCompany():

    company_name = "Bellrock Property and Facilities Management"
    result = getC7ContactsByCompany(company_name)

    assert result != [], "No contacts returned"



def test_getC7RequirementCandidates():

    requirementId = 260
    result = getC7RequirementCandidates(requirementId)
    
    assert result != [], "No candidates returned"


def test_getC7Candidate():

    service_id = "BRG003"

    result = getC7contract(service_id)
                        
    assert result != [], "No candidate returned"
    
    print(result)

if __name__ == '__main__':
    test_getC7Candidate()