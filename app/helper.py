import configparser
from app.classes import Config


def loadConfig():

    subscription_key = Config.find_by_name("C7 Key")
    
    if subscription_key is None:
        try:
            # Read from config file
            config = configparser.ConfigParser()
            files_read = config.read("colleague7.cfg")
            
            # Load subscription key from config
            subscription_key = Config("C7 Key",config.get('APIKEYS', 'SUBSCRIPTION_KEY1'))
            user_id = Config("C7 Userid",config.get('APIKEYS', 'C7_USERID'))
            ch_key = Config("CH Key",config.get('APIKEYS', 'CH_KEY'))

        except Exception as e:
            print(e)
            exit(0)

    return("C7 Config Loaded")

def loadAzureKeys():
    
    subscription_key = Config.find_by_name("AZURE_CLIENT_ID")
    
    if subscription_key is None:
        try:
            # Read from config file
            config = configparser.ConfigParser()
            files_read = config.read("colleague7.cfg")
            
            # Load subscription key from config
            AZURE_CLIENT_ID = Config("AZURE_CLIENT_ID",config.get('AZUREKEYS', 'AZURE_CLIENT_ID'))
            AZURE_TENANT_ID = Config("AZURE_TENANT_ID",config.get('AZUREKEYS', 'AZURE_TENANT_ID'))
            AZURE_CLIENT_SECRET = Config("AZURE_CLIENT_SECRET",config.get('AZUREKEYS', 'AZURE_CLIENT_SECRET'))

        except Exception as e:
            print(e)
            exit(0)

    return("Azure Config Loaded")


def formatName(name_string):
    name_part = name_string.split(":")[0].strip()
    name_array = name_part.split(" ")
    surname_posn = len(name_array) - 1
    
    return f"{name_array[0]} {name_array[surname_posn]}"