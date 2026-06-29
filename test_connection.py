from database import get_connection

conn = get_connection()

if conn:
    print("Connected successfully!")

    cursor = conn.cursor()

    cursor.execute("SELECT DB_NAME()")

    db = cursor.fetchone()

    print("Current Database:", db[0])

    conn.close()

else:
    print("Connection failed!")