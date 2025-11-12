import json
import os, sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from app.chquery import getCHRecord, validateCH

def test_getCHRecord():

    companyNo = "03075427"
        
    company_data = getCHRecord(companyNo)

    assert company_data.get("company_name") == "BELLROCK PROPERTY & FACILITIES MANAGEMENT LIMITED", "Incorrect company name returned"

def test_validateCH():

    """ companyNo = "13246947"
    ch_name = "MBOROGA HORN CONSULTING LTD"
    director = "MICHAEL HORN" """

    companyNo = "SC855314"
    ch_name = "AMBETH CONSULTING LIMITED"
    director = "CAMERON MCEACHRAN"

    # validateCH(ch_number: str, ch_name: str, director: Optional[str] = None) -> Dict[str, Any]: 
    result = validateCH(companyNo, ch_name, director)

    print(result)

    assert result.get("Valid") == True, "Company validation failed when it should have passed"

