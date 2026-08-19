"""Build the Jaya Jaya Institut Metabase dashboard via the Metabase API.

Prerequisites
-------------
1. `python load_dashboard_db.py` has produced `students.db`.
2. Metabase is running with that file mounted, e.g.

       docker run -d -p 3000:3000 --name metabase \
         -v "/absolute/path/to/students.db:/data/students.db" \
         metabase/metabase

   and http://localhost:3000 answers.

Usage
-----
    python metabase_setup.py

The script is idempotent: it creates the admin account only if Metabase has
not been set up yet, reuses an existing "Jaya Jaya Institut" database
connection, and updates cards/dashboards it created on an earlier run.
Standard library only - no extra pip installs.
"""
import json
import sys
import time
import urllib.error
import urllib.request

HOST = "http://localhost:3000"
EMAIL = "root@mail.com"
PASSWORD = "root123"
FIRST, LAST = "Georgius", "Bintang"
SITE_NAME = "Jaya Jaya Institut"

DB_NAME = "Jaya Jaya Institut"
DB_PATH_IN_CONTAINER = "/data/students.db"
DASHBOARD_NAME = "Jaya Jaya Institut - Student Monitoring"

session_token = None


# --------------------------------------------------------------- http utils
def api(method, path, payload=None, expect_json=True):
    url = "{}/api/{}".format(HOST, path.lstrip("/"))
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if session_token:
        req.add_header("X-Metabase-Session", session_token)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:800]
        raise RuntimeError(
            "{} {} -> HTTP {}: {}".format(method, path, e.code, detail)) from None
    except urllib.error.URLError as e:
        raise RuntimeError(
            "cannot reach Metabase at {} ({}). Is the container running?"
            .format(HOST, e.reason)) from None
    if not expect_json or not body:
        return None
    return json.loads(body)


def wait_for_metabase(timeout=300):
    print("Waiting for Metabase at {} ...".format(HOST), end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            props = api("GET", "session/properties")
            print(" up.")
            return props
        except RuntimeError:
            print(".", end="", flush=True)
            time.sleep(5)
    sys.exit("\nMetabase did not become ready within {}s.".format(timeout))


# ------------------------------------------------------------- setup / login
def ensure_admin(props):
    global session_token
    if props.get("has-user-setup"):
        print("Admin already exists - logging in.")
    else:
        token = props.get("setup-token")
        if not token:
            sys.exit("Metabase reports no admin and no setup token; "
                     "finish setup manually at " + HOST)
        print("Creating admin {} ...".format(EMAIL))
        res = api("POST", "setup", {
            "token": token,
            "user": {"first_name": FIRST, "last_name": LAST, "email": EMAIL,
                     "password": PASSWORD, "site_name": SITE_NAME},
            "prefs": {"site_name": SITE_NAME, "site_locale": "en",
                      "allow_tracking": False},
        })
        if isinstance(res, dict) and res.get("id"):
            session_token = res["id"]
            return
    session_token = api("POST", "session",
                        {"username": EMAIL, "password": PASSWORD})["id"]
    print("Logged in.")


# ------------------------------------------------------------------ database
def ensure_database():
    existing = api("GET", "database")
    items = existing["data"] if isinstance(existing, dict) else existing
    for db in items:
        if db["name"] == DB_NAME:
            print("Reusing database '{}' (id={}).".format(DB_NAME, db["id"]))
            return db["id"]
    print("Adding SQLite database '{}' -> {} ...".format(
        DB_NAME, DB_PATH_IN_CONTAINER))
    db = api("POST", "database", {
        "engine": "sqlite",
        "name": DB_NAME,
        "details": {"db": DB_PATH_IN_CONTAINER, "advanced-options": False},
        "is_full_sync": True,
    })
    return db["id"]


def wait_for_sync(db_id, timeout=180):
    print("Syncing schema ...", end="", flush=True)
    try:
        api("POST", "database/{}/sync_schema".format(db_id), {},
            expect_json=False)
    except RuntimeError:
        pass
    deadline = time.time() + timeout
    while time.time() < deadline:
        meta = api("GET", "database/{}/metadata".format(db_id))
        tables = [t for t in meta.get("tables", []) if t["name"] == "students"]
        if tables and tables[0].get("fields"):
            print(" done ({} fields on 'students').".format(
                len(tables[0]["fields"])))
            return
        print(".", end="", flush=True)
        time.sleep(5)
    sys.exit("\nTable 'students' never appeared. Check that students.db is "
             "mounted at {} inside the container.".format(DB_PATH_IN_CONTAINER))


# --------------------------------------------------------------------- cards
def card(name, sql, display, description="", viz=None, size=(6, 5)):
    return {"name": name, "sql": sql.strip(), "display": display,
            "description": description, "viz": viz or {}, "size": size}


BAR_VIZ = {"graph.dimensions": ["label"],
           "graph.metrics": ["dropout_rate_pct"],
           "graph.x_axis.title_text": "",
           "graph.y_axis.title_text": "Dropout rate (%)",
           "graph.show_values": True}

RISK_HISTOGRAM_SQL = """
SELECT CAST(dropout_risk_score * 10 AS INT) / 10.0 AS risk_bucket,
       COUNT(*) AS jumlah_siswa
FROM students
WHERE status = 'Enrolled'
GROUP BY risk_bucket
ORDER BY risk_bucket
"""

HIGH_RISK_TABLE_SQL = """
SELECT course, gender, age_group, tuition_up_to_date, debtor,
       scholarship_holder, units_1st_sem_approved, units_2nd_sem_approved,
       grade_2nd_sem, dropout_risk_score
FROM students
WHERE status = 'Enrolled' AND dropout_risk_score > 0.6
ORDER BY dropout_risk_score DESC
"""

CARDS = [
    # ---- KPI row ----------------------------------------------------------
    card("Total Siswa",
         "SELECT COUNT(*) AS total_siswa FROM students",
         "scalar", "Jumlah seluruh siswa dalam dataset.", None, (6, 3)),
    card("Jumlah Dropout",
         "SELECT SUM(is_dropout) AS jumlah_dropout FROM students",
         "scalar", "Jumlah siswa berstatus Dropout.", None, (6, 3)),
    card("Persentase Dropout",
         "SELECT ROUND(AVG(is_dropout) * 100, 1) AS dropout_rate_pct "
         "FROM students",
         "scalar", "Dropout rate keseluruhan (%).",
         {"column_settings":
          {'["name","dropout_rate_pct"]': {"suffix": " %"}}}, (6, 3)),
    card("Rata-rata Skor Risiko - Siswa Enrolled",
         "SELECT ROUND(AVG(dropout_risk_score), 3) AS avg_risk_score "
         "FROM students WHERE status = 'Enrolled'",
         "scalar",
         "Rata-rata dropout_risk_score dari model untuk siswa yang masih aktif.",
         None, (6, 3)),

    # ---- distribution -----------------------------------------------------
    card("Distribusi Status Siswa",
         "SELECT status AS label, COUNT(*) AS jumlah_siswa "
         "FROM students GROUP BY status ORDER BY jumlah_siswa DESC",
         "pie", "Komposisi Dropout / Enrolled / Graduate.",
         {"pie.dimension": "label", "pie.metric": "jumlah_siswa"}, (12, 6)),
    card("Dropout Rate per Program Studi",
         "SELECT course AS label, COUNT(*) AS jumlah_siswa, "
         "ROUND(AVG(is_dropout) * 100, 1) AS dropout_rate_pct "
         "FROM students GROUP BY course ORDER BY dropout_rate_pct DESC",
         "row", "Program studi diurutkan dari dropout rate tertinggi.",
         {"graph.dimensions": ["label"],
          "graph.metrics": ["dropout_rate_pct"],
          "graph.show_values": True}, (12, 6)),

    # ---- dropout rate breakdowns -----------------------------------------
    card("Dropout Rate per Status Pembayaran",
         "SELECT tuition_up_to_date AS label, COUNT(*) AS jumlah_siswa, "
         "ROUND(AVG(is_dropout) * 100, 1) AS dropout_rate_pct "
         "FROM students GROUP BY tuition_up_to_date "
         "ORDER BY dropout_rate_pct DESC",
         "bar", "Biaya kuliah lancar (Yes) vs menunggak (No).",
         BAR_VIZ, (8, 5)),
    card("Dropout Rate per Status Beasiswa",
         "SELECT scholarship_holder AS label, COUNT(*) AS jumlah_siswa, "
         "ROUND(AVG(is_dropout) * 100, 1) AS dropout_rate_pct "
         "FROM students GROUP BY scholarship_holder "
         "ORDER BY dropout_rate_pct DESC",
         "bar", "Penerima beasiswa vs bukan penerima.", BAR_VIZ, (8, 5)),
    card("Dropout Rate per Status Debtor",
         "SELECT debtor AS label, COUNT(*) AS jumlah_siswa, "
         "ROUND(AVG(is_dropout) * 100, 1) AS dropout_rate_pct "
         "FROM students GROUP BY debtor ORDER BY dropout_rate_pct DESC",
         "bar", "Siswa dengan tunggakan vs tanpa tunggakan.", BAR_VIZ, (8, 5)),
    card("Dropout Rate per Kelompok Usia",
         "SELECT age_group AS label, COUNT(*) AS jumlah_siswa, "
         "ROUND(AVG(is_dropout) * 100, 1) AS dropout_rate_pct "
         "FROM students GROUP BY age_group ORDER BY label",
         "bar", "Dropout rate menurut usia saat mendaftar.", BAR_VIZ, (12, 5)),
    card("Dropout Rate per Gender",
         "SELECT gender AS label, COUNT(*) AS jumlah_siswa, "
         "ROUND(AVG(is_dropout) * 100, 1) AS dropout_rate_pct "
         "FROM students GROUP BY gender ORDER BY dropout_rate_pct DESC",
         "bar", "Dropout rate menurut gender.", BAR_VIZ, (12, 5)),

    # ---- academic performance --------------------------------------------
    card("Rata-rata SKS Lulus Semester 1-2 per Status",
         "SELECT status AS label, "
         "ROUND(AVG(units_2nd_sem_approved), 2) AS avg_units_2nd_sem_approved, "
         "ROUND(AVG(units_1st_sem_approved), 2) AS avg_units_1st_sem_approved "
         "FROM students GROUP BY status "
         "ORDER BY avg_units_2nd_sem_approved DESC",
         "bar",
         "Perbandingan performa akademik semester awal antar status siswa.",
         {"graph.dimensions": ["label"],
          "graph.metrics": ["avg_units_2nd_sem_approved",
                            "avg_units_1st_sem_approved"],
          "graph.y_axis.title_text": "Rata-rata SKS lulus",
          "graph.show_values": True}, (12, 6)),

    # ---- risk monitoring --------------------------------------------------
    card("Distribusi Skor Risiko - Siswa Enrolled",
         RISK_HISTOGRAM_SQL, "bar",
         "Histogram dropout_risk_score (bin 0,1) untuk siswa yang masih aktif.",
         {"graph.dimensions": ["risk_bucket"],
          "graph.metrics": ["jumlah_siswa"],
          "graph.x_axis.title_text": "Skor risiko dropout",
          "graph.y_axis.title_text": "Jumlah siswa",
          "graph.show_values": True}, (12, 6)),
    card("Siswa Enrolled Berisiko Tinggi (skor > 0,6)",
         HIGH_RISK_TABLE_SQL, "table",
         "Daftar prioritas bimbingan khusus: siswa aktif dengan skor "
         "risiko di atas 0,6.",
         None, (24, 8)),
]


def create_cards(db_id):
    existing = {c["name"]: c["id"] for c in (api("GET", "card") or [])}
    created = []
    for spec in CARDS:
        payload = {
            "name": spec["name"],
            "description": spec["description"],
            "display": spec["display"],
            "visualization_settings": spec["viz"],
            "collection_id": None,          # root collection
            "dataset_query": {
                "type": "native",
                "database": db_id,
                "native": {"query": spec["sql"], "template-tags": {}},
            },
        }
        if spec["name"] in existing:
            cid = existing[spec["name"]]
            api("PUT", "card/{}".format(cid), payload)
            print("  updated card: {}".format(spec["name"]))
        else:
            cid = api("POST", "card", payload)["id"]
            print("  created card: {}".format(spec["name"]))
        created.append((cid, spec))
    return created


# ----------------------------------------------------------------- dashboard
def layout(cards):
    """Place cards on Metabase's 24-column grid, row by row."""
    dashcards, col, row, row_h = [], 0, 0, 0
    for i, (cid, spec) in enumerate(cards):
        w, h = spec["size"]
        if col + w > 24:
            row += row_h
            col, row_h = 0, 0
        dashcards.append({
            "id": -(i + 1), "card_id": cid,
            "row": row, "col": col, "size_x": w, "size_y": h,
            "parameter_mappings": [], "visualization_settings": {},
        })
        col += w
        row_h = max(row_h, h)
    return dashcards


def build_dashboard(cards):
    dash_id = None
    for d in (api("GET", "dashboard") or []):
        if d["name"] == DASHBOARD_NAME and not d.get("archived"):
            dash_id = d["id"]
            print("Reusing dashboard (id={}).".format(dash_id))
            break
    if dash_id is None:
        dash_id = api("POST", "dashboard", {
            "name": DASHBOARD_NAME,
            "description": "Monitoring performa siswa & deteksi dini dropout "
                           "- Georgius Bintang (Georgius_bintang).",
            "collection_id": None,
        })["id"]
        print("Created dashboard (id={}).".format(dash_id))

    dashcards = layout(cards)
    try:
        api("PUT", "dashboard/{}".format(dash_id), {"dashcards": dashcards})
    except RuntimeError as e:
        print("  (dashcards PUT failed: {}\n   falling back to per-card POST)"
              .format(e))
        for dc in dashcards:
            api("POST", "dashboard/{}/cards".format(dash_id), {
                "cardId": dc["card_id"], "row": dc["row"], "col": dc["col"],
                "size_x": dc["size_x"], "size_y": dc["size_y"]})
    print("Placed {} cards on the dashboard.".format(len(dashcards)))
    return dash_id


def main():
    props = wait_for_metabase()
    ensure_admin(props)
    db_id = ensure_database()
    wait_for_sync(db_id)
    print("Creating questions ...")
    cards = create_cards(db_id)
    dash_id = build_dashboard(cards)
    print("\nDone. Open the dashboard at:")
    print("  {}/dashboard/{}".format(HOST, dash_id))
    print("\nNext steps:")
    print("  1. Screenshot it as Georgius_bintang-dashboard.png")
    print("  2. docker cp metabase:/metabase.db/metabase.db.mv.db ./")


if __name__ == "__main__":
    main()
