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
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, '..', 'service_standards.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", f"sqlite:///{db_path}")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db)

    from app.views import views_bp
    app.register_blueprint(views_bp)

    return app
    

def build_engine():
    conn_str = os.environ["DATABASE_URL"]
    engine = create_engine(
        conn_str,
        pool_pre_ping=True,       # drops stale connections
        pool_recycle=1800,        # recycle every 30 mins
        fast_executemany=True     # faster bulk inserts with pyodbc
    )
    return engine


    
