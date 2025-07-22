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



if __name__ == '__main__':
    
    company_no = "08320269"

    result = getCHRecord(company_no)
    
    for key, value in result.items():
        print(key, ":", value)