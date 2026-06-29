import pyodbc
from config import Config


def get_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={{{Config.DRIVER}}};"
            f"SERVER={Config.SERVER};"
            f"DATABASE={Config.DATABASE};"
            "Trusted_Connection=yes;"
        )
        return conn

    except Exception as e:
        print("Database connection failed!")
        print(e)
        return None