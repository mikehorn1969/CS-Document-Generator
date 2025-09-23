import os
from threading import Thread
from flask import redirect, render_template, url_for
from app import create_app
from app.helper import wait_for_db

app = create_app()
db_ready = False

def db_check_thread():
    global db_ready
    db_ready = wait_for_db()

@app.route('/')
def index():
    if not db_ready:
        return redirect(url_for('waiting'))
    return render_template('index.html')  # Your main app page

@app.route('/waiting')
def waiting():
    return render_template('waiting.html')  # Show waiting message

if __name__ == '__main__':
    # Start DB check in a background thread
    Thread(target=db_check_thread, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

