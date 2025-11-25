# ============================================================
# FINAL FIXED FULL APP.PY FOR DOMISAFE
# ============================================================

from flask import Flask, render_template, request, jsonify
import requests
import logging
from datetime import datetime, date
import sys
import os

# Allow imports from root/modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.config_loader import load_config
from modules.cloud_db import CloudDB
from modules.local_db import fetch_unsynced
from modules.mqtt_client import MqttClient

# ============================================================
# Flask App Setup
# ============================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'domisafe-secret-key-change-me'

cfg = load_config('config.json')
AIO_USERNAME = cfg.get('ADAFRUIT_IO_USERNAME', '')
AIO_KEY = cfg.get('ADAFRUIT_IO_KEY', '')
AIO_BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}"

cloud_db = CloudDB()
cloud_db.connect()

mqtt = MqttClient(subscribe=False)  # PUBLISH-ONLY (webapp must not subscribe)

log = logging.getLogger(__name__)

# ============================================================
# Adafruit IO Helper Functions
# ============================================================
def get_adafruit(feed_name):
    try:
        url = f"{AIO_BASE_URL}/feeds/{feed_name}/data/last"
        headers = {'X-AIO-Key': AIO_KEY}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json().get("value")
        return None
    except Exception as e:
        log.error(f"Feed read error {feed_name}: {e}")
        return None


def set_adafruit(feed_name, value):
    try:
        url = f"{AIO_BASE_URL}/feeds/{feed_name}/data"
        headers = {'X-AIO-Key': AIO_KEY, 'Content-Type': 'application/json'}
        data = {'value': str(value)}
        r = requests.post(url, headers=headers, json=data, timeout=5)
        return r.status_code in (200, 201)
    except Exception as e:
        log.error(f"Feed write error {feed_name}: {e}")
        return False

# ============================================================
# DASHBOARD PAGE
# ============================================================
@app.route('/')
def dashboard():
    try:
        # LIVE DATA
        live_data = {
            'temperature': get_adafruit('temperature') or "N/A",
            'humidity': get_adafruit('humidity') or "N/A",
            'motion': get_adafruit('motion') or "0"
        }

        # ENVIRONMENT LAST 5 ROWS
        latest_env = cloud_db.get_latest_environment(limit=5)

        # DEVICE STATES
        devices = ['led_status', 'buzzer_status', 'motor_status']
        device_states = {dev: get_adafruit(dev) or "0" for dev in devices}

        # PENDING SYNC VALUES
        sync_pending = {
            'env': len(fetch_unsynced('environment')),
            'motion': len(fetch_unsynced('motion'))
        }

        return render_template(
            "dashboard.html",
            live_data=live_data,
            latest_env=latest_env,
            device_states=device_states,
            sync_pending=sync_pending
        )
    except Exception as e:
        log.error(f"DASHBOARD ERROR: {e}")
        return render_template(
            "dashboard.html",
            live_data={},
            latest_env=[],
            device_states={},
            sync_pending={}
        )

# ============================================================
# ENVIRONMENT PAGE
# ============================================================
@app.route('/environment', methods=['GET', 'POST'])
def environment():
    selected_date = request.form.get('date', str(date.today()))
    rows = cloud_db.get_environment_by_date(selected_date)

    labels = []
    temps = []
    hums = []

    for row in rows:
        timestamp, t, h = row
        labels.append(timestamp.strftime("%H:%M:%S"))
        temps.append(float(t))
        hums.append(float(h))

    return render_template(
        "environment.html",
        selected_date=selected_date,
        data_count=len(rows),
        labels=labels,
        temperatures=temps,
        humidities=hums,
        min_temp=min(temps) if temps else None,
        max_temp=max(temps) if temps else None,
        min_hum=min(hums) if hums else None,
        max_hum=max(hums) if hums else None,
        env_data=rows
    )

# ============================================================
# SECURITY PAGE
# ============================================================
@app.route('/security', methods=['GET', 'POST'])
def security_page():
    selected_date = request.form.get('date', str(date.today()))

    raw = get_adafruit("security_enabled")
    is_enabled = (raw == "1")

    if request.method == 'POST' and 'toggle_security' in request.form:
        new_state = 1 if request.form.get("toggle_security") == "enable" else 0

        set_adafruit("security_enabled", new_state)
        mqtt.publish("security_enabled", new_state)  # main.py reacts
        is_enabled = (new_state == 1)

    motion_rows = cloud_db.get_motion_by_date(selected_date)
    intrusions = [r for r in motion_rows if r[1] == 1]

    return render_template(
        "security.html",
        selected_date=selected_date,
        is_enabled=is_enabled,
        intrusions=intrusions,
        total_intrusions=len(intrusions)
    )

# ============================================================
# CONTROL PAGE
# ============================================================
@app.route('/control', methods=['GET', 'POST'])
def control_page():
    message = ""

    if request.method == "POST":
        device = request.form.get("device")
        value = request.form.get("value")

        if device and value:
            set_adafruit(device, value)
            mqtt.publish(device, value)
            message = f"Updated {device} → {value}"

    devices = ['led_status', 'buzzer_status', 'motor_status']
    device_states = {dev: get_adafruit(dev) or "0" for dev in devices}

    return render_template(
        "control.html",
        device_states=device_states,
        message=message
    )

# ============================================================
# API – LIVE DATA FOR DASHBOARD AUTO REFRESH
# ============================================================
@app.route("/api/live-data")
def api_live():
    try:
        data = {
            "temperature": get_adafruit("temperature") or "N/A",
            "humidity": get_adafruit("humidity") or "N/A",
            "motion": get_adafruit("motion") or "0",
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

# ============================================================
# ABOUT PAGE
# ============================================================
@app.route('/about')
def about_page():
    return render_template("about.html")

# ============================================================
# RUN APP
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
