# create_admin_db.py
import sqlite3
from pathlib import Path

Path(".").mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect("admin.db")
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS admins (admin_id TEXT PRIMARY KEY, password TEXT)")
cur.execute("INSERT OR IGNORE INTO admins (admin_id, password) VALUES (?,?)", ("admin","12345"))
conn.commit()
conn.close()
print("Created admin.db with default admin / 12345")
