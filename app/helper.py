import configparser
from app.classes import Config
import requests
import io, pandas as pd

import os, io, paramiko
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


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

            nameapi_prefix = config.get('NAMEAPI', 'KEY_PREFIX')            
            nameapi_suffix = config.get('NAMEAPI', 'KEY_SUFFIX')
            nameapi_key = f"{nameapi_prefix}-{nameapi_suffix}"
            Config("NAMEAPI Key",nameapi_key)

            c7hdr = {
                    'Cache-Control': 'no-cache',
                    'Ocp-Apim-Subscription-Key': Config.find_by_name("C7 Key"),
                }
            Config("C7 HDR", c7hdr)

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


def synonymsOf(word):
    """
    Fetch synonyms for names from the Stands4 API.
    """
    api_url = f"https://api.stands4.com/v1/synonyms?word={word}&userid={Config.find_by_name('STANDS4_USERID')}&token={Config.find_by_name('STANDS4_TOKEN')}"
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json().get("synonyms", [])
    else:
        return []
    

def uploadToSharePoint(file_bytes, filename, target_url, ctx):
    """
    Upload a file to a SharePoint document library.
    """
    target_folder = ctx.web.get_folder_by_server_relative_url(target_url)
    target_file = target_folder.upload_file(filename, file_bytes)
    try:
        ctx.execute_query()
    except ValueError as e:
        if "auth cookies" in str(e):
            return None
        raise
    
    return target_file.serverRelativeUrl


def fetch_akv():
    
    kv_name = os.environ["KEY_VAULT_NAME"]        
    pem_secret_name = os.environ.get("SSH_PEM_SECRET_NAME")
    passphrase_secret_name = os.environ.get("SSH_KEY_PASSPHRASE")  

    vault_uri = f"https://{kv_name}.vault.azure.net"

    credential = DefaultAzureCredential()          # uses managed identity in Azure, env creds locally
    client = SecretClient(vault_url=vault_uri, credential=credential)
    pem_secret = client.get_secret(pem_secret_name).value  # PEM text
    passphrase = client.get_secret(passphrase_secret_name).value if passphrase_secret_name else None
 
    # Use Paramiko straight from string (no file on disk)
    try:
        pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(pem_secret), password=passphrase)
    except paramiko.ssh_exception.SSHException:
        pkey = paramiko.RSAKey.from_private_key(io.StringIO(pem_secret), password=passphrase)


def use_akv():
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect("files.example.com", username="svc_sftp", pkey=pkey, look_for_keys=False)