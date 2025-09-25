from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Tech Debt: my be able to remove
import os, secrets
import dotenv
from sqlalchemy import create_engine
from sqlalchemy import text
from app.helper import load_config

from sqlalchemy.orm import sessionmaker

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
     # Choose auth by environment (simple heuristic)
    """ running_in_azure = bool(os.getenv("WEBSITE_SITE_NAME") or os.getenv("AZURE_CONTAINER_APP_NAME"))

    if running_in_azure:
        sql_server = os.getenv("SQL_SERVERNAME")
        sql_database = os.getenv("SQL_DATABASENAME")    
        sql_port = os.getenv("SQL_PORT", "1433")
        if not sql_server or not sql_database:
            raise RuntimeError("Missing SQL_SERVERNAME or SQL_DATABASENAME environment variable for Azure.")
        odbc_params = (
            "Driver={ODBC Driver 18 for SQL Server};"
            f"Server=tcp:{sql_server},{sql_port};"
            f"Database={sql_database};"
            "Authentication=ActiveDirectoryMsi;"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
        )
            # user-assigned managed identity
        msi_client_id = os.getenv("AZURE_CLIENT_ID")
        if msi_client_id:
            odbc_params += f";MsiClientId={msi_client_id}"

    else: """
    sql_username = os.getenv("SQL-USERNAME")
    sql_password = os.getenv("SQL-PASSWORD")
    if not sql_username or not sql_password:
        cfg = load_config()
        sql_username = cfg["SQL-USERNAME"]
        sql_password = cfg["SQL-PASSWORD"]

    sql_servername = os.getenv("SQL_SERVERNAME")
    sql_databasename = os.getenv("SQL_DATABASENAME")
    sql_port = os.getenv("SQL_PORT", "1433")
    if not all([sql_username, sql_password, sql_servername, sql_databasename]):
        raise RuntimeError("Missing one or more required SQL environment variables for local connection.")
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
    safe_odbc_params = odbc_params.replace(f"Pwd={os.getenv('SQL_PASSWORD', '')};", "Pwd=****;")
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

