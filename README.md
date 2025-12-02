# 🏠 DomiSafe IoT Home Security System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4-red.svg)](https://www.raspberrypi.org/)

A complete IoT home security system with motion detection, environmental monitoring, camera capture, and cloud synchronization.

---

## 👥 **Team Information**

**Developer:** Amir (Sraldon24)  Alex 
**Course:** 420-N55 IoT: Design and Prototyping of Connected Devices  
**Institution:** Champlain College Saint-Lambert  
**Term:** Fall 2025  
**Professor:** Haikel Hichri

---

## 📡 **Adafruit IO Dashboard**

View live sensor data and control devices in real-time:

👉 **[View Dashboard](https://io.adafruit.com/YOUR_USERNAME/dashboards/domisafe)**

*Replace YOUR_USERNAME with your actual Adafruit IO username after setup*

**Features on Dashboard:**
- Real-time temperature and humidity gauges
- Motion detection indicator
- LED, buzzer, and motor control toggles
- Historical data line charts

---

## ☁️ **Cloud Storage**

Daily logs and captured motion images are automatically uploaded:

👉 **[View Files on Google Drive](https://drive.google.com/drive/folders/YOUR_FOLDER_ID)**

*Or data is stored in Neon PostgreSQL database - accessible via Flask app*

---

## 🎥 **Demo Video**

Watch the complete system demonstration (3 minutes):

👉 **[Watch on YouTube](https://youtube.com/shorts/6NvQyifem0k?si=NhJyaJJdsLLMG1LM)**

**Video demonstrates:**
- System overview and code structure
- Starting the application on Raspberry Pi
- App running without exceptions
- Local log files with timestamps
- Live data on Adafruit IO dashboard
- Motion detection triggering alerts
- Camera image capture

---

## 📦 **Features**

| Feature | Description |
|---------|-------------|
| 🔔 **Motion Detection** | PIR sensor triggers LED, buzzer, motor, and camera |
| 🌡️ **Environmental Monitoring** | DHT11 reads temperature and humidity every 30s |
| 📷 **Camera Capture** | Automatic image capture on motion events |
| ☁️ **MQTT Communication** | Secure TLS connection to Adafruit IO |
| 💾 **Offline-First Storage** | Local SQLite with automatic cloud sync |
| 🔄 **Cloud Synchronization** | Background sync to Neon PostgreSQL |
| 📊 **Flask Web Dashboard** | 5-page interface with Chart.js visualizations |
| 🎛️ **Remote Control** | Control devices via Adafruit IO or web app |

---

## 🧰 **Hardware Components**

| Component | BCM Pin | Board Pin | Purpose |
|-----------|---------|-----------|---------|
| PIR Motion Sensor | 6 | 31 | Detects motion |
| LED Indicator | 16 | 36 | Visual alert |
| Buzzer | 26 | 37 | Audio alert |
| DHT11 Sensor | 4 | 7 | Temperature & humidity |
| DC Motor/Fan | 21 | 40 | Physical alert |
| Camera Module | CSI | - | Image capture |

**Wiring:**
- All components use 3.3V or 5V power
- LED uses 330Ω resistor
- Motor uses transistor circuit
- See `HARDWARE_GUIDE.md` for detailed wiring diagrams

---

## 🏗️ **System Architecture**

```
┌─────────────────┐
│  Raspberry Pi   │
│                 │
│  ┌──────────┐   │      ┌──────────────┐
│  │ Sensors  │───┼─────▶│  Adafruit IO │ (MQTT/TLS)
│  │ Actuators│   │      │   Dashboard  │
│  └──────────┘   │      └──────────────┘
│       │         │              ▲
│       ▼         │              │
│  ┌──────────┐   │              │
│  │ SQLite   │   │     HTTP GET for live data
│  │ Local DB │   │              │
│  └──────────┘   │              │
│       │         │              │
│       ▼         │              │
│  ┌──────────┐   │      ┌──────────────┐
│  │  Sync    │───┼─────▶│ Flask Web App│
│  │ Service  │   │      │  Dashboard   │
│  └──────────┘   │      └──────────────┘
│       │         │              │
└───────┼─────────┘              │
        │                        │
        ▼                        ▼
┌──────────────────┐       (SQL Queries)
│  Neon PostgreSQL │              │
│  Cloud Database  │◀─────────────┘
└──────────────────┘
```

---

## ⚡ **Quick Start**

### Prerequisites
- Raspberry Pi 4 (2GB+ RAM)
- Raspbian OS (64-bit recommended)
- Python 3.9+
- Internet connection
- Hardware components wired correctly

### Installation

```bash
# 1. Clone repository
git clone https://github.com/Sraldon24/Iot2HomeS.git
cd Iot2HomeS

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Configure credentials
cp config.example.json config.json
nano config.json
# Add your Adafruit IO and Neon DB credentials

# 4. Install dependencies
source venv/bin/activate
pip install -r requirements.txt

# 5. Run tests
python3 test_system.py

# 6. Start main application
python3 main.py

# 7. In another terminal - Start Flask web app
cd web_app
python3 app.py

# 8. Access dashboard
# Open browser: http://YOUR_PI_IP:5000
```

---

## 📝 **Configuration**

Edit `config.json` with your credentials:

```json
{
  "ADAFRUIT_IO_USERNAME": "your_username",
  "ADAFRUIT_IO_KEY": "your_key",
  "NEON_DB_URL": "postgresql://user:pass@host/db",
  "DHT_PIN": 4,
  "PIR_PIN": 6,
  "LED_PIN": 16,
  "BUZZER_PIN": 26,
  "MOTOR_PIN": 21,
  "camera_enabled": true,
  "cloud_sync_enabled": true
}
```

**See `SETUP_TUTORIAL.md` for detailed credential setup instructions.**

---

## 🌐 **Flask Web Dashboard**

Access at `http://YOUR_PI_IP:5000`

### Pages:

1. **Home Dashboard** (`/`)
   - Live sensor readings from Adafruit IO
   - Recent environment logs
   - Recent motion events
   - Device status
   - Cloud sync status

2. **Environment Data** (`/environment`)
   - Date picker for historical data
   - Interactive Chart.js line graphs
   - Temperature and humidity trends
   - Statistics (avg, min, max)

3. **Security Management** (`/security`)
   - Enable/disable security system
   - View intrusions by date
   - Motion event timeline

4. **Device Control** (`/control`)
   - Control LED, buzzer, motor
   - Quick actions
   - Real-time status

5. **About** (`/about`)
   - Project information
   - Reflection
   - Team members
   - Links

---

## 🗂️ **Project Structure**

```
Iot2HomeS/
├── main.py                      # Main IoT application
├── manual_control.py            # Manual device control script
├── config.example.json          # Configuration template
├── requirements.txt             # Python dependencies
├── setup.sh                     # Automated setup script
├── test_system.py              # System test suite
├── upload_logs.py              # Google Drive uploader
│
├── modules/
│   ├── config_loader.py        # Configuration loader
│   ├── mqtt_client.py          # Adafruit IO MQTT client
│   ├── local_db.py             # SQLite database
│   ├── cloud_db.py             # PostgreSQL cloud database
│   ├── sync_service.py         # Offline sync service
│   ├── environment_monitor.py  # DHT11 sensor handler
│   ├── security_system.py      # PIR motion detection
│   └── camera_handler.py       # Pi Camera wrapper
│
├── web_app/
│   ├── app.py                  # Flask application
│   ├── templates/              # HTML templates (5 pages)
│   └── static/                 # CSS styling
│
├── logs/                        # Application logs
├── captures/                    # Motion event images
└── iot_data.db                 # Local SQLite database
```

---

## 💭 **Project Reflection**

### ✅ **What Worked Well:**

The threaded architecture allowed simultaneous environment monitoring and security checks without blocking, enabling real-time responsiveness. MQTT over TLS provided secure, encrypted communication with Adafruit IO, ensuring data integrity. The dual-database strategy (local SQLite + cloud PostgreSQL) handled internet outages gracefully with automatic synchronization when connectivity was restored. Flask with Chart.js created an intuitive, professional-looking dashboard that made data visualization accessible and actionable.

### 🔧 **What Was Hardest:**

Implementing the offline-first sync mechanism required careful state tracking and error handling to prevent data loss during network interruptions. Managing concurrent database writes from multiple threads was challenging, requiring proper locking mechanisms and transaction handling. Debugging GPIO pin conflicts between multiple hardware components took significant time. Configuring PostgreSQL connection pooling for reliable cloud database access required extensive testing. Handling camera capture timing to avoid missing motion events during image processing was complex.

### 🚀 **What We'd Improve:**

We would add real-time WebSocket updates to the dashboard instead of polling to reduce latency and server load. Implementing email/SMS notifications for critical security events would enhance the system's alerting capabilities. Adding machine learning-based motion detection could reduce false positives from environmental factors. Creating a mobile app would enable remote monitoring from anywhere. Implementing time-based automation rules (e.g., arm security at night, disable during day) would add intelligence. Multi-user authentication with role-based access control would make it production-ready for multiple household members.

---

## 🛠️ **Technical Stack**

**Hardware:**
- Raspberry Pi 4
- PIR Motion Sensor (HC-SR501)
- DHT11 Temperature/Humidity Sensor
- Pi Camera Module v2
- LED, Buzzer, DC Motor

**Software:**
- Python 3.9+
- Flask 3.0 (Web Framework)
- Paho-MQTT (MQTT Client)
- SQLite (Local Database)
- PostgreSQL (Cloud Database via Neon.tech)
- Chart.js (Data Visualization)
- Adafruit IO (IoT Platform)

**Protocols:**
- MQTT over TLS (Sensor Data Publishing)
- HTTP/HTTPS (Flask API & Adafruit IO)
- SQL (Database Queries)
- WebSockets (Optional for real-time updates)

---

## 📊 **Data Flow**

1. **Sensors** → Read data every 5-30 seconds
2. **Local Processing** → Store in SQLite immediately
3. **MQTT Publish** → Send to Adafruit IO (TLS encrypted)
4. **Cloud Sync** → Background thread syncs SQLite → PostgreSQL
5. **Flask App** → Fetches live data (HTTP) & historical (SQL)
6. **User** → Views dashboard & controls devices

**Offline Mode:**
- Data stored locally in SQLite
- Marked as "unsynced"
- When internet returns, sync service automatically uploads
- No data loss

---

## 🧪 **Testing**

Run the complete test suite:

```bash
python3 test_system.py
```

**Tests:**
- ✅ Configuration loading
- ✅ MQTT connection
- ✅ Local database operations
- ✅ Cloud database connection
- ✅ Sensor reading
- ✅ Camera functionality
- ✅ Sync service
- ✅ Flask routes

---

## 📚 **Documentation**

- **`SETUP_TUTORIAL.md`** - Complete setup guide (Adafruit IO, Neon DB, Google Drive)
- **`HARDWARE_GUIDE.md`** - Wiring diagrams and component details
- **`DEPLOYMENT.md`** - Production deployment with systemd
- **`CONFIG_GUIDE.md`** - Configuration options explained
- **`API_GUIDE.md`** - Flask API endpoints

---

## 🔒 **Security**

- All credentials stored in `config.json` (not committed to Git)
- MQTT uses TLS/SSL encryption
- PostgreSQL uses SSL mode
- No hardcoded secrets in code
- `.gitignore` prevents accidental credential exposure

---

## 🆘 **Troubleshooting**

### "MQTT Connection Failed"
```bash
# Check credentials in config.json
# Verify at io.adafruit.com
python3 -c "from modules.mqtt_client import MqttClient; m = MqttClient()"
```

### "Cloud DB Connection Failed"
```bash
# Test Neon connection
python3 -c "from modules.cloud_db import CloudDB; c = CloudDB(); c.connect()"
```

### "Camera Not Working"
```bash
# Enable camera
sudo raspi-config
# Interface Options → Camera → Enable
```

**See full troubleshooting guide in `DEPLOYMENT.md`**

---

## 📞 **Support**

- **Issues:** [GitHub Issues](https://github.com/Sraldon24/Iot2HomeS/issues)
- **Email:** Contact via GitHub profile
- **Documentation:** See markdown files in repository

---

## 📄 **License**

MIT License - See LICENSE file for details

---

## 🙏 **Acknowledgments**

- Professor Haikel Hichri for guidance and course structure
- Champlain College Saint-Lambert for resources
- Adafruit for excellent IoT platform and documentation
- Neon.tech for free PostgreSQL database hosting
- Open source community for libraries and tools

---

## 🔗 **Links**

- **GitHub Repository:** https://github.com/Sraldon24/Iot2HomeS
- **Demo Video:** https://youtube.com/shorts/6NvQyifem0k?si=NhJyaJJdsLLMG1LM
- **Adafruit IO:** https://io.adafruit.com
- **Neon Database:** https://neon.tech
- **Flask Documentation:** https://flask.palletsprojects.com
- **Chart.js:** https://www.chartjs.org

---

**Made with ❤️ for IoT Course - Fall 2025**
