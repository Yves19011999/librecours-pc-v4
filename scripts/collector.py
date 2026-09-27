import os, re, sqlite3, hashlib, time
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote_plus
import requests
from bs4 import BeautifulSoup
from license_verifier import verify_license

BASE = Path(__file__).resolve().parents[1]
DB = BASE / "data" / "courses.db"
DOWNLOAD_DIR = BASE / os.getenv("DOWNLOAD_DIR", "data/courses")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
UA = "LibreCoursPC/4.0 (+educational-resource-indexer)"

LEVELS = ["6e", "5e", "4e", "3e", "Seconde", "Première", "Terminale"]
SUBJECTS = ["Physique", "Chimie"]
MAX_PDF_BYTES = 30 * 1024 * 1024

# We only auto-download when the source page explicitly exposes a reusable licence.
# NC resources are indexed as links for review; they are not copied automatically.
LICENCE_RE = [
    ("CC BY-NC-SA", r"creativecommons\.org/licenses/by-nc-sa/|cc[-\s]?by[-\s]?nc[-\s]?sa"),
    ("CC BY-NC", r"creativecommons\.org/licenses/by-nc/|cc[-\s]?by[-\s]?nc"),
    ("CC BY-SA", r"creativecommons\.org/licenses/by-sa/|cc[-\s]?by[-\s]?sa"),
    ("CC BY", r"creativecommons\.org/licenses/by/|cc[-\s]?by(?:[-\s]?4\.0)?"),
    ("CC0", r"creativecommons\.org/publicdomain/zero/|cc0"),
    ("Public Domain", r"public\s+domain|domaine\s+public"),
]

def detect_license(text):
    t = (text or "").lower()
    for name, pattern in LICENCE_RE:
        if re.search(pattern, t):
            return name
    return None

def is_redistributable(lic):
    return lic in {"CC BY", "CC BY-SA", "CC0", "Public Domain"}

def classify_level(text):
    t = text.lower()
    aliases = [
        ("Terminale", ["terminale", "grade 12", "12th"]),
        ("Première", ["première", "premiere", "grade 11", "11th"]),
        ("Seconde", ["seconde", "grade 10", "10th"]),
        ("3e", ["3e", "3ème", "3eme", "grade 9", "9th"]),
        ("4e", ["4e", "4ème", "4eme", "grade 8", "8th"]),
        ("5e", ["5e", "5ème", "5eme", "grade 7", "7th"]),
        ("6e", ["6e", "6ème", "6eme", "grade 6", "6th"]),
    ]
    for level, words in aliases:
        if any(w in t for w in words):
            return level
    return "À classer"

def classify_subject(text):
    t = text.lower()
    if "chimie" in t or "chemistry" in t:
        return "Chimie"
    if "physique" in t or "physics" in t:
        return "Physique"
    return "Physique-Chimie"

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS courses (
      id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, level TEXT NOT NULL,
      subject TEXT NOT NULL, chapter TEXT DEFAULT '', description TEXT DEFAULT '',
      source_url TEXT NOT NULL UNIQUE, author TEXT DEFAULT '', license TEXT NOT NULL,
      file_name TEXT, status TEXT NOT NULL DEFAULT 'pending',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    return conn

def fetch(url, stream=False):
    return requests.get(url, timeout=25, headers={"User-Agent": UA}, stream=stream)

def page_metadata(url):
    r = fetch(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    author = ""
    m = soup.find("meta", attrs={"name": re.compile("^author$", re.I)})
    if m: author = m.get("content", "")
    lic = detect_license(text + " " + " ".join(a.get("href","") for a in soup.find_all("a", href=True)))
    return soup, title, author, lic

def save(conn, title, level, subject, source, lic, author="", file_name=None, status="pending"):
    try:
        result = verify_license(title, lic, source)
        conn.execute("""INSERT INTO courses
        (title,level,subject,source_url,author,license,file_name,status,ai_score,ai_decision,ai_reason,ai_checked_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",
        (title[:250], level, subject, source, author[:250], lic, file_name, status, result["score"], result["decision"], result["reason"]))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def maybe_download_pdf(pdf_url, lic):
    if not is_redistributable(lic):
        return None
    try:
        r = fetch(pdf_url, stream=True)
        ctype = r.headers.get("content-type","").lower()
        if "pdf" not in ctype and not pdf_url.lower().endswith(".pdf"):
            return None
        length = int(r.headers.get("content-length","0") or 0)
        if length and length > MAX_PDF_BYTES:
            return None
        data = bytearray()
        for chunk in r.iter_content(1024 * 256):
            data.extend(chunk)
            if len(data) > MAX_PDF_BYTES:
                return None
        if not data.startswith(b"%PDF"):
            return None
        digest = hashlib.sha256(data).hexdigest()
        name = digest + ".pdf"
        path = DOWNLOAD_DIR / name
        if not path.exists():
            path.write_bytes(data)
        return name
    except Exception as exc:
        print("PDF skipped:", pdf_url, exc)
        return None

def crawl_page(conn, url, source_name, forced_level=None, forced_subject=None):
    try:
        soup, title, author, lic = page_metadata(url)
    except Exception as exc:
        print("Page skipped:", url, exc)
        return 0

    if not lic:
        return 0

    level = forced_level or classify_level(title + " " + soup.get_text(" ", strip=True)[:6000])
    subject = forced_subject or classify_subject(title + " " + soup.get_text(" ", strip=True)[:6000])
    count = 0

    # Index the page itself.
    if len(title) >= 4:
        count += save(conn, title, level, subject, url, lic, author)

    # For permissive licences, download linked PDFs. For NC, keep a source link only.
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"])
        if urlparse(href).scheme not in ("http", "https"):
            continue
        label = a.get_text(" ", strip=True) or href.rsplit("/",1)[-1]
        if not href.lower().endswith(".pdf"):
            continue
        file_name = maybe_download_pdf(href, lic)
        count += save(conn, label[:250], level, subject, href, lic, author, file_name)
    return count

def google_discovery(conn, query, source_name):
    # Discovery only. Search results are followed and individually checked for licence.
    url = "https://www.google.com/search?q=" + quote_plus(query)
    try:
        r = fetch(url)
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return 0
    urls = []
    for a in soup.select("a[href]"):
        h = a["href"]
        if h.startswith("http") and not "google.com/search" in h:
            urls.append(h)
    n = 0
    for u in list(dict.fromkeys(urls))[:12]:
        try:
            n += crawl_page(conn, u, source_name)
        except Exception:
            pass
        time.sleep(0.2)
    return n

def main():
    conn = init_db()
    total = 0
    for level in LEVELS:
        for subject in SUBJECTS:
            query = f'"{level}" "{subject}" (cours OR course) (Creative Commons OR "CC BY" OR OER)'
            print("Recherche:", query)
            total += google_discovery(conn, query, "Web discovery")
            time.sleep(0.5)
    conn.close()
    print("Collecte terminée. Nouvelles entrées:", total)

if __name__ == "__main__":
    main()
