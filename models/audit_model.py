from database import get_connection

from database import get_connection

def generate_log_id():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT MAX(logID)

        FROM AuditLog

    """)

    row = cursor.fetchone()

    conn.close()

    if row[0] is None:

        return "AL0001"

    number = int(row[0][2:])

    return f"AL{number+1:04d}"

def write_log(userID, action, details):

    conn = get_connection()

    cursor = conn.cursor()

    logID = generate_log_id()

    cursor.execute("""

        INSERT INTO AuditLog

        (logID,userID,action,details)

        VALUES

        (?,?,?,?)

    """,
    (
        logID,
        userID,
        action,
        details
    ))

    conn.commit()

    conn.close()