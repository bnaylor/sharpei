import sqlite3

def check_data():
    conn = sqlite3.connect('sharpei.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, priority, position FROM tasks")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    conn.close()

if __name__ == "__main__":
    check_data()
