import pymysql
import pymysql.cursors
from config import Config

def get_db_connection():
    """Helper function to get a raw database connection using pymysql and config.py"""
    return pymysql.connect(
        host=Config.db_host,
        user=Config.db_user,
        password=Config.db_password,
        database=Config.db_name,
        port=int(Config.db_port),
        cursorclass=pymysql.cursors.DictCursor  # Ensures queries return dictionaries
    )