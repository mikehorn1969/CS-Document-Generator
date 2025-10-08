from app import helper
from app.helper import downloadFromSharePoint, serve_docx 


def test_downloadFromSharePoint():
    
    target_folder = "Templates/Business templates/Service Provider Templates"
    target_file = "Client MSA - AUTOMATED MASTER.docx"
    
    file_bytes = downloadFromSharePoint(target_folder, target_file)
    
    assert file_bytes is not None
    assert isinstance(file_bytes, bytes)
    assert len(file_bytes) > 0
    
    

    