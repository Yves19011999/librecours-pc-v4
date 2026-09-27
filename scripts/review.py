import sqlite3
from pathlib import Path
import argparse

BASE = Path(__file__).resolve().parents[1]
DB = BASE / "data/courses.db"

p = argparse.ArgumentParser()
p.add_argument("--publish", type=int)
p.add_argument("--reject", type=int)
args = p.parse_args()

conn = sqlite3.connect(DB)
if args.publish:
    conn.execute("UPDATE courses SET status='published' WHERE id=? AND status='pending'", (args.publish,))
elif args.reject:
    conn.execute("UPDATE courses SET status='rejected' WHERE id=? AND status='pending'", (args.reject,))
else:
    rows = conn.execute("""SELECT id,title,level,subject,license,source_url
                           FROM courses WHERE status='pending'
                           ORDER BY created_at DESC""").fetchall()
    for r in rows:
        print(f"[{r[0]}] {r[2]} | {r[3]} | {r[1]}\n    Licence: {r[4]}\n    Source: {r[5]}\n")
conn.commit()
conn.close()
