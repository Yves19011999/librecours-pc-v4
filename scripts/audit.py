import sqlite3, hashlib
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DB = BASE/"data/courses.db"
PDFS = BASE/"data/courses"

conn = sqlite3.connect(DB)
rows = conn.execute("SELECT id,title,file_name FROM courses WHERE file_name IS NOT NULL").fetchall()
seen = {}
duplicates = []
for rid,title,name in rows:
    p = PDFS/name
    if not p.exists(): continue
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h in seen:
        duplicates.append((rid,title,seen[h]))
    else:
        seen[h] = (rid,title)
print("PDF vérifiés:", len(rows))
print("Doublons exacts:", len(duplicates))
for x in duplicates:
    print(x)
conn.close()
