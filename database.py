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

        cursor = conn.cursor()

        cursor.execute("SELECT DB_NAME()")
        print("Current Database:", cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM Invoice")
        print("Invoice Count:", cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM Payment")
        print("Payment Count:", cursor.fetchone()[0])

        cursor.close()

        return conn

    except Exception as e:

        print("Database connection failed!")
        print(e)

        return None