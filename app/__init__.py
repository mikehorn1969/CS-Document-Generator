from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Tech Debt: my be able to remove
import os, secrets
import dotenv
from sqlalchemy import create_engine

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
    # Base ODBC parameters
     # Choose auth by environment (simple heuristic)
    running_in_azure = bool(os.getenv("WEBSITE_SITE_NAME") or os.getenv("AZURE_CONTAINER_APP_NAME"))

    if running_in_azure:
        sql_server = os.getenv("SQL_SERVERNAME")
        sql_database = os.getenv("SQL_DATABASENAME")    
        sql_port = os.getenv("SQL_PORT", "1433")
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

    else:
        sql_username = os.getenv("SQL_USERNAME")
        sql_password = os.getenv("SQL_PASSWORD")
        sql_servername = os.getenv("SQL_SERVERNAME")
        sql_databasename = os.getenv("SQL_DATABASENAME")
        sql_port = os.getenv("SQL_PORT", "1433")
        odbc_params = (
            "Driver=ODBC Driver 18 for SQL Server;"
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

    return create_engine(
        "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc_params),
        pool_pre_ping=True,
        pool_recycle=1800,
        fast_executemany=True,
    )


    
    
    

""" def build_engine():
    conn_str = os.environ["DATABASE_URL"]
    engine = create_engine(
        conn_str,
        pool_pre_ping=True,       # drops stale connections
        pool_recycle=1800,        # recycle every 30 mins
        fast_executemany=True     # faster bulk inserts with pyodbc
    )

    return engine """