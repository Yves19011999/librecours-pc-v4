import os, sqlite3, secrets
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, abort, session
from dotenv import load_dotenv

load_dotenv()
BASE = Path(__file__).resolve().parent
DB = BASE / "data" / "courses.db"
DOWNLOAD_DIR = BASE / os.getenv("DOWNLOAD_DIR", "data/courses")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS courses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      level TEXT NOT NULL,
      subject TEXT NOT NULL,
      chapter TEXT DEFAULT '',
      description TEXT DEFAULT '',
      source_url TEXT NOT NULL,
      author TEXT DEFAULT '',
      license TEXT NOT NULL,
      file_name TEXT,
      status TEXT NOT NULL DEFAULT 'pending',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    level = request.args.get("level", "").strip()
    subject = request.args.get("subject", "").strip()
    sql = "SELECT * FROM courses WHERE status='published'"
    args = []
    if q:
        sql += " AND (title LIKE ? OR chapter LIKE ? OR description LIKE ?)"
        like = f"%{q}%"
        args += [like, like, like]
    if level:
        sql += " AND level=?"; args.append(level)
    if subject:
        sql += " AND subject=?"; args.append(subject)
    sql += " ORDER BY created_at DESC"
    conn = db()
    courses = conn.execute(sql, args).fetchall()
    levels = [r["level"] for r in conn.execute(
        "SELECT DISTINCT level FROM courses WHERE status='published' ORDER BY level").fetchall()]
    conn.close()
    return render_template("index.html", courses=courses, levels=levels, q=q, level=level, subject=subject)

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    conn = db()
    rows = conn.execute("""SELECT id,title,level,subject FROM courses
                           WHERE status='published' AND title LIKE ?
                           ORDER BY title LIMIT 10""", (f"%{q}%",)).fetchall()
    conn.close()
    return {"results": [dict(r) for r in rows]}

@app.route("/cours/<int:course_id>")
def course(course_id):
    conn = db()
    item = conn.execute("SELECT * FROM courses WHERE id=? AND status='published'", (course_id,)).fetchone()
    conn.close()
    if not item: abort(404)
    return render_template("course.html", course=item)

@app.route("/download/<int:course_id>")
def download(course_id):
    conn = db()
    item = conn.execute("SELECT * FROM courses WHERE id=? AND status='published'", (course_id,)).fetchone()
    conn.close()
    if not item or not item["file_name"]:
        abort(404)
    return send_from_directory(DOWNLOAD_DIR, item["file_name"], as_attachment=True)

def admin_required():
    return session.get("admin") is True

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if secrets.compare_digest(request.form.get("password",""), os.getenv("ADMIN_PASSWORD","")):
            session["admin"] = True
            return redirect(url_for("admin"))
        return render_template("login.html", error="Mot de passe incorrect.")
    return render_template("login.html", error=None)

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/sources")
def sources_page():
    import json
    sources = json.loads((BASE / "data" / "sources.json").read_text(encoding="utf-8"))
    return render_template("sources.html", sources=sources)

@app.route("/admin")
def admin():
    if not admin_required(): return redirect(url_for("admin_login"))
    conn = db()
    pending = conn.execute("SELECT * FROM courses WHERE status='pending' ORDER BY created_at DESC").fetchall()
    published = conn.execute("SELECT * FROM courses WHERE status='published' ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("admin.html", pending=pending, published=published)

@app.post("/admin/course/<int:course_id>/<action>")
def admin_action(course_id, action):
    if not admin_required(): abort(403)
    if action not in ("publish", "reject"): abort(400)
    status = "published" if action == "publish" else "rejected"
    conn = db()
    conn.execute("UPDATE courses SET status=? WHERE id=?", (status, course_id))
    conn.commit(); conn.close()
    return redirect(url_for("admin"))

@app.post("/admin/add")
def admin_add():
    if not admin_required(): abort(403)
    form = request.form
    if not form.get("license","").strip():
        return "Licence obligatoire", 400
    conn = db()
    conn.execute("""INSERT INTO courses
      (title,level,subject,chapter,description,source_url,author,license,status)
      VALUES (?,?,?,?,?,?,?,?,?)""",
      (form["title"], form["level"], form["subject"], form.get("chapter",""),
       form.get("description",""), form["source_url"], form.get("author",""),
       form["license"], "published"))
    conn.commit(); conn.close()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
