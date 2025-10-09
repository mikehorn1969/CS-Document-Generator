# Example Flask route
import app
from app.helper import serve_docx_with_agreement_date

@app.route('/show-docx')
def show_docx():
    return serve_docx_with_agreement_date("target-folder", "test.docx")