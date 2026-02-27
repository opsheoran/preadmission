import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key'
    # Default to SQL Server HAU_PreAdmission. Adjust credentials as needed.
    # Driver could be 'ODBC Driver 17 for SQL Server'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mssql+pyodbc://localhost/HAU_Preadmission_Client_Backup?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
