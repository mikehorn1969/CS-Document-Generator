import os

class Config:    
    SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://username:password@cs-datastore.database.windows.net,1433/cs-datastore?driver=ODBC+Driver+17+for+SQL+Server'
    SQLALCHEMY_TRACK_MODIFICATIONS = False # Disable tracking to save resources

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'    

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
    
class TestingConfig(Config):
    TESTING = True
    