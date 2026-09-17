import os
from pathlib import Path
from urllib.parse import quote_plus

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"

class Config:
    SECRET_KEY = "change-this-secret-key-in-production"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---------------------------------------------------------
    # Direct XAMPP MySQL Configuration (No .env required)
    # ---------------------------------------------------------
    db_user = quote_plus("root")
    db_password = quote_plus("")  # XAMPP default is empty password
    db_host = "127.0.0.1"
    db_port = "3306"
    db_name = "ez_lab_db"         # Updated to the new DB name
    
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )