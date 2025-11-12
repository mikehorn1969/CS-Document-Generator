import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from app import helper
from app.helper import downloadFromSharePoint, serve_docx 


def test_downloadFromSharePoint():
    
    target_folder = "Templates/Business templates/Service Provider Templates"
    target_file = "Service Provider NDA AUTOMATED MASTER.docx"
    
    file_bytes = downloadFromSharePoint(target_folder, target_file)
    
    assert file_bytes is not None
    assert isinstance(file_bytes, bytes)
    assert len(file_bytes) > 0
    
    return serve_docx(file_bytes, target_file)
