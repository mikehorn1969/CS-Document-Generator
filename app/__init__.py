from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Tech Debt: my be able to remove
import os, secrets
import dotenv
from sqlalchemy import create_engine, text
from app.keyvault import get_secret

# Initialise extensions globally
db = SQLAlchemy()
migrate = Migrate()

# Initialise the app
def create_app():
    app = Flask(__name__)

    # Load the config
    # Select config class based on environment variable
    dotenv.load_dotenv()

    config_mode = os.environ.get('FLASK_CONFIG', 'DevelopmentConfig')
    app.config.from_object(f'config.{config_mode}')
    app.secret_key = secrets.token_hex(32)

    engine = build_engine()
    if not engine:
        raise RuntimeError("Failed to create database engine.") 
    
    app.config['SQLALCHEMY_DATABASE_URI'] = str(engine.url)  # Flask needs this
    db.init_app(app)
    migrate.init_app(app, db)

    from app.views import views_bp
    app.register_blueprint(views_bp)

    return app


def build_engine():
    from urllib.parse import quote_plus
    import logging
    import time
    # Base ODBC parameters

    sql_username = get_secret("SQL-USERNAME")
    sql_password = get_secret("SQL-PASSWORD")
    sql_servername = get_secret("SQL-SERVERNAME")
    sql_databasename = get_secret("SQL-DATABASE")
    sql_port = get_secret("SQL-PORT")
    if not all([sql_username, sql_password, sql_servername, sql_databasename]):
        raise RuntimeError("Missing one or more required SQL environment variables for db connection.")
    odbc_params = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{sql_servername},{sql_port};"
        f"Database={sql_databasename};"
        f"Uid={sql_username};"
        f"Pwd={sql_password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Login Timeout=90;"
        "ConnectRetryCount=3;"
        "ConnectRetryInterval=10;"
    )

    # Optional: log connection string without password for debugging
    safe_odbc_params = odbc_params.replace(f"Pwd={sql_password};", "Pwd=****;")
    logging.info(f"Connecting to SQL Server with: {safe_odbc_params}")

    engine = create_engine(
        "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc_params),
        pool_pre_ping=True,
        pool_recycle=1800,
        fast_executemany=True,
    )

    # Test db connection on startup, with retry logic as the db may not be ready yet
    max_retries = 3
    retry_delay = 1  # Start with 1 second delay
    
    for attempt in range(1, max_retries + 1):
        try:
            # Create a fresh connection each time
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))  # Simple test query that doesn't depend on table existence
                logging.info(f"Database connection successful on attempt {attempt}.")
                break  # Success, exit the retry loop
        except Exception as e:
            logging.warning(f"Connection attempt {attempt} failed: {e}")
            if attempt == max_retries:
                logging.error(f"All {max_retries} connection attempts failed.")
                raise  # Re-raise the exception after all retries fail
            
            # Exponential backoff: wait longer after each failure
            wait_time = retry_delay * (2 ** (attempt - 1))
            logging.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    return engine

