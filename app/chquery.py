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
    

if __name__ == '__main__':

    company_number = 13246947    
    company_name = "Mboroga Horn Consulting Ltd"

    result = getCHRecord(company_number)
    #result = searchCH(company_name)
    
    """ for key, value in result.items():
        if key == "items":
            #print(key, ":", value)
            for item in value:
                if item.get('title') == company_name.upper():
                    print(f"{item.get('title')}, {item.get('company_number')}, {item.get('address_snippet')}") """
            
    for key, value in result.items():
        if key == "jurisdiction":
            print(value)