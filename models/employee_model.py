from database import get_connection


def get_all_employee():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            userID,
            fullName,
            position
        FROM Employee
        WHERE isActive = 1
        ORDER BY fullName
    """)

    employees = cursor.fetchall()

    conn.close()

    return employees

def check_login(userID, pin):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM Employee

        WHERE userID=?

        AND pin=?

        AND isActive=1

    """,(userID,pin))

    employee = cursor.fetchone()

    conn.close()

    return employee

def add_audit(userID, action):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""

        INSERT INTO AuditLog
        (logID,userID,action)

        VALUES
        (?,?,?)

    """,
    (
        create_log_id(),
        userID,
        action
    ))

    conn.commit()

    conn.close()