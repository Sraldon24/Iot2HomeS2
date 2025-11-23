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
from modules.security_system import SecuritySystem

# ============================================================
# Flask App Setup
# ============================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'domisafe-secret-key-change-me'

cfg = load_config('../config.json')
AIO_USERNAME = cfg.get('ADAFRUIT_IO_USERNAME', '')
AIO_KEY = cfg.get('ADAFRUIT_IO_KEY', '')
AIO_BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}"

cloud_db = CloudDB()
cloud_db.connect()

mqtt = MqttClient()
security = SecuritySystem()

log = logging.getLogger(__name__)

# ============================================================
# Adafruit IO Helper Functions
# ============================================================
def get_adafruit_feed(feed_name):
    try:
        url = f"{AIO_BASE_URL}/feeds/{feed_name}/data/last"
        headers = {'X-AIO-Key': AIO_KEY}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {'value': data.get('value')}
        return None
    except Exception as e:
        log.error(f"Feed fetch error: {e}")
        return None

def set_adafruit_feed(feed_name, value):
    try:
        url = f"{AIO_BASE_URL}/feeds/{feed_name}/data"
        headers = {'X-AIO-Key': AIO_KEY, 'Content-Type': 'application/json'}
        data = {'value': str(value)}
        response = requests.post(url, headers=headers, json=data, timeout=5)
        return response.status_code in [200, 201]
    except Exception as e:
        log.error(f"Feed set error: {e}")
        return False

# ============================================================
# Dashboard Page
# ============================================================
@app.route('/')
def index():
    try:
        sensors = ['temperature', 'humidity', 'motion']
        live_data = {}

        for sensor in sensors:
            feed = get_adafruit_feed(sensor)
            live_data[sensor] = feed['value'] if feed else 'N/A'

        latest_env = cloud_db.get_latest_environment(limit=5)
        latest_motion = cloud_db.get_latest_motion(limit=5)

        devices = ['led_status', 'buzzer_status', 'motor_status']
        device_states = {}

        for device in devices:
            feed = get_adafruit_feed(device)
            device_states[device] = feed['value'] if feed else 'unknown'

        sync_pending = {
            'env': len(fetch_unsynced('environment')),
            'motion': len(fetch_unsynced('motion'))
        }

        return render_template(
            'dashboard.html',
            live_data=live_data,
            latest_env=latest_env,
            latest_motion=latest_motion,
            device_states=device_states,
            sync_pending=sync_pending
        )
    except Exception as e:
        log.error(f"Dashboard error: {e}")
        return render_template(
            'dashboard.html',
            live_data={}, latest_env=[], latest_motion=[],
            device_states={}, sync_pending={'env': 0, 'motion': 0}
        )

# ============================================================
# Environment Charts
# ============================================================
@app.route('/environment', methods=['GET', 'POST'])
def environment():
    selected_date = request.form.get('date', str(date.today()))
    env_data = cloud_db.get_environment_by_date(selected_date)

    timestamps = []
    temps = []
    hums = []

    for row in env_data:
        ts = row[0].strftime('%H:%M:%S') if hasattr(row[0], 'strftime') else str(row[0])
        timestamps.append(ts)
        temps.append(float(row[1]))
        hums.append(float(row[2]))

    return render_template(
        'environment.html',
        selected_date=selected_date,
        timestamps=timestamps,
        temps=temps,
        hums=hums,
        data_count=len(env_data)
    )

# ============================================================
# Security Page
# ============================================================
@app.route('/security', methods=['GET', 'POST'])
def security_page():
    selected_date = request.form.get('date', str(date.today()))

    security_enabled = get_adafruit_feed('security_enabled')
    is_enabled = security_enabled.get('value') == '1' if security_enabled else True

    if request.method == 'POST' and 'toggle_security' in request.form:
        new_state = 1 if request.form.get('toggle_security') == 'enable' else 0

        if set_adafruit_feed('security_enabled', new_state):
            mqtt.publish("security_enabled", new_state)
            is_enabled = (new_state == 1)

    motion_events = cloud_db.get_motion_by_date(selected_date)
    intrusions = [event for event in motion_events if event[1] == 1]

    return render_template(
        'security.html',
        selected_date=selected_date,
        is_enabled=is_enabled,
        intrusions=intrusions,
        total_intrusions=len(intrusions)
    )

# ============================================================
# Device Control Page
# ============================================================
@app.route('/control', methods=['GET', 'POST'])
def control():
    message = ""

    if request.method == 'POST':
        device = request.form.get('device')
        value = request.form.get('value')

        if device and value:

            # 1) Update feed on Adafruit IO (REST)
            success = set_adafruit_feed(device, value)

            # 2) Publish over MQTT
            mqtt.publish(device, value)

            # 3) Local Hardware Control
            val = int(value)

            if device == "led_status":
                SecuritySystem.set_led(val)

            elif device == "buzzer_status":
                SecuritySystem.set_buzzer(val)

            elif device == "motor_status":
                SecuritySystem.set_motor(val)

            message = f"✅ {device} → {value}" if success else "❌ Failed"

    devices = ['led_status', 'buzzer_status', 'motor_status']
    device_states = {}

    for device in devices:
        feed = get_adafruit_feed(device)
        device_states[device] = feed['value'] if feed else 'unknown'

    return render_template(
        'control.html',
        device_states=device_states,
        message=message
    )

# ============================================================
# API - Live JSON Data
# ============================================================
@app.route('/api/live-data')
def api_live_data():
    try:
        data = {}
        for sensor in ['temperature', 'humidity', 'motion']:
            feed = get_adafruit_feed(sensor)
            data[sensor] = feed['value'] if feed else 'N/A'
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# About Page
# ============================================================
@app.route('/about')
def about():
    return render_template('about.html')

# ============================================================
# Run App
# ============================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
