import os

class Config:    
    # Placeholder - actual connection built dynamically in app/__init__.py using Key Vault secrets
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Temporary URI, replaced at runtime
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Disable tracking to save resources
    SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://username:password@cs-datastore.database.windows.net,1433/cs-datastore?driver=ODBC+Driver+17+for+SQL+Server'

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'    

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
    
class TestingConfig(Config):
    TESTING = True
    