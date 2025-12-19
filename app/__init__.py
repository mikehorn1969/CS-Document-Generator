from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os, secrets
import dotenv
from sqlalchemy import create_engine, text
from app.keyvault import get_secret
import logging
import threading


# Initialise extensions globally
db = SQLAlchemy()

# Global flag for database connection status
db_connected = False
db_error = None
db_lock = threading.Lock()

# Initialise the app
def create_app():
    app = Flask(__name__)

    # Load the config
    dotenv.load_dotenv()

    config_mode = get_secret('FLASK_CONFIG', 'FLASK-CONFIG')
    app.config.from_object(f'config.{config_mode}')
    app.secret_key = secrets.token_hex(32)

    # Initialize extensions with app BEFORE starting the background thread
    # Use a placeholder URI that will be updated once connected
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('SQLALCHEMY_DATABASE_URI')
    db.init_app(app)
    
    # Start database connection in background thread
    threading.Thread(target=connect_database, args=(app,), daemon=True).start()

    from app.views import views_bp
    app.register_blueprint(views_bp)
    
    # Add waiting page route
    @app.route('/waiting')
    def waiting():
        return render_template('waiting.html')
    
    # Add database status endpoint
    @app.route('/db-status')
    def db_status():
        global db_connected, db_error
        with db_lock:
            return {
                'connected': db_connected,
                'error': db_error
            }
    
    # Redirect root to waiting page initially
    @app.before_request
    def check_db_connection():
        from flask import request
        global db_connected
        
        # Allow these endpoints without DB
        allowed = ['/waiting', '/db-status', '/static/', '/favicon.ico']
        if any(request.path.startswith(path) for path in allowed):
            return None
            
        # Redirect to waiting if not connected
        if not db_connected and request.path != '/waiting':
            return render_template('waiting.html')
        
        return None

    return app


def connect_database(app):
    """Connect to database in background thread"""
    global db_connected, db_error
    
    try:
        engine = build_engine()
        if not engine:
            with db_lock:
                db_error = "Failed to create database engine."
            return
        
        with app.app_context():
            # Test the engine we created
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            # Update the config for Flask-SQLAlchemy to use
            app.config['SQLALCHEMY_DATABASE_URI'] = str(engine.url)
            
            # Dispose of the old engine (if any) using the correct bind key
            try:
                old_engine = db.get_engine()
                old_engine.dispose()
            except Exception as e:
                logging.info(f"No existing engine to dispose: {e}")
            
            # Store the working engine in Flask-SQLAlchemy's engine registry
            # None is the default bind key
            app.extensions['sqlalchemy'].engines[None] = engine
            
            with db_lock:
                db_connected = True
                db_error = None
                
            logging.info("Database connected successfully")
            
    except Exception as e:
        with db_lock:
            db_error = str(e)
            db_connected = False
        logging.error(f"Database connection failed: {e}")
        import traceback
        logging.error(traceback.format_exc())


def build_engine():
    from urllib.parse import quote_plus
    import logging
    import time
    import pyodbc
    
    # Debug: Check available drivers
    try:
        available_drivers = pyodbc.drivers()
        logging.info(f"Available ODBC drivers: {list(available_drivers)}")
    except Exception as e:
        logging.error(f"Failed to list ODBC drivers: {e}")
    
    # Get secrets from environment or Key Vault
    # Note: Key Vault secret names use different format than env vars
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
    
    # Try different driver names
    driver_options = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server",
        "SQL Server Native Client 11.0",
        "SQL Server"
    ]
    
    last_error = None
    for driver in driver_options:
        try:
            # Add Connection Timeout for Azure SQL
            odbc_params = (
                f"DRIVER={{{driver}}};"
                f"Server=tcp:{sql_servername},{sql_port};"
                f"Database={sql_databasename};"
                f"Uid={sql_username};"
                f"Pwd={sql_password};"
                "Encrypt=yes;"
                "TrustServerCertificate=no;"
                "Connection Timeout=30;"
                "Login Timeout=30;"
                "ConnectRetryCount=3;"
                "ConnectRetryInterval=10;"
            )

            safe_odbc_params = odbc_params.replace(f"Pwd={sql_password};", "Pwd=****;")
            logging.info(f"Trying driver: {driver}")
            logging.info(f"Connection string: {safe_odbc_params}")

            engine = create_engine(
                "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc_params),
                pool_pre_ping=True,
                pool_recycle=1800,
                fast_executemany=True,
            )

            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logging.info(f"Successfully connected using driver: {driver}")
                return engine
                
        except Exception as e:
            last_error = e
            logging.warning(f"Failed with driver '{driver}': {e}")
            continue
    
    # If all drivers failed, raise the last error
    raise last_error if last_error else RuntimeError("No ODBC driver worked")

