import sys
import os
import pytest

from app import helper, create_app
from app.helper import downloadFromSharePoint, serve_docx 

# Fixture to create a test client
@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_downloadFromSharePoint():
    
    target_folder = "Templates/Business templates/Service Provider Templates"
    target_file = "Service Provider NDA AUTOMATED MASTER.docx"
    
    file_bytes = downloadFromSharePoint(target_folder, target_file)
    
    assert file_bytes is not None
    assert isinstance(file_bytes, bytes)
    assert len(file_bytes) > 0
    
    preview = serve_docx(file_bytes, target_file)

    assert preview is not None, "Preview generation failed"