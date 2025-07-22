from app import app
from flask import Flask, render_template, request

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/c7data')
def capture_c7data():
    return 'c7data'

@app.route('/chdata')
def check_chdata():
    return 'chdata'

@app.route('/servicestandards', methods=['GET', 'POST'])
def set_servicestandards():

    if request.method == 'POST':
        ssn = request.form.get('ssn','')
        sdesc = request.form.get('service-description','')

        return 'servicestandards submitted'
    
    return render_template('main.html')

@app.route('/servicearrangements')
def set_servicearrangements():
    return 'servicearrangements'


    
