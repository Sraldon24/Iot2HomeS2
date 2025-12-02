"""
============================================================
DOMISAFE FLASK APPLICATION (FIXED VERSION)
============================================================
Fixes:
- Proper form handling for device control
- Better error handling
- Consistent sync_pending display
- NEW: feed_name → feed-key conversion (underscore → dash)
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import logging
from datetime import datetime, date
import sys
import os
import time
from typing import Optional

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

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Load configuration
cfg = load_config('config.json')

def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve a configuration value using priority:
    1. `cfg.get(key)`
    2. `os.getenv(key)`
    3. `default` if provided

    If no value is found and no default is provided, raise RuntimeError.
    Logs which source provided the value using `logging.info()`.
    """
    # First try config file
    try:
        val = cfg.get(key) if isinstance(cfg, dict) else None
    except Exception:
        val = None

    if val is not None and val != "":
        log.info(f"Config {key} loaded from config.json")
        return val

    # Fallback to environment
    env_val = os.getenv(key)
    if env_val is not None and env_val != "":
        log.info(f"Config {key} loaded from environment")
        return env_val

    # Use provided default if any
    if default is not None:
        log.info(f"Config {key} loaded from default")
        return default

    # Nothing found — required config is missing
    raise RuntimeError(f"Missing required config: {key}")


# Use helper to load required config values
AIO_USERNAME = get_config_value('ADAFRUIT_IO_USERNAME')
AIO_KEY = get_config_value('ADAFRUIT_IO_KEY')
AIO_BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}"
# Optional/required external DB URL
NEON_DB_URL = get_config_value('NEON_DB_URL')

# Initialize cloud database (pass NEON_DB_URL override)
cloud_db = CloudDB(db_url=NEON_DB_URL)
cloud_db.connect()

# MQTT client (publish-only)
mqtt = MqttClient(subscribe=False)

# ============================================================
# FEED KEY NORMALIZATION
# ============================================================
def to_feed_key(feed_name: str) -> str:
    """Adafruit IO expects dashes, not underscores"""
    return feed_name.replace("_", "-")


# ============================================================
# Adafruit IO Helper Functions
# ============================================================
def get_adafruit(feed_name):
    """Get latest value from an Adafruit IO feed"""
    try:
        feed_key = to_feed_key(feed_name)
        url = f"{AIO_BASE_URL}/feeds/{feed_key}/data/last"
        headers = {'X-AIO-Key': AIO_KEY}

        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json().get("value")

        log.warning(f"Feed {feed_key} returned status {r.status_code}")
        return None
    except Exception as e:
        log.error(f"Feed read error {feed_name}: {e}")
        return None


def set_adafruit(feed_name, value):
    """Set value on an Adafruit IO feed"""
    try:
        time.sleep(0.3)  # Rate limiting
        feed_key = to_feed_key(feed_name)
        url = f"{AIO_BASE_URL}/feeds/{feed_key}/data"
        headers = {'X-AIO-Key': AIO_KEY, 'Content-Type': 'application/json'}
        data = {'value': str(value)}

        r = requests.post(url, headers=headers, json=data, timeout=5)
        success = r.status_code in (200, 201)

        if success:
            log.info(f"✅ Set {feed_key} = {value}")
        else:
            log.warning(f"❌ Failed to set {feed_key}: {r.status_code}")

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
# DASHBOARD PAGE
# ============================================================
@app.route('/')
def dashboard():
    try:
        live_data = {
            'temperature': get_adafruit('temperature') or "N/A",
            'humidity': get_adafruit('humidity') or "N/A",
            'motion': get_adafruit('motion') or "0"
        }

        latest_env = cloud_db.get_latest_environment(limit=5)

        devices = ['led_status', 'buzzer_status', 'motor_status']
        device_states = {dev: get_adafruit(dev) or "0" for dev in devices}

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

    labels, temps, hums = [], [], []

    for row in rows:
        timestamp, t, h = row

        if hasattr(timestamp, 'strftime'):
            labels.append(timestamp.strftime("%H:%M:%S"))
        else:
            labels.append(str(timestamp))

        temps.append(float(t))
        hums.append(float(h))

    return render_template(
        "environment.html",
        selected_date=selected_date,"""
============================================================
DOMISAFE FLASK APPLICATION (FIXED VERSION)
============================================================
Fixes:
- Proper form handling for device control
- Better error handling
- Consistent sync_pending display
- NEW: feed_name → feed-key conversion (underscore → dash)
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import logging
from datetime import datetime, date
import sys
import os
import time
from typing import Optional

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

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Load configuration
cfg = load_config('config.json')

def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve a configuration value using priority:
    1. `cfg.get(key)`
    2. `os.getenv(key)`
    3. `default` if provided

    If no value is found and no default is provided, raise RuntimeError.
    Logs which source provided the value using `logging.info()`.
    """
    # First try config file
    try:
        val = cfg.get(key) if isinstance(cfg, dict) else None
    except Exception:
        val = None

    if val is not None and val != "":
        log.info(f"Config {key} loaded from config.json")
        return val

    # Fallback to environment
    env_val = os.getenv(key)
    if env_val is not None and env_val != "":
        log.info(f"Config {key} loaded from environment")
        return env_val

    # Use provided default if any
    if default is not None:
        log.info(f"Config {key} using provided default")
        return default

    # Nothing found — required config is missing
    raise RuntimeError(f"Missing required config: {key}")


# Use helper to load required config values
AIO_USERNAME = get_config_value('ADAFRUIT_IO_USERNAME')
AIO_KEY = get_config_value('ADAFRUIT_IO_KEY')
AIO_BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}"
# Optional/required external DB URL
NEON_DB_URL = get_config_value('NEON_DB_URL')

# Initialize cloud database
cloud_db = CloudDB()
cloud_db.connect()

# MQTT client (publish-only)
mqtt = MqttClient(subscribe=False)

# ============================================================
# FEED KEY NORMALIZATION
# ============================================================
def to_feed_key(feed_name: str) -> str:
    """Adafruit IO expects dashes, not underscores"""
    return feed_name.replace("_", "-")


# ============================================================
# Adafruit IO Helper Functions
# ============================================================
def get_adafruit(feed_name):
    """Get latest value from an Adafruit IO feed"""
    try:
        feed_key = to_feed_key(feed_name)
        url = f"{AIO_BASE_URL}/feeds/{feed_key}/data/last"
        headers = {'X-AIO-Key': AIO_KEY}

        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            return r.json().get("value")

        log.warning(f"Feed {feed_key} returned status {r.status_code}")
        return None
    except Exception as e:
        log.error(f"Feed read error {feed_name}: {e}")
        return None


def set_adafruit(feed_name, value):
    """Set value on an Adafruit IO feed"""
    try:
        time.sleep(0.3)  # Rate limiting
        feed_key = to_feed_key(feed_name)
        url = f"{AIO_BASE_URL}/feeds/{feed_key}/data"
        headers = {'X-AIO-Key': AIO_KEY, 'Content-Type': 'application/json'}
        data = {'value': str(value)}

        r = requests.post(url, headers=headers, json=data, timeout=5)
        success = r.status_code in (200, 201)

        if success:
            log.info(f"✅ Set {feed_key} = {value}")
        else:
            log.warning(f"❌ Failed to set {feed_key}: {r.status_code}")

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
# DASHBOARD PAGE
# ============================================================
@app.route('/')
def dashboard():
    try:
        live_data = {
            'temperature': get_adafruit('temperature') or "N/A",
            'humidity': get_adafruit('humidity') or "N/A",
            'motion': get_adafruit('motion') or "0"
        }

        latest_env = cloud_db.get_latest_environment(limit=5)

        devices = ['led_status', 'buzzer_status', 'motor_status']
        device_states = {dev: get_adafruit(dev) or "0" for dev in devices}

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

    labels, temps, hums = [], [], []

    for row in rows:
        timestamp, t, h = row

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

    raw = get_adafruit("security_enabled")
    is_enabled = (raw == "1")

    if request.method == 'POST' and 'toggle_security' in request.form:
        action = request.form.get("toggle_security")
        new_state = 1 if action == "enable" else 0

        set_adafruit("security_enabled", new_state)
        mqtt.publish("security_enabled", new_state)

        is_enabled = (new_state == 1)
        log.info(f"🔐 Security toggled → {is_enabled}")

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
        device = request.form.get("device")
        value = request.form.get("value")

        if device and value is not None:
            success = set_adafruit(device, value)
            mqtt.publish(device, value)

            if success:
                state = "ON" if value == "1" else "OFF"
                message = f"✅ {device.replace('_status', '').upper()} turned {state}"
            else:
                message = f"❌ Failed to update {device}"
        else:
            log.warning(f"Invalid form data: device={device}, value={value}")

    devices = ['led_status', 'buzzer_status', 'motor_status']
    device_states = {dev: get_adafruit(dev) or "0" for dev in devices}

    return render_template(
        "control.html",
        device_states=device_states,
        message=message
    )


# ============================================================
# API (dashboard auto-refresh)
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
        action = request.form.get("toggle_security")
        new_state = 1 if action == "enable" else 0

        set_adafruit("security_enabled", new_state)
        mqtt.publish("security_enabled", new_state)

        is_enabled = (new_state == 1)
        log.info(f"🔐 Security toggled → {is_enabled}")

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
        device = request.form.get("device")
        value = request.form.get("value")

        if device and value is not None:
            success = set_adafruit(device, value)
            mqtt.publish(device, value)

            if success:
                state = "ON" if value == "1" else "OFF"
                message = f"✅ {device.replace('_status', '').upper()} turned {state}"
            else:
                message = f"❌ Failed to update {device}"
        else:
            log.warning(f"Invalid form data: device={device}, value={value}")

    devices = ['led_status', 'buzzer_status', 'motor_status']
    device_states = {dev: get_adafruit(dev) or "0" for dev in devices}

    return render_template(
        "control.html",
        device_states=device_states,
        message=message
    )


# ============================================================
# API (dashboard auto-refresh)
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
