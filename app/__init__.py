from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from app.keyvault import get_secret
import os, secrets
import dotenv
import logging
import threading
import time
import pyodbc

# Initialise extensions globally
db = SQLAlchemy()

from app.helper import load_config

# Global flag for database connection status
db_connected = False
db_error = None
db_lock = threading.Lock()
db_waking = False  # Flag to indicate database is waking up
app_instance = None  # Store app instance for background thread
db_engine = None  # Store the engine globally


def initialize_database_connection(app=None):
    """Attempt database connection and update app config/status flags."""
    global db_connected, db_error, db_waking, db_engine, app_instance

    target_app = app or app_instance

    try:
        engine = build_engine()
        if engine:
            # build_engine already validates connectivity; store URI for Flask-SQLAlchemy.
            if target_app:
                target_app.config['SQLALCHEMY_DATABASE_URI'] = str(engine.url)
            db_engine = engine

            with db_lock:
                db_connected = True
                db_error = None
                db_waking = False

            logging.info("Database connected successfully")
            return True

    except Exception as e:
        error_str = str(e)
        # Check if it's a serverless database waking up (error 40613 OR timeout errors)
        if '40613' in error_str or '08001' in error_str or 'timeout' in error_str.lower():
            logging.info("Database is paused/waking up - will retry in background")
            with db_lock:
                db_connected = False
                db_error = None
                db_waking = True
            # Start background thread to keep trying
            threading.Thread(target=connect_database_background, daemon=True).start()
        else:
            # Permanent error
            logging.error(f"Database connection failed: {e}")
            with db_lock:
                db_connected = False
                db_error = error_str
                db_waking = False

    """ # Set dummy URI to prevent SQLAlchemy errors when DB is not ready.  LET THE CODE HANDLE THIS    
    if target_app:
        target_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' """

    return False

# Initialise the app
def create_app():
    global app_instance
    app = Flask(__name__)
    app_instance = app

    # Load the config
    dotenv.load_dotenv()

    config_mode = get_secret('FLASK_CONFIG', 'FLASK-CONFIG')
    app.config.from_object(f'config.{config_mode}')
    app.secret_key = secrets.token_hex(32)

    # Try to connect to database on startup
    initialize_database_connection(app)
    
    db.init_app(app)

    from app.views import views_bp
    app.register_blueprint(views_bp)
    
    # Application-level utility routes (not part of main business logic)
    @app.route('/waiting')
    def waiting():
        global db_connected

        next_url = request.args.get('next') or url_for('views.index')
        if db_connected:
            return redirect(next_url)

        return render_template('waiting.html', next_url=next_url)
    
    @app.route('/db-status')
    def db_status():
        """Database connection status endpoint for monitoring"""
        global db_connected, db_error, db_waking
        with db_lock:
            response = {
                'connected': db_connected,
                'error': db_error,
                'waking': db_waking
            }
        return response, 200, {'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0'}
    
    # Add diagnostic endpoint to check data
    @app.route('/db-check')
    def db_check():
        from sqlalchemy import text
        global db_connected
        
        if not db_connected:
            return {'error': 'Database not connected'}, 503
        
        try:
            # Check table exists and count records
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) as total, COUNT(CASE WHEN UPPER(sid) = 'CS' THEN 1 END) as cs_count FROM dbo.ServiceStandard"))
                row = result.fetchone()
                
                if row is None:
                    return {'error': 'No data returned from query'}, 500
                
                # Get sample of CS records
                cs_records = conn.execute(text("SELECT TOP 5 stdid, sid, ssn, description FROM dbo.ServiceStandard WHERE UPPER(sid) = 'CS'"))
                cs_data = [{'stdid': r[0], 'sid': r[1], 'ssn': r[2], 'description': r[3]} for r in cs_records]
                
                return {
                    'total_records': row[0],
                    'cs_records': row[1],
                    'sample_data': cs_data,
                    'database_url': str(db.engine.url).replace(str(db.engine.url).split('@')[0].split('/')[-1], '****') if '@' in str(db.engine.url) else 'sqlite'
                }
        except Exception as e:
            return {'error': str(e)}, 500
    
    # Show waiting page if database not connected
    @app.before_request
    def check_db_connection():
        global db_connected
        
        # Allow these endpoints without requiring database connection
        allowed_paths = ['/waiting', '/db-status', '/db-check', '/static/', '/favicon.ico']
        if any(request.path.startswith(path) for path in allowed_paths):
            return None
            
        # For all other routes, show waiting page if database not ready
        if not db_connected:
            next_url = request.full_path if request.query_string else request.path
            if next_url.endswith('?'):
                next_url = next_url[:-1]
            return render_template('waiting.html', next_url=next_url)
        
        return None

    return app


def connect_database_background():
    """Background thread to connect to database when it's waking up"""
    global db_connected, db_error, db_waking, app_instance, db_engine
    
    max_attempts = 30  # Reduced attempts since each attempt now waits 2 minutes
    attempt = 0
    
    while attempt < max_attempts:
        try:
            logging.info(f"Background connection attempt {attempt + 1}/{max_attempts}")
            engine = build_engine()
            
            if engine:
                # Test the connection
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                # Update the app configuration with the real database URI
                if app_instance:
                    with app_instance.app_context():
                        # Dispose temporary SQLite engine completely
                        if db.engine:
                            db.engine.dispose()
                        
                        # Update config
                        app_instance.config['SQLALCHEMY_DATABASE_URI'] = str(engine.url)
                        db_engine = engine
                        
                        # Force SQLAlchemy to use the new engine by replacing it
                        db.session.remove()
                        db.get_engine().dispose()
                        
                        # Test with actual query using the NEW engine directly
                        with engine.connect() as test_conn:
                            result = test_conn.execute(text("SELECT COUNT(*) FROM dbo.ServiceStandard"))
                            logging.info(f"Successfully connected to SQL Server with {result.scalar()} standards")
                
                with db_lock:
                    db_connected = True
                    db_error = None
                    db_waking = False
                
                logging.info("Database connected successfully in background and app reconfigured")
                return  # Success, exit thread
                
        except Exception as e:
            error_str = str(e)
            attempt += 1
            
            # Check if still waking up (40613, timeout, or 08001 errors)
            if '40613' in error_str or '08001' in error_str or 'timeout' in error_str.lower():
                logging.info(f"Database still waking up, attempt {attempt}/{max_attempts}")
                time.sleep(10)  # Wait 10 seconds before retry (build_engine waits 2 mins internally)
            else:
                # Different error - stop trying
                logging.error(f"Database connection failed with non-waking error: {e}")
                with db_lock:
                    db_connected = False
                    db_error = error_str
                    db_waking = False
                return
    
    # Timeout after max attempts
    logging.error("Database wake-up timeout exceeded")
    with db_lock:
        db_connected = False
        db_error = "Database wake-up timeout: The database did not become available within the expected time."
        db_waking = False


def build_engine():
    from urllib.parse import quote_plus
    
    # Debug: Check available drivers
    available_drivers = []
    try:
        available_drivers = list(pyodbc.drivers())
        logging.info(f"Available ODBC drivers: {available_drivers}")
    except Exception as e:
        logging.error(f"Failed to list ODBC drivers: {e}")
    
    # Get secrets from environment or Key Vault
    config = load_config()
    sql_username = config.get("SQL_USERNAME")
    sql_password = config.get("SQL_PASSWORD")
    sql_servername = config.get("SQL_SERVERNAME")
    sql_databasename = config.get("SQL_DATABASE")
    sql_port = config.get("SQL_PORT")
        
    if not all([sql_username, sql_password, sql_servername, sql_databasename]):
        raise RuntimeError("Missing one or more required SQL environment variables for db connection.")
    
    # Select the best installed SQL Server ODBC driver.
    preferred_drivers = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "ODBC Driver 13 for SQL Server",
        "ODBC Driver 11 for SQL Server",
        "SQL Server",
    ]
    driver = next((d for d in preferred_drivers if d in available_drivers), None)
    if not driver:
        raise RuntimeError(
            "No compatible SQL Server ODBC driver found. "
            "Install 'ODBC Driver 18 for SQL Server' (or 17)."
        )
    
    # Connection string for Azure SQL serverless with MUCH longer timeouts
    odbc_params = (
        f"DRIVER={{{driver}}};"
        f"Server=tcp:{sql_servername},{sql_port};"
        f"Database={sql_databasename};"
        f"Uid={sql_username};"
        f"Pwd={sql_password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=120;"  # Increased to 2 minutes for serverless wake-up
        "Login Timeout=120;"        # Increased to 2 minutes for serverless wake-up
    )

    safe_odbc_params = odbc_params.replace(f"Pwd={sql_password};", "Pwd=****;")
    logging.info(f"Using driver: {driver}")
    logging.info(f"Connection string: {safe_odbc_params}")

    engine = create_engine(
        "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc_params),
        pool_pre_ping=True,
        pool_recycle=1800,
        fast_executemany=True,
        pool_size=5,
        max_overflow=10,
        connect_args={
            "timeout": 120,  # DBAPI timeout also increased
        }
    )

    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        logging.info(f"Successfully connected using driver: {driver}")
    
    return engine

