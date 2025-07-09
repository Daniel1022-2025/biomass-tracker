from flask import Flask, render_template, request, redirect, send_file, session, url_for
import csv, os, hashlib, shutil
from datetime import datetime, date
from statistics import mean
from collections import defaultdict
from utils import compute_alert_level
import pandas as pd

app = Flask(__name__)
app.secret_key = "passwof3a9c1e7b2d4a6f8c0e1d3b5a7c9e2f0a1b3d5f7c9e0a2b4c6d8e0f2a4c6e8f0"

# 🔧 Constants
EXCEL_PATH = "static/data/Biomass_Rainfall_Dan.xlsx"
DATA_FILE = "static/data/biomass_data.csv"
FIELDNAMES = ["date", "biomass", "rainfall", "location", "narrative"]

# 🔄 Load and merge Excel data
def load_combined_data():
    biomass_df = pd.read_excel(EXCEL_PATH, sheet_name="Biomass Spefic Locatons")
    rainfall_df = pd.read_excel(EXCEL_PATH, sheet_name="Biomass_Rainfall all Areas")
    biomass_df["Date"] = pd.to_datetime(biomass_df["Date"])
    rainfall_df["Date"] = pd.to_datetime(rainfall_df["Date"])
    df = pd.merge(biomass_df, rainfall_df[["Date", "Total.Monthly.Rain"]], on="Date", how="left")

    locations = ["CHOLOLO", "EAST_RESERVE", "WEST_RESERVE", "DOLDOL"]
    location_series = {
        loc: {
            "dates": df["Date"].dt.strftime("%Y-%m-%d").tolist(),
            "biomass": df[loc].fillna(0).tolist()
        }
        for loc in locations
    }

    biomass = df["Biomass.new"].fillna(0).tolist()
    rainfall = df["Total.Monthly.Rain"].fillna(0).tolist()
    dates = df["Date"].dt.strftime("%Y-%m-%d").tolist()

    return dates, biomass, rainfall, location_series

# 🔐 Admin credentials (hashed)
ADMIN_USERS = {
    "dan": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # password
    "admin": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"  # biomass123
}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def safe_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def load_data():
    if not os.path.exists(DATA_FILE):
        return [], [], [], []
    with open(DATA_FILE, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    dates, biomass, rainfall = [], [], []
    for row in rows:
        dates.append(row.get('date', ''))
        biomass.append(safe_float(row.get('biomass')))
        rainfall.append(safe_float(row.get('rainfall')))
    return rows, dates, biomass, rainfall

def get_latest_biomass(values):
    return values[-1] if values else 0

def calculate_7_day_avg(data):
    return round(mean(data[-7:]), 2) if len(data) >= 7 else round(mean(data), 2) if data else 0

def backup_data():
    if os.path.exists(DATA_FILE):
        shutil.copy(DATA_FILE, DATA_FILE + ".bak")

def log_action(action, row):
    user = session.get("user", "unknown")
    timestamp = datetime.now().isoformat()
    with open("audit.log", "a") as f:
        f.write(f"{timestamp} | {user} | {action.upper()} | {row}\n")

# 🌐 Routes

@app.route("/")
def index():
    start = request.args.get("start")
    end = request.args.get("end")
    location = request.args.get("location", "").strip()

    dates, biomass, rainfall, location_series = load_combined_data()

    if start and end:
        filtered = [(d, b, r) for d, b, r in zip(dates, biomass, rainfall) if start <= d <= end]
        if filtered:
            dates, biomass, rainfall = zip(*filtered)
        else:
            dates, biomass, rainfall = [], [], []

    latest = round(biomass[-1], 3) if biomass else 0
    avg = round(sum(biomass) / len(biomass), 3) if biomass else 0
    gauge_color = compute_alert_level(latest)

    return render_template(
        "dashboard.html",
        dates=dates,
        biomass=biomass,
        rainfall=rainfall,
        biomass_value=latest,
        biomass_avg=avg,
        gauge_color=gauge_color,
        locations=list(location_series.keys()),
        selected_location=location,
        start_date=start or "",
        end_date=end or "",
        location_series=location_series
    )

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        form = request.form
        try:
            datetime.strptime(form["date"], "%Y-%m-%d")
            float(form["biomass"])
            float(form["rainfall"])
        except (ValueError, KeyError):
            return "Invalid input.", 400
        new_row = [
            form["date"],
            form["biomass"],
            form["rainfall"],
            form.get("location", "N/A"),
            form.get("narrative", "")
        ]
        file_exists = os.path.isfile(DATA_FILE)
        with open(DATA_FILE, "a", newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(FIELDNAMES)
            writer.writerow(new_row)
        return redirect("/")
    return render_template("admin.html", current_date=date.today().isoformat())

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        index = int(request.form["index"])
        action = request.form.get("action")
        with open(DATA_FILE, newline='') as f:
            rows = list(csv.reader(f))
        if action == "delete":
            deleted_row = rows.pop(index + 1)
            log_action("delete", deleted_row)
        else:
            updated_row = [
                request.form["date"],
                request.form["biomass"],
                request.form["rainfall"],
                request.form.get("location", "N/A"),
                request.form.get("narrative", "")
            ]
            rows[index + 1] = updated_row
            log_action("edit", updated_row)
        backup_data()
        with open(DATA_FILE, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        return redirect(url_for("edit"))

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    search = request.args.get("search", "").lower()

    with open(DATA_FILE, newline='') as f:
        reader = csv.reader(f)
        rows = list(reader)

    headers = rows[0]
    data = rows[1:]

    if search:
        data = [row for row in data if search in row[0].lower() or search in row[3].lower()]

    total_pages = (len(data) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    paginated_data = data[start:end]

    return render_template(
        "edit.html",
        headers=headers,
        data=paginated_data,
        page=page,
        total_pages=total_pages,
        per_page=per_page,
        search=search,
        start_index=start
    )

@app.route("/undo")
def undo():
    if "user" not in session:
        return redirect(url_for("login"))
    backup_file = DATA_FILE + ".bak"
    if os.path.exists(backup_file):
        shutil.copy(backup_file, DATA_FILE)
        return redirect("/edit")
    return "No backup available.", 400

@app.route("/download")
def download_data():
    if not os.path.exists(DATA_FILE):
        return "No data available.", 404
    return send_file(DATA_FILE, as_attachment=True)

@app.route("/export")
def export_filtered():
    start = request.args.get("start")
    end = request.args.get("end")
    location = request.args.get("location", "").strip()

    records, _, _, _ = load_data()
    filtered = []

    for row in records:
        if location and row.get("location", "").lower() != location.lower():
            continue
        if start and row["date"] < start:
            continue
        if end and row["date"] > end:
            continue
        filtered.append(row)

    filename = "filtered_biomass.csv"
    with open(filename, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(filtered)

    return send_file(filename, as_attachment=True)

@app.route("/forecast")
def forecast():
    _, _, biomass_values,
    @app.route("/forecast")
d@app.route("/forecast")
def forecast():
    _, _, biomass_values, _ = load_data()
    if len(biomass_values) < 2:
        return "Not enough data to forecast.", 200
    trend = biomass_values[-1] - biomass_values[-2]
    forecast = round(biomass_values[-1] + trend, 2)
    return f"📈 Projected biomass for next entry: {forecast} g/m²", 200
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        hashed = hash_password(password)
        if username in ADMIN_USERS and ADMIN_USERS[username] == hashed:
            session["user"] = username
            return redirect(url_for("admin"))
        return "Invalid credentials", 401
    return render_template("login.html")

# ✅ Run the app (for Railway deployment)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)