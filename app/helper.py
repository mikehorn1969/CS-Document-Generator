# helper.py
from __future__ import annotations
import os
import requests
import time
from typing import Optional, Dict
from sqlalchemy.exc import OperationalError, DisconnectionError
from app.keyvault import get_secret
from docx import Document
from flask import send_file
from datetime import datetime
import tempfile
from azure.identity import DefaultAzureCredential
from app import db


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
    c7_key = get_secret("C7APIKey")
    c7_userid = get_secret("C7USERID")
    ch_key = get_secret("CHKEY")
    sql_username = get_secret("SQL-USERNAME")
    sql_password = get_secret("SQL-PASSWORD")
    prefix = get_secret("NAMEAPI-KEYPREFIX")
    suffix = get_secret("NAMEAPI-KEYSUFFIX")
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
        "SQL_USERNAME": sql_username,
        "SQL_PASSWORD": sql_password,
    }


def load_azure_app_identity() -> Dict[str, str]:
    """
    Load Azure app-registration credentials (when not using managed identity).
    These should normally be provided by the platform as env vars.
    """
    return {
        "AZURE_CLIENT_ID": get_secret("AZURE-CLIENT-ID"),
        "AZURE_TENANT_ID": get_secret("AZURE-TENANT-ID"),
        "AZURE_CLIENT_SECRET": get_secret("AZURE-CLIENT-SECRET"),
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


def uploadToSharePoint(file_bytes: bytes, filename: str, target_url):
    """
    Upload a file to SharePoint using Microsoft Graph API and managed identity.
    """
    credential = DefaultAzureCredential()
    token = credential.get_token("https://graph.microsoft.com/.default")
    access_token = token.token

    site_name = get_secret('SP-SITE-NAME')
    site_domain = get_secret('SP-SITE-DOMAIN')
    library = get_secret('SP-LIBRARY')
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
    print(f"Uploading to URL: {upload_url}")

    upload_response = requests.put(upload_url, headers={
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/octet-stream'
    }, data=file_bytes)

    return upload_response.status_code


def downloadFromSharePoint(folder_path: str, filename: str) -> Optional[bytes]:
    """
    Download a file from SharePoint using Microsoft Graph API and managed identity.
    Returns the file bytes if successful, else None.
    """
    credential = DefaultAzureCredential()
    token = credential.get_token("https://graph.microsoft.com/.default")
    access_token = token.token

    site_name = get_secret('SP-SITE-NAME')
    site_domain = get_secret('SP-SITE-DOMAIN')

    # Get Site ID
    site_url = f'https://graph.microsoft.com/v1.0/sites/{site_domain}:/sites/{site_name}'
    site_response = requests.get(site_url, headers={'Authorization': f'Bearer {access_token}'})

    if site_response.status_code != 200:
        print(f"Error getting site ID: {site_response.status_code} - {site_response.text}")
        return None

    site_id = site_response.json()['id']

    # Download file
    download_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{folder_path}/{filename}'
    print(f"Downloading from URL: {download_url}")

    download_response = requests.get(download_url, headers={
        'Authorization': f'Bearer {access_token}'
    })

    if download_response.status_code == 200:
        return download_response.content
    else:
        print(f"Error downloading file: {download_response.status_code} - {download_response.text}")
        return None


def wait_for_db(max_wait=120, interval=5):
    """Wait for the Azure database to be available before starting the app."""
    waited = 0
    while waited < max_wait:
        try:
            # Check if the connection is alive
            db.session.connection()
            print("Database is available.")
            return True
        except OperationalError:
            print(f"Database not available, retrying in {interval}s...")
            time.sleep(interval)
            waited += interval
    print("Database did not become available in time.")
    return False


def debugMode():
    config_mode = os.environ.get('FLASK_CONFIG', 'DevelopmentConfig')
    return config_mode == 'DevelopmentConfig'


def serve_docx(file_bytes: bytes, filename: str):
    """
    Open a docx from bytes, replace placeholders, and serve to user
    """
    # Create temp file and keep it open
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    output = None

    try:
        # Write bytes to temp file
        tmp.write(file_bytes)
        tmp.flush()  # Ensure all data is written
        tmp.close()  # Close but don't delete yet

        # Open and modify the document
        doc = Document(tmp.name)
        today_str = datetime.today().strftime('%d %B %Y')

        # Replace {{AgreementDate}} in all paragraphs
        for para in doc.paragraphs:
            if "{{AgreementDate}}" in para.text:
                para.text = para.text.replace("{{AgreementDate}}", today_str)

        # Also replace in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if "{{AgreementDate}}" in cell.text:
                        cell.text = cell.text.replace("{{AgreementDate}}", today_str)

        # Create new temp file for modified document
        output = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc.save(output.name)
        output.close()

        # Send file to user
        return send_file(
            output.name,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    finally:
        # Clean up temp files
        import os
        try:
            os.unlink(tmp.name)
            if output is not None:
                os.unlink(output.name)
        except:
            pass  # Ignore cleanup errors


def execute_db_query_with_retry(stmt, operation_name="database query"):
    """
    Execute a database query with retry logic for connection issues.
    
    Args:
        stmt: SQLAlchemy statement to execute
        operation_name: Description of the operation for logging
    
    Returns:
        Query results or empty list if all retries fail
    """
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            query_result = db.session.execute(stmt).scalars().all()
            return query_result
            
        except (OperationalError, DisconnectionError) as e:
            if debugMode():
                print(f"{datetime.now().strftime('%H:%M:%S')} {operation_name}: Database connection error on attempt {attempt + 1}: {str(e)}")
            
            if attempt < max_retries - 1:
                # Close the current session to ensure clean retry
                try:
                    db.session.rollback()
                except:
                    pass
                
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                if debugMode():
                    print(f"{datetime.now().strftime('%H:%M:%S')} {operation_name}: All retry attempts failed, returning empty list")
                return []
        
        except Exception as e:
            if debugMode():
                print(f"{datetime.now().strftime('%H:%M:%S')} {operation_name}: Unexpected error: {str(e)}")
            return []