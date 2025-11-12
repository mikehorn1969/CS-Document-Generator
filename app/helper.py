# helper.py
from __future__ import annotations
import os
import requests
import time
from typing import Optional, Dict
from sqlalchemy.exc import OperationalError, DisconnectionError
from app.keyvault import get_secret
from docx import Document
from flask import send_file, Response
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
    library= "Common"

    # Get Site ID
    site_url = f'https://graph.microsoft.com/v1.0/sites/{site_domain}:/sites/{site_name}'
    site_response = requests.get(site_url, headers={'Authorization': f'Bearer {access_token}'})

    if site_response.status_code != 200:
        print(f"Error getting site ID: {site_response.status_code} - {site_response.text}")
        return None

    site_id = site_response.json()['id']

    # Get file metadata first to get the download URL
    metadata_url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{library}/{folder_path}/{filename}'
    print(f"Getting file metadata from: {metadata_url}")

    metadata_response = requests.get(metadata_url, headers={
        'Authorization': f'Bearer {access_token}'
    })

    if metadata_response.status_code == 200:
        metadata = metadata_response.json()
        download_url = metadata.get('@microsoft.graph.downloadUrl')
        
        if download_url:
            print(f"Downloading file content from: {download_url}")
            
            # Download the actual file content using the download URL
            file_response = requests.get(download_url)
            
            if file_response.status_code == 200:
                content = file_response.content
                
                # Check if content looks like a valid DOCX file (should start with PK)
                if len(content) > 0 and content[:2] == b'PK':
                    if debugMode():
                        print(f"Downloaded file size: {len(content)} bytes")
                    return content
                else:
                    print(f"Downloaded content is not a valid DOCX file, size: {len(content)} bytes")
                    print(f"Content preview: {content[:100]}")
                    return None
            else:
                print(f"Error downloading file content: {file_response.status_code}")
                return None
        else:
            print("No download URL found in metadata")
            return None
    else:
        print(f"Error getting file metadata: {metadata_response.status_code} - {metadata_response.text}")
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


def serve_docx(file_bytes: bytes, filename: str, replacements: Optional[dict] = None):
    """
    Open a docx from bytes, replace placeholders, convert to HTML and serve for viewing
    """
    import tempfile
    import os
    from flask import Response
    
    # Default replacements if none provided
    if replacements is None:
        replacements = {}
    
    # Add today's date as default replacement
    today_str = datetime.today().strftime('%d %B %Y')
    replacements.setdefault('{{DocDate}}', today_str)
    
    
    # Validate input
    if not file_bytes or len(file_bytes) < 100:
        raise ValueError(f"Invalid file_bytes provided, size: {len(file_bytes) if file_bytes else 0}")
    
    # Check if it looks like a DOCX file
    if file_bytes[:2] != b'PK':
        raise ValueError("File does not appear to be a valid DOCX file (missing PK header)")
    
    tmp_dir = tempfile.gettempdir()
    tmp_path = None

    try:
        # Create a unique temporary file path
        import uuid
        unique_id = str(uuid.uuid4())
        tmp_path = os.path.join(tmp_dir, f"docx_input_{unique_id}.docx")

        # Write bytes to temp file
        with open(tmp_path, 'wb') as f:
            f.write(file_bytes)

        if debugMode():
            print(f"Created temp file: {tmp_path}")
            print(f"File exists: {os.path.exists(tmp_path)}")
            print(f"File size: {os.path.getsize(tmp_path)} bytes")

        # Open and modify the document
        doc = Document(tmp_path)
        if debugMode():
            print("Document loaded successfully")
            
        # Replace placeholders in paragraphs
        replace_text_in_document(doc, replacements)

        if debugMode():
            print("Document modifications completed")

        # Convert document to HTML
        html_content = convert_docx_to_html(doc)

        if debugMode():
            print("Document converted to HTML successfully")

        # Return HTML response for inline viewing
        return Response(
            html_content,
            mimetype='text/html',
            headers={
                'Content-Disposition': f'inline; filename="{filename}.html"'
            }
        )

    except Exception as e:
        if debugMode():
            print(f"Error in serve_docx: {str(e)}")
            import traceback
            traceback.print_exc()
        raise  # Re-raise the exception so Flask can handle it properly
        
    finally:
        # Clean up temp files
        try:
            if debugMode():
                print(f"Cleaning up temp files")
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception as cleanup_error:
            if debugMode():
                print(f"Cleanup error: {str(cleanup_error)}")


def convert_docx_to_html(doc) -> str:
    """
    Convert a python-docx Document object to HTML with enhanced formatting preservation
    """
    html_parts = []
    html_parts.append("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Document Preview</title>
        <style>
            body { 
                font-family: 'Calibri', 'Arial', sans-serif; 
                margin: 0;
                padding: 20px;
                line-height: 1.4; 
                background-color: #f0f0f0;
                font-size: 11pt;
            }
            .document {
                background-color: white;
                padding: 72px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                max-width: 8.5in;
                min-height: 11in;
                margin: 0 auto;
            }
            .page-break {
                page-break-before: always;
            }
            table { 
                border-collapse: collapse; 
                width: 100%; 
                margin: 6pt 0;
                font-size: inherit;
            }
            td, th { 
                border: 1px solid #000; 
                padding: 4pt 6pt; 
                text-align: left;
                vertical-align: top;
            }
            th { 
                background-color: #f2f2f2; 
                font-weight: bold;
            }
            p { 
                margin: 0 0 6pt 0;
                text-align: left;
            }
            .center { text-align: center; }
            .right { text-align: right; }
            .justify { text-align: justify; }
            .bold { font-weight: bold; }
            .italic { font-style: italic; }
            .underline { text-decoration: underline; }
            .heading1 { font-size: 16pt; font-weight: bold; margin: 12pt 0 6pt 0; }
            .heading2 { font-size: 14pt; font-weight: bold; margin: 10pt 0 6pt 0; }
            .heading3 { font-size: 12pt; font-weight: bold; margin: 8pt 0 6pt 0; }
            .large { font-size: 14pt; }
            .small { font-size: 9pt; }
            .indent { margin-left: 36pt; }
            .tab { margin-left: 36pt; }
        </style>
    </head>
    <body>
        <div class="document">
    """)
    
    # Convert paragraphs with enhanced formatting
    for paragraph in doc.paragraphs:
        para_html = convert_paragraph_to_html(paragraph)
        if para_html:
            html_parts.append(para_html)
    
    # Convert tables with enhanced formatting
    for table in doc.tables:
        html_parts.append(convert_table_to_html(table))
    
    html_parts.append("""
        </div>
    </body>
    </html>
    """)
    
    return ''.join(html_parts)


def convert_paragraph_to_html(paragraph) -> str:
    """Convert a paragraph with formatting to HTML"""
    if not paragraph.text.strip():
        return '<p>&nbsp;</p>'
    
    # Determine paragraph alignment
    alignment_class = ""
    if hasattr(paragraph, 'alignment') and paragraph.alignment:
        if paragraph.alignment == 1:  # Center
            alignment_class = " center"
        elif paragraph.alignment == 2:  # Right
            alignment_class = " right"
        elif paragraph.alignment == 3:  # Justify
            alignment_class = " justify"
    
    # Check for heading styles
    style_class = ""
    if hasattr(paragraph, 'style') and paragraph.style:
        style_name = str(paragraph.style.name).lower()
        if 'heading 1' in style_name:
            style_class = " heading1"
        elif 'heading 2' in style_name:
            style_class = " heading2"
        elif 'heading 3' in style_name:
            style_class = " heading3"
    
    # Process runs (formatted text segments within paragraph)
    formatted_text = ""
    for run in paragraph.runs:
        text = run.text
        if not text:
            continue
            
        # Apply formatting to the run
        if run.bold:
            text = f'<strong>{text}</strong>'
        if run.italic:
            text = f'<em>{text}</em>'
        if run.underline:
            text = f'<u>{text}</u>'
        
        # Font size adjustments
        if hasattr(run, 'font') and run.font.size:
            size_pt = run.font.size.pt
            if size_pt > 12:
                text = f'<span class="large">{text}</span>'
            elif size_pt < 10:
                text = f'<span class="small">{text}</span>'
        
        formatted_text += text
    
    # If no runs processed, use plain text
    if not formatted_text:
        formatted_text = paragraph.text
    
    # Build the paragraph HTML
    classes = f"class='{style_class}{alignment_class}'" if (style_class or alignment_class) else ""
    
    return f'<p {classes}>{formatted_text}</p>'


def convert_table_to_html(table) -> str:
    """Convert a table with formatting to HTML"""
    html_parts = ['<table>']
    
    for row_idx, row in enumerate(table.rows):
        html_parts.append('<tr>')
        for cell in row.cells:
            # Use th for first row if it looks like headers
            tag = 'th' if row_idx == 0 and is_header_row(row) else 'td'
            
            # Process cell content with formatting
            cell_content = ""
            for paragraph in cell.paragraphs:
                para_html = convert_paragraph_to_html(paragraph)
                if para_html:
                    # Remove <p> tags for table cells to avoid extra spacing
                    para_content = para_html.replace('<p>', '').replace('</p>', '')
                    if para_content.strip():
                        cell_content += para_content + '<br/>'
            
            # Remove trailing <br/>
            cell_content = cell_content.rstrip('<br/>')
            
            html_parts.append(f'<{tag}>{cell_content}</{tag}>')
        html_parts.append('</tr>')
    
    html_parts.append('</table>')
    return ''.join(html_parts)


def is_header_row(row) -> bool:
    """Determine if a table row should be treated as a header"""
    # Simple heuristic: if most cells in first row are bold, treat as header
    bold_count = 0
    total_runs = 0
    
    for cell in row.cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                total_runs += 1
                if run.bold:
                    bold_count += 1
    
    return total_runs > 0 and (bold_count / total_runs) > 0.5


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

def replace_text_in_document(doc, replacements: dict):
    """
    Replace placeholder text throughout the entire document including content controls
    """
    # Replace text in content controls (fields)
    replace_text_in_content_controls(doc, replacements)
    
    # Replace text in paragraphs
    for paragraph in doc.paragraphs:
        replace_text_in_paragraph(paragraph, replacements)
    
    # Replace text in tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                # Check for content controls in table cells
                replace_text_in_content_controls_element(cell._element, replacements)
                for paragraph in cell.paragraphs:
                    replace_text_in_paragraph(paragraph, replacements)
    
    # Replace text in headers and footers
    for section in doc.sections:
        # Header
        header = section.header
        replace_text_in_content_controls_element(header._element, replacements)
        for paragraph in header.paragraphs:
            replace_text_in_paragraph(paragraph, replacements)
        
        # Footer
        footer = section.footer
        replace_text_in_content_controls_element(footer._element, replacements)
        for paragraph in footer.paragraphs:
            replace_text_in_paragraph(paragraph, replacements)


def replace_text_in_content_controls(doc, replacements: dict):
    """
    Replace text in Word content controls (fields)
    """
    try:
        # Access the document's XML element
        doc_element = doc._body._element
        replace_text_in_content_controls_element(doc_element, replacements)
    except Exception as e:
        if debugMode():
            print(f"Error replacing content controls: {e}")


def replace_text_in_content_controls_element(element, replacements: dict):
    """
    Replace text in content controls within a specific XML element
    """
    try:
        #from lxml import etree
        
        # Find all content control elements
        # These are the XML tags for different types of content controls
        cc_tags = [
            './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sdt',  # Structured document tag
            './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fldSimple',  # Simple field
            './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fldChar',  # Field character
        ]
        
        for tag_pattern in cc_tags:
            for cc in element.findall(tag_pattern):
                replace_text_in_single_content_control(cc, replacements)
                
        # Also look for text elements directly
        text_tags = './/{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'
        for text_elem in element.findall(text_tags):
            if text_elem.text:
                original_text = text_elem.text
                new_text = original_text
                for placeholder, replacement in replacements.items():
                    new_text = new_text.replace(placeholder, replacement)
                if new_text != original_text:
                    text_elem.text = new_text
                    
    except Exception as e:
        if debugMode():
            print(f"Error in replace_text_in_content_controls_element: {e}")


def replace_text_in_single_content_control(cc_element, replacements: dict):
    """
    Replace text in a single content control element
    """
    try:
        # Get all text elements within this content control
        text_elements = cc_element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
        
        for text_elem in text_elements:
            if text_elem.text:
                original_text = text_elem.text
                new_text = original_text
                
                for placeholder, replacement in replacements.items():
                    new_text = new_text.replace(placeholder, replacement)
                
                if new_text != original_text:
                    text_elem.text = new_text
                    if debugMode():
                        print(f"Replaced '{original_text}' with '{new_text}' in content control")
                        
    except Exception as e:
        if debugMode():
            print(f"Error replacing text in content control: {e}")


def replace_text_in_paragraph(paragraph, replacements: dict):
    """
    Replace text in a single paragraph while preserving formatting
    """
    try:
        # Get the full paragraph text first
        full_text = paragraph.text
        
        # Check if any placeholder exists in this paragraph
        has_placeholder = any(placeholder in full_text for placeholder in replacements.keys())
        
        if not has_placeholder:
            return
            
        # For each replacement
        for placeholder, replacement in replacements.items():
            if placeholder in full_text:
                # Try to replace within individual runs first
                replaced_in_run = False
                for run in paragraph.runs:
                    if placeholder in run.text:
                        run.text = run.text.replace(placeholder, replacement)
                        replaced_in_run = True
                        if debugMode():
                            print(f"Replaced '{placeholder}' with '{replacement}' in paragraph run")
                
                # If not replaced in runs, try across runs
                if not replaced_in_run:
                    replace_text_across_runs(paragraph, placeholder, replacement)
                    
    except Exception as e:
        if debugMode():
            print(f"Error replacing text in paragraph: {e}")


def replace_text_across_runs(paragraph, placeholder, replacement):
    """
    Replace text that spans across multiple runs in a paragraph
    """
    try:
        # Get the full paragraph text
        full_text = paragraph.text
        
        if placeholder not in full_text:
            return
        
        # Replace all occurrences
        new_text = full_text.replace(placeholder, replacement)
        
        if new_text != full_text:
            # Clear all runs
            for run in paragraph.runs[:]:
                run._element.getparent().remove(run._element)
            
            # Add the new text as a single run
            paragraph.add_run(new_text)
            
            if debugMode():
                print(f"Replaced '{placeholder}' with '{replacement}' across multiple runs")
                
    except Exception as e:
        if debugMode():
            print(f"Error replacing text across runs: {e}")