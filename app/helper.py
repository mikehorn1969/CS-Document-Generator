# helper.py
from __future__ import annotations

import os
import io
import requests
import paramiko
from typing import Optional, Dict

# local .env support
from dotenv import load_dotenv
load_dotenv()

# Azure Key Vault (optional fallback if env var missing)
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from msal import ConfidentialClientApplication

# -----------------------------
# Internal helpers
# -----------------------------
def _get_kv_client() -> Optional[SecretClient]:
    """Return a SecretClient if KEY_VAULT_NAME is configured, else None."""
    kv_name = os.environ.get("KEY_VAULT_NAME")
    if not kv_name:
        return None
    vault_uri = f"https://{kv_name}.vault.azure.net"
    credential = DefaultAzureCredential()
    return SecretClient(vault_url=vault_uri, credential=credential)


def _get_secret(env_name: str, kv_secret_name: Optional[str] = None) -> str:
    """
    Fetch a secret from environment, or (if not set) from Azure Key Vault.
    kv_secret_name defaults to env_name if not supplied.
    """
    val = os.environ.get(env_name)
    if val:
        return val

    client = _get_kv_client()
    if not client:
        raise KeyError(
            f"Required secret '{env_name}' not set and KEY_VAULT_NAME is not configured."
        )

    secret_name = kv_secret_name or env_name
    try:
        result = client.get_secret(secret_name).value 
        return result if result is not None else ""
    except Exception as exc:
        raise KeyError(
            f"Failed to retrieve '{secret_name}' from Azure Key Vault."
        ) from exc


# -----------------------------
# Public configuration loaders
# -----------------------------
def load_config() -> dict[str, str | dict]:
    """
    Load core application secrets.
    Prefers environment variables; falls back to AKV if available.
    Returns a plain dict; nothing is cached globally.
    """
    # C7 / CH / NameAPI
    c7_key = _get_secret("C7_KEY", "C7APIKey")
    c7_userid = _get_secret("C7_USERID", "C7USERID")
    ch_key = _get_secret("CH_KEY", "CHKEY")

    # NameAPI can arrive split; support both patterns.
    nameapi_key = os.environ.get("NAMEAPI_KEY")
    if not nameapi_key:
        prefix = _get_secret("NAMEAPI_KEYPREFIX", "NAMEAPI-KEYPREFIX")
        suffix = _get_secret("NAMEAPI_KEYSUFFIX", "NAMEAPI-KEYSUFFIX")
        nameapi_key = f"{prefix}-{suffix}"

    c7_hdr = {
        "Cache-Control": "no-cache",
        "Ocp-Apim-Subscription-Key": c7_key,
    }

    return {
        "C7_KEY": c7_key,
        "C7_USERID": c7_userid,
        "CH_KEY": ch_key,
        "NAMEAPI_KEY": nameapi_key,
        "C7_HDR": c7_hdr,
    }


def load_azure_app_identity() -> Dict[str, str]:
    """
    Load Azure app-registration credentials (when not using managed identity).
    These should normally be provided by the platform as env vars.
    """
    return {
        "AZURE_CLIENT_ID": _get_secret("AZURE_CLIENT_ID"),
        "AZURE_TENANT_ID": _get_secret("AZURE_TENANT_ID"),
        "AZURE_CLIENT_SECRET": _get_secret("AZURE_CLIENT_SECRET"),
    }


# -----------------------------
# Utilities
# -----------------------------
def formatName(name_string: str) -> str:
    """
    Convert 'Surname, Forename[:extra]' -> 'Forename Surname'
    """
    name_array = name_string.split(",")
    forename_part = name_array[1].strip() if len(name_array) > 1 else ""
    surname_part = name_array[0].strip()
    surname_only = surname_part.split(":")[0].strip()
    return f"{forename_part} {surname_only}".strip()


def synonymsOf(word: str):
    """
    Fetch synonyms for names from the Stands4 API.
    Requires STANDS4_USERID and STANDS4_TOKEN.
    """
    userid = _get_secret("STANDS4_USERID")
    token = _get_secret("STANDS4_TOKEN")

    api_url = (
        "https://api.stands4.com/v1/synonyms"
        f"?word={word}&userid={userid}&token={token}"
    )
    resp = requests.get(api_url, timeout=20)
    if resp.status_code == 200:
        try:
            return resp.json().get("synonyms", [])
        except Exception:
            return []
    return []


def uploadToSharePoint(file_bytes: bytes, filename: str, target_url):
    
    """
    Upload a file to SharePoint using Microsoft Graph API.
    """

    azure_cfg = load_azure_app_identity()
    client_id = azure_cfg.get('AZURE_CLIENT_ID','')
    client_secret = azure_cfg.get('AZURE_CLIENT_SECRET','')  
    tenant_id = azure_cfg.get('AZURE_TENANT_ID','')

    authority = f'https://login.microsoftonline.com/{tenant_id}'
    scope = ['https://graph.microsoft.com/.default']

    app = ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    token_response = app.acquire_token_for_client(scopes=scope)

    access_token = token_response.get('access_token')
   
    site_name = 'InternalTeam'
    site_domain = 'jjag.sharepoint.com'
    library = 'Mike'
    folder_path = target_url 
    file_name = filename

    # Get Site ID
    site_url = f'https://graph.microsoft.com/v1.0/sites/{site_domain}:/sites/{site_name}'
    site_response = requests.get(site_url, headers={'Authorization': f'Bearer {access_token}'})

    if site_response.status_code != 200:
        print(f"Error getting site ID: {site_response.status_code} - {site_response.text}")
        return None

    site_id = site_response.json()['id']

    # Upload file
    upload_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{library}/{folder_path}/{file_name}:/content'
    #upload_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{folder_path}/{file_name}:/content'
    print(f"Uploading to URL: {upload_url}")

    upload_response = requests.put(upload_url, headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/octet-stream'
    }, data=file_bytes)

    return upload_response.status_code
    




# -----------------------------
# SSH key handling (AKV fallback)
# -----------------------------
def load_ssh_private_key() -> paramiko.PKey:
    """
    Load an SSH private key (PEM) either from:
      - env vars (PEM text in SSH_PEM, passphrase in SSH_KEY_PASSPHRASE), or
      - Azure Key Vault secrets named by SSH_PEM_SECRET_NAME / SSH_KEY_PASSPHRASE_SECRET

    Returns a paramiko PKey (Ed25519 preferred, fallback to RSA).
    """
    pem_text = os.environ.get("SSH_PEM")
    passphrase = os.environ.get("SSH_KEY_PASSPHRASE")

    if pem_text is None:
        pem_secret_name = _get_secret("SSH_PEM_SECRET_NAME")
        passphrase_secret_name = os.environ.get("SSH_PASSPHRASE_SECRET")  # optional
        client = _get_kv_client()
        if not client:
            raise KeyError(
                "SSH_PEM not set and no Key Vault configured to fetch SSH key."
            )
        pem_text = client.get_secret(pem_secret_name).value
        if passphrase_secret_name:
            passphrase = client.get_secret(passphrase_secret_name).value

    # Build PKey in-memory (no temp files)
    try:
        return paramiko.Ed25519Key.from_private_key(
            io.StringIO(pem_text), password=passphrase
        )
    except paramiko.SSHException:
        return paramiko.RSAKey.from_private_key(
            io.StringIO(pem_text), password=passphrase
        )


def open_ssh_client(
    host: str,
    username: str,
    pkey: Optional[paramiko.PKey] = None,
    *,
    port: int = 22,
    strict_host_key_checking: bool = True,
) -> paramiko.SSHClient:
    """
    Open and return a connected Paramiko SSHClient.
    """
    if pkey is None:
        pkey = load_ssh_private_key()

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(
        paramiko.RejectPolicy() if strict_host_key_checking else paramiko.AutoAddPolicy()
    )
    client.connect(
        host,
        port=port,
        username=username,
        pkey=pkey,
        look_for_keys=False,
        allow_agent=False,
        timeout=30,
    )
    return client
