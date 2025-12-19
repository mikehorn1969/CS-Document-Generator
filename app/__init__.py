from flask import Flask, render_template
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

# Global flag for database connection status
db_connected = False
db_error = None
db_lock = threading.Lock()
db_waking = False  # Flag to indicate database is waking up
app_instance = None  # Store app instance for background thread
db_engine = None  # Store the engine globally

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
    global db_connected, db_error, db_waking, db_engine
    try:
        engine = build_engine()
        if engine:
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            app.config['SQLALCHEMY_DATABASE_URI'] = str(engine.url)
            db_engine = engine
            
            with db_lock:
                db_connected = True
                db_error = None
                db_waking = False
            
            logging.info("Database connected successfully")
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
        
        # Set dummy URI to prevent SQLAlchemy errors
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    db.init_app(app)

    from app.views import views_bp
    app.register_blueprint(views_bp)
    
    # Add waiting page route
    @app.route('/waiting')
    def waiting():
        return render_template('waiting.html')
    
    # Add database status endpoint
    @app.route('/db-status')
    def db_status():
        global db_connected, db_error, db_waking
        with db_lock:
            return {
                'connected': db_connected,
                'error': db_error,
                'waking': db_waking
            }
    
    # Redirect to waiting page if DB not connected
    @app.before_request
    def check_db_connection():
        from flask import request
        global db_connected
        
        # Allow these endpoints without DB
        allowed = ['/waiting', '/db-status', '/static/', '/favicon.ico']
        if any(request.path.startswith(path) for path in allowed):
            return None
            
        # Show waiting page if not connected
        if not db_connected and request.path != '/waiting':
            return render_template('waiting.html')
        
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
                        # Dispose old SQLite engine completely
                        if db.engine:
                            db.engine.dispose()
                        
                        # Update config
                        app_instance.config['SQLALCHEMY_DATABASE_URI'] = str(engine.url)
                        db_engine = engine
                        
                        # Force SQLAlchemy to use the new engine by replacing it
                        db.session.remove()
                        db.get_engine().dispose()
                        
                        # Test with actual query
                        with db.engine.connect() as test_conn:
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
    try:
        available_drivers = pyodbc.drivers()
        logging.info(f"Available ODBC drivers: {list(available_drivers)}")
    except Exception as e:
        logging.error(f"Failed to list ODBC drivers: {e}")
    
    # Get secrets from environment or Key Vault
    sql_username = get_secret("SQL_USERNAME", "SQL-USERNAME")
    sql_password = get_secret("SQL_PASSWORD", "SQL-PASSWORD")
    sql_servername = get_secret("SQL_SERVERNAME", "SQL-SERVERNAME")
    sql_databasename = get_secret("SQL_DATABASE", "SQL-DATABASE")
    sql_port = get_secret("SQL_PORT", "SQL-PORT")
    
    # Debug: Log connection parameters (without password)
    logging.info(f"SQL Server: {sql_servername}")
    logging.info(f"SQL Port: {sql_port}")
    logging.info(f"SQL Database: {sql_databasename}")
    logging.info(f"SQL Username: {sql_username}")
    
    if not all([sql_username, sql_password, sql_servername, sql_databasename]):
        raise RuntimeError("Missing one or more required SQL environment variables for db connection.")
    
    # Only try ODBC Driver 18 for serverless databases
    driver = "ODBC Driver 18 for SQL Server"
    
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

