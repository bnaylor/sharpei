import sqlite3

def migrate():
    conn = sqlite3.connect('sharpei.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN position INTEGER DEFAULT 0")
        print("Successfully added 'position' column.")
    except sqlite3.OperationalError as e:
        print(f"Migration failed (column might already exist): {e}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
