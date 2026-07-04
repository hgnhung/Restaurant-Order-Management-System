# models/audit_model.py
from database import get_connection

def generate_log_id():
    conn = get_connection()
    cursor = conn.cursor()
    # Lấy tất cả các mã logID bắt đầu bằng 'AL' để tự lọc bằng Python cho an toàn
    cursor.execute("SELECT logID FROM AuditLog WHERE logID LIKE 'AL%'")
    rows = cursor.fetchall()
    conn.close()

    max_number = 0
    for row in rows:
        if row[0]:
            try:
                # Trích xuất phần số từ ký tự thứ 2 trở đi (bỏ chữ 'AL')
                num_part = int(row[0][2:])
                if num_part > max_number:
                    max_number = num_part
            except ValueError:
                # BỎ QUA: Nếu chuỗi còn lại là chữ rác (như 'VSHN') thì bỏ qua không ép kiểu để tránh crash
                continue

    return f"AL{max_number + 1:04d}"

def write_log(userID, action, details):
    conn = get_connection()
    cursor = conn.cursor()
    logID = generate_log_id()
    cursor.execute("""
        INSERT INTO AuditLog
        (logID, userID, action, details)
        VALUES
        (?,?,?,?)
    """, (logID, userID, action, details))
    conn.commit()
    conn.close()