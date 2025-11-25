"""
============================================================
DOMISAFE FLASK APPLICATION (FIXED VERSION)
============================================================
Fixes:
- Proper form handling for device control
- Better error handling
- Consistent sync_pending display
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
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

# Setup logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Load configuration
cfg = load_config('config.json')
AIO_USERNAME = cfg.get('ADAFRUIT_IO_USERNAME', '')
AIO_KEY = cfg.get('ADAFRUIT_IO_KEY', '')
AIO_BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}"

# Initialize cloud database
cloud_db = CloudDB()
cloud_db.connect()

# MQTT client - PUBLISH-ONLY mode (webapp must not subscribe)
mqtt = MqttClient(subscribe=False)

# ============================================================
# Adafruit IO Helper Functions
# ============================================================
def get_adafruit(feed_name):
    """Get latest value from an Adafruit IO feed"""
    try:
        url = f"{AIO_BASE_URL}/feeds/{feed_name}/data/last"
        headers = {'X-AIO-Key': AIO_KEY}
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json().get("value")
        log.warning(f"Feed {feed_name} returned status {r.status_code}")
        return None
    except Exception as e:
        log.error(f"Feed read error {feed_name}: {e}")
        return None


def set_adafruit(feed_name, value):
    """Set value on an Adafruit IO feed"""
    try:
        url = f"{AIO_BASE_URL}/feeds/{feed_name}/data"
        headers = {'X-AIO-Key': AIO_KEY, 'Content-Type': 'application/json'}
        data = {'value': str(value)}
        r = requests.post(url, headers=headers, json=data, timeout=5)
        success = r.status_code in (200, 201)
        if success:
            log.info(f"✅ Set {feed_name} = {value}")
        else:
            log.warning(f"❌ Failed to set {feed_name}: {r.status_code}")
        return success
    except Exception as e:
        log.error(f"Feed write error {feed_name}: {e}")
        return False


def get_sync_pending():
    """Get count of unsynced records"""
    try:
        return {
            'env': len(fetch_unsynced('environment')),
            'motion': len(fetch_unsynced('motion'))
        }
    except Exception as e:
        log.error(f"Error getting sync status: {e}")
        return {'env': 0, 'motion': 0}


# ============================================================
# DASHBOARD PAGE (HOME)
# ============================================================
@app.route('/')
def dashboard():
    try:
        # LIVE DATA from Adafruit IO
        live_data = {
            'temperature': get_adafruit('temperature') or "N/A",
            'humidity': get_adafruit('humidity') or "N/A",
            'motion': get_adafruit('motion') or "0"
        }

        # RECENT ENVIRONMENT from Cloud DB
        latest_env = cloud_db.get_latest_environment(limit=5)

        # DEVICE STATES from Adafruit IO
        devices = ['led_status', 'buzzer_status', 'motor_status']
        device_states = {dev: get_adafruit(dev) or "0" for dev in devices}

        # SYNC STATUS
        sync_pending = get_sync_pending()

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
            live_data={'temperature': 'N/A', 'humidity': 'N/A', 'motion': '0'},
            latest_env=[],
            device_states={'led_status': '0', 'buzzer_status': '0', 'motor_status': '0'},
            sync_pending={'env': 0, 'motion': 0}
        )


# ============================================================
# ENVIRONMENT PAGE
# ============================================================
@app.route('/environment', methods=['GET', 'POST'])
def environment():
    selected_date = request.form.get('date', str(date.today()))
    
    try:
        rows = cloud_db.get_environment_by_date(selected_date)
    except Exception as e:
        log.error(f"DB query error: {e}")
        rows = []

    labels = []
    temps = []
    hums = []

    for row in rows:
        timestamp, t, h = row
        # Format timestamp for display
        if hasattr(timestamp, 'strftime'):
            labels.append(timestamp.strftime("%H:%M:%S"))
        else:
            labels.append(str(timestamp))
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

    # Get current security state from Adafruit IO
    raw = get_adafruit("security_enabled")
    is_enabled = (raw == "1")

    # Handle security toggle
    if request.method == 'POST' and 'toggle_security' in request.form:
        action = request.form.get("toggle_security")
        new_state = 1 if action == "enable" else 0
        
        # Update Adafruit IO via HTTP
        set_adafruit("security_enabled", new_state)
        
        # Also publish via MQTT (main.py receives this)
        mqtt.publish("security_enabled", new_state)
        
        is_enabled = (new_state == 1)
        log.info(f"🔐 Security toggled to: {'ENABLED' if is_enabled else 'DISABLED'}")

    # Get motion events for selected date
    try:
        motion_rows = cloud_db.get_motion_by_date(selected_date)
        intrusions = [r for r in motion_rows if r[1] == 1]
    except Exception as e:
        log.error(f"Motion query error: {e}")
        intrusions = []

    return render_template(
        "security.html",
        selected_date=selected_date,
        is_enabled=is_enabled,
        intrusions=intrusions,
        total_intrusions=len(intrusions)
    )


# ============================================================
# DEVICE CONTROL PAGE
# ============================================================
@app.route('/control', methods=['GET', 'POST'])
def control_page():
    message = ""

    if request.method == "POST":
        # FIXED: Get device and value from hidden form fields
        device = request.form.get("device")
        value = request.form.get("value")

        if device and value is not None:
            # Update Adafruit IO via HTTP API
            success = set_adafruit(device, value)
            
            # Also publish via MQTT (main.py's security system receives this)
            mqtt.publish(device, value)
            
            if success:
                state = "ON" if value == "1" else "OFF"
                message = f"✅ {device.replace('_status', '').upper()} turned {state}"
            else:
                message = f"❌ Failed to update {device}"
        else:
            log.warning(f"Invalid form data: device={device}, value={value}")

    # Get current device states
    devices = ['led_status', 'buzzer_status', 'motor_status']
    device_states = {dev: get_adafruit(dev) or "0" for dev in devices}

    return render_template(
        "control.html",
        device_states=device_states,
        message=message
    )


# ============================================================
# API - LIVE DATA FOR DASHBOARD AUTO REFRESH
# ============================================================
@app.route("/api/live-data")
def api_live():
    try:
        data = {
            "temperature": get_adafruit("temperature") or "N/A",
            "humidity": get_adafruit("humidity") or "N/A",
            "motion": get_adafruit("motion") or "0",
            "led_status": get_adafruit("led_status") or "0",
            "buzzer_status": get_adafruit("buzzer_status") or "0",
            "motor_status": get_adafruit("motor_status") or "0",
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    log.info("🚀 Starting DomiSafe Flask App...")
    log.info(f"📡 Adafruit IO User: {AIO_USERNAME}")
    log.info(f"🌐 Access at: http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)