#!/usr/bin/env python3
"""Migration script to add archived column to tasks table."""
import sqlite3

conn = sqlite3.connect('sharpei.db')
cursor = conn.cursor()

# Check if column already exists
cursor.execute("PRAGMA table_info(tasks)")
columns = [col[1] for col in cursor.fetchall()]

if 'archived' not in columns:
    cursor.execute("ALTER TABLE tasks ADD COLUMN archived BOOLEAN DEFAULT 0")
    conn.commit()
    print("Added 'archived' column to tasks table")
else:
    print("'archived' column already exists")

conn.close()
