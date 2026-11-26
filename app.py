import hmac
import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from jinja2 import FileSystemLoader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
)
app.jinja_loader = FileSystemLoader(
    [
        os.path.join(BASE_DIR, "templates"),
        os.path.join(BASE_DIR, "Templates"),
        os.path.join(BASE_DIR, "template"),
        BASE_DIR,
    ]
)

app.secret_key = os.environ.get("SECRET_KEY") or "lifecircle-change-this-secret-key"
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "data.db"))

DEFAULT_PRODUCTS = [
    {"id": "bp", "nameBn": "ডিজিটাল অটোমেটিক বিপি মেশিন (Upper Arm)", "category": "bp", "warranty": "২ বছর অফিসিয়াল ওয়ারেন্টি", "descriptionBn": "রক্তচাপ ও পালস রেট নিখুঁতভাবে পরিমাপের জন্য বড় এলসিডি স্ক্রিনযুক্ত ডিজিটাল বিপি মেশিন। অনিয়মিত হৃদস্পন্দন শনাক্তকরণ ও ৯০টি রিডিং সেভ রাখার সুবিধা।", "imageUrl": ""},
    {"id": "diabetes", "nameBn": "স্মার্ট ডায়াবেটিস ব্লাড গ্লুকোজ মিটার কিট", "category": "diabetes", "warranty": "লাইফটাইম রিপ্লেসমেন্ট ওয়ারেন্টি", "descriptionBn": "মাত্র ৫ সেকেন্ডে ০.৫ মাইক্রোলিটার রক্তের মাধ্যমে নির্ভুল সুগার লেভেল পরীক্ষা। খালি পেট ও ভরা পেটের আলাদা মার্কিং এবং ৫০০টি টেস্ট মেমোরি।", "imageUrl": ""},
    {"id": "thermo-ir", "nameBn": "কন্ট্যাক্টলেস ইনফ্রারেড ডিজিটাল থার্মোমিটার", "category": "thermometer", "warranty": "১ বছর ওয়ারেন্টি", "descriptionBn": "স্পর্শ ছাড়াই ১ সেকেন্ডে কপাল থেকে শরীরের সঠিক তাপমাত্রা নির্ণয়। শিশু ও বয়স্কদের জ্বর মাপার জন্য নিরাপদ।", "imageUrl": ""},
    {"id": "thermo-analog", "nameBn": "অ্যানালগ ক্লিনিক্যাল থার্মোমিটার (Analog Thermometer)", "category": "thermometer", "warranty": "সঠিক স্কেল ক্যালিব্রেটেড", "descriptionBn": "ব্যাটারি ছাড়াই নির্ভুল তাপমাত্রা পরিমাপের জন্য নির্ভরযোগ্য অ্যানালগ ক্লিনিক্যাল থার্মোমিটার। সেলসিয়াস ও ফারেনহাইট উভয় স্কেল ও সুরক্ষিত কেস সহ।", "imageUrl": ""},
    {"id": "oxygen", "nameBn": "মেডিকেল অক্সিজেন কনসেন্ট্রেটর (৫ লিটার)", "category": "oxygen", "warranty": "২ বছর মোটর ও সার্ভিস ওয়ারেন্টি", "descriptionBn": "৯৩% ± ৩% বিশুদ্ধ অক্সিজেন সরবরাহকারী নীরব ৫ লিটার অক্সিজেন কনসেন্ট্রেটর। বিল্ট-ইন নেবুলাইজার ও অ্যালার্ম যুক্ত।", "imageUrl": ""},
    {"id": "bipap", "nameBn": "অটো বাইপ্যাপ মেশিন (BiPAP ST with Humidifier)", "category": "bipap", "warranty": "২ বছর অফিসিয়াল ওয়ারেন্টি", "descriptionBn": "COPD, নিউমোনিয়া পরবর্তী দুর্বলতা ও হাইপারক্যাপনিক রেসপিরেটরি ফেইলিউর রোগীদের শ্বাসযন্ত্র সহায়তাকারী উন্নত বাইপ্যাপ মেশিন।", "imageUrl": ""},
    {"id": "cpap", "nameBn": "অটো সি-প্যাপ মেশিন (Auto-CPAP Sleep Therapy)", "category": "cpap", "warranty": "২ বছর অফিসিয়াল ওয়ারেন্টি", "descriptionBn": "অবস্ট্রাকটিভ স্লিপ অ্যাপনিয়া ও নাক ডাকা দূর করতে স্বয়ংক্রিয় চাপ নিয়ন্ত্রণকারী Auto-CPAP মেশিন এবং নীরব হিউমিডিফায়ার।", "imageUrl": ""},
    {"id": "mask", "nameBn": "সিঙ্গেল এনপিভি মাস্ক (Single NPV / NIV Mask)", "category": "mask", "warranty": "মেডিকেল গ্রেড সিলিকন সিল", "descriptionBn": "BiPAP, CPAP ও NIV মেশিনে ব্যবহারের জন্য নরম সিলিকন কুশনযুক্ত সিঙ্গেল এনপিভি মাস্ক। মুখ ও নাকে নিখুঁত ফিট নিশ্চিত করে।", "imageUrl": ""},
]

DEFAULT_FAQS = [
    {"id": "faq-1", "questionBn": "হোম স্লিপ টেস্ট কীভাবে করা হয়?", "answerBn": "অ্যাপয়েন্টমেন্ট বুক করলে আমাদের টেকনিশিয়ান বাসায় গিয়ে পোর্টেবল স্লিপ টেস্ট যন্ত্র সেট করে দেবেন। পরদিন সকালে যন্ত্র সংগ্রহ করে বিশেষজ্ঞ রিপোর্ট দেওয়া হয়।"},
    {"id": "faq-2", "questionBn": "BiPAP ও CPAP মেশিনের মধ্যে পার্থক্য কী?", "answerBn": "CPAP স্লিপ অ্যাপনিয়া ও নাক ডাকার জন্য স্থির/স্বয়ংক্রিয় চাপ দেয়; আর BiPAP শ্বাস নেওয়া ও ছাড়ার দুটি আলাদা চাপ দেয়, যা COPD ও তীব্র শ্বাসকষ্টে ব্যবহৃত হয়।"},
    {"id": "faq-3", "questionBn": "সিঙ্গেল এনপিভি মাস্ক কীভাবে পরিষ্কার করবেন?", "answerBn": "ব্যবহারের পর কুসুম গরম পানি ও মৃদু সাবান দিয়ে সিলিকন কুশন ধুয়ে বাতাসে শুকিয়ে নিন।"},
    {"id": "faq-4", "questionBn": "যন্ত্রপাতির প্রাপ্যতা ও অর্ডার তথ্য কীভাবে জানব?", "answerBn": "ওয়েবসাইটে কোনো মূল্য প্রদর্শিত হয় না; সরাসরি WhatsApp (01754149749)-এ যোগাযোগ করুন। বিকাশ নম্বর: 01711480987।"},
]

DEFAULT_SETTINGS = {
    "companyName": "lifecircle.bd",
    "tagline": "বিশ্বস্ত মেডিকেল যন্ত্রপাতি ও আধুনিক স্লিপ টেস্ট সেবা",
    "whatsapp": "01754149749",
    "bkash": "01711480987",
    "hours": "শনি - বৃহস্পতি: সকাল ৯টা - রাত ৯টা | জরুরি সাপোর্ট ২৪/৭",
    "address": "আপনার ঠিকানা এখানে লিখুন (ঢাকা, বাংলাদেশ)",
    "sleepLabNote": "ঘুমের মধ্যে নাক ডাকা, দম বন্ধ হয়ে আসা (Sleep Apnea) কিংবা অতিরিক্ত দিনের ঘুমের সমস্যা নির্ণয়ে হোম স্লিপ অ্যাপনিয়া টেস্ট (HSAT) ও ক্লিনিক্যাল পলিসমনোগ্রাফি সুবিধা।",
}


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db():
    conn = get_db()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                nameBn TEXT NOT NULL,
                category TEXT NOT NULL,
                warranty TEXT NOT NULL,
                descriptionBn TEXT NOT NULL,
                imageUrl TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS faqs (
                id TEXT PRIMARY KEY,
                questionBn TEXT NOT NULL,
                answerBn TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                name TEXT DEFAULT '',
                contact TEXT DEFAULT '',
                message TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            for p in DEFAULT_PRODUCTS:
                conn.execute(
                    "INSERT INTO products (id, nameBn, category, warranty, descriptionBn, imageUrl) VALUES (?, ?, ?, ?, ?, ?)",
                    (p["id"], p["nameBn"], p["category"], p["warranty"], p["descriptionBn"], p["imageUrl"]),
                )
        if conn.execute("SELECT COUNT(*) FROM faqs").fetchone()[0] == 0:
            for f in DEFAULT_FAQS:
                conn.execute(
                    "INSERT INTO faqs (id, questionBn, answerBn) VALUES (?, ?, ?)",
                    (f["id"], f["questionBn"], f["answerBn"]),
                )
        for k, v in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (k, v),
            )
    conn.close()


init_db()


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for("admin_page"))
        return fn(*args, **kwargs)

    return wrapper


def build_site_data():
    conn = get_db()
    settings_rows = conn.execute("SELECT key, value FROM settings").fetchall()
    settings = {r["key"]: r["value"] for r in settings_rows}
    products = [dict(r) for r in conn.execute("SELECT * FROM products").fetchall()]
    faqs = [dict(r) for r in conn.execute("SELECT * FROM faqs").fetchall()]
    conn.close()
    return {
        "companyName": settings.get("companyName", DEFAULT_SETTINGS["companyName"]),
        "tagline": settings.get("tagline", DEFAULT_SETTINGS["tagline"]),
        "whatsapp": settings.get("whatsapp", DEFAULT_SETTINGS["whatsapp"]),
        "bkash": settings.get("bkash", DEFAULT_SETTINGS["bkash"]),
        "hours": settings.get("hours", DEFAULT_SETTINGS["hours"]),
        "address": settings.get("address", DEFAULT_SETTINGS["address"]),
        "sleepLabNote": settings.get("sleepLabNote", DEFAULT_SETTINGS["sleepLabNote"]),
        "products": products,
        "faqs": faqs,
    }


def serve_static_fallback(filename, mimetype=None):
    for folder in ["static", "Static", ""]:
        path = os.path.join(BASE_DIR, folder) if folder else BASE_DIR
        full = os.path.join(path, filename)
        if os.path.isfile(full):
            return send_from_directory(path, filename, mimetype=mimetype)
    return ("Not Found", 404)


@app.route("/")
def index():
    return render_template("index.html", site_data=build_site_data())


@app.route("/service-worker.js")
def service_worker():
    return serve_static_fallback("service-worker.js", mimetype="application/javascript")


@app.route("/static/manifest.json")
@app.route("/manifest.json")
def manifest_file():
    return serve_static_fallback("manifest.json", mimetype="application/manifest+json")


@app.route("/api/submissions", methods=["POST"])
def create_submission():
    payload = request.get_json(silent=True) or {}
    sub_type = str(payload.get("type", "inquiry"))[:30]
    name = str(payload.get("name", "")).strip()[:120]
    contact = str(payload.get("contact", "")).strip()[:120]
    message = str(payload.get("message", "")).strip()[:1000]
    if not contact and not message:
        return jsonify({"error": "তথ্য দিন"}), 400
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    conn = get_db()
    with conn:
        cur = conn.execute(
            "INSERT INTO submissions (type, name, contact, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (sub_type, name, contact, message, created_at),
        )
        new_id = cur.lastrowid
    conn.close()
    return jsonify({"ok": True, "id": new_id, "created_at": created_at}), 201


@app.route("/admin", methods=["GET", "POST"])
def admin_page():
    error = ""
    expected_pw = os.environ.get("ADMIN_PASSWORD", "")

    if request.method == "POST":
        action = request.form.get("action", "login")
        if action == "login":
            pw = request.form.get("password", "")
            if not expected_pw:
                error = "Render-এ ADMIN_PASSWORD সেট করা হয়নি।"
            elif hmac.compare_digest(pw, expected_pw):
                session["is_admin"] = True
                return redirect(url_for("admin_page"))
            else:
                error = "ভুল পাসওয়ার্ড দিয়েছেন।"
        elif action == "logout":
            session.clear()
            return redirect(url_for("admin_page"))

    if not session.get("is_admin"):
        return render_template("admin.html", logged_in=False, error=error)

    conn = get_db()
    products = [dict(r) for r in conn.execute("SELECT * FROM products").fetchall()]
    faqs = [dict(r) for r in conn.execute("SELECT * FROM faqs").fetchall()]
    submissions = [
        dict(r)
        for r in conn.execute("SELECT * FROM submissions ORDER BY id DESC LIMIT 200").fetchall()
    ]
    settings = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM settings").fetchall()}
    conn.close()
    return render_template(
        "admin.html",
        logged_in=True,
        products=products,
        faqs=faqs,
        submissions=submissions,
        settings=settings,
        msg=request.args.get("msg", ""),
    )


@app.route("/admin/products/add", methods=["POST"])
@admin_required
def admin_add_product():
    name = request.form.get("nameBn", "").strip()[:140]
    category = request.form.get("category", "bp").strip()[:40]
    warranty = request.form.get("warranty", "অফিসিয়াল ওয়ারেন্টি সহ").strip()[:100]
    desc = request.form.get("descriptionBn", "").strip()[:1000]
    image_data = request.form.get("imageData", "").strip()
    image_url = request.form.get("imageUrl", "").strip()

    final_img = ""
    if image_data.startswith("data:image/"):
        final_img = image_data
    elif image_url.startswith(("https://", "http://")):
        final_img = image_url

    if name and desc:
        pid = f"prod-{int(datetime.now(timezone.utc).timestamp())}"
        conn = get_db()
        with conn:
            conn.execute(
                "INSERT INTO products (id, nameBn, category, warranty, descriptionBn, imageUrl) VALUES (?, ?, ?, ?, ?, ?)",
                (pid, name, category, warranty, desc, final_img),
            )
        conn.close()
    return redirect(url_for("admin_page", msg="নতুন পণ্য যোগ হয়েছে"))


@app.route("/admin/products/delete/<pid>", methods=["POST"])
@admin_required
def admin_delete_product(pid):
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM products WHERE id = ?", (pid,))
    conn.close()
    return redirect(url_for("admin_page", msg="পণ্য মুছে ফেলা হয়েছে"))


@app.route("/admin/faqs/add", methods=["POST"])
@admin_required
def admin_add_faq():
    q = request.form.get("questionBn", "").strip()[:300]
    a = request.form.get("answerBn", "").strip()[:1500]
    if q and a:
        fid = f"faq-{int(datetime.now(timezone.utc).timestamp())}"
        conn = get_db()
        with conn:
            conn.execute("INSERT INTO faqs (id, questionBn, answerBn) VALUES (?, ?, ?)", (fid, q, a))
        conn.close()
    return redirect(url_for("admin_page", msg="FAQ যোগ হয়েছে"))


@app.route("/admin/faqs/delete/<fid>", methods=["POST"])
@admin_required
def admin_delete_faq(fid):
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM faqs WHERE id = ?", (fid,))
    conn.close()
    return redirect(url_for("admin_page", msg="FAQ মুছে ফেলা হয়েছে"))


@app.route("/admin/settings/save", methods=["POST"])
@admin_required
def admin_save_settings():
    allowed = ["whatsapp", "bkash", "address", "hours"]
    conn = get_db()
    with conn:
        for k in allowed:
            val = request.form.get(k, "").strip()[:400]
            if val:
                conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, val))
    conn.close()
    return redirect(url_for("admin_page", msg="তথ্য সংরক্ষিত হয়েছে"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
