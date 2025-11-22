import json, os, logging

log = logging.getLogger(__name__)

DEFAULTS = {
    "ADAFRUIT_IO_USERNAME": "",
    "ADAFRUIT_IO_KEY": "",
    "MQTT_BROKER": "io.adafruit.com",
    "MQTT_PORT": 8883,
    "NEON_DB_URL": "",
    "DHT_PIN": 4,
    "PIR_PIN": 6,
    "LED_PIN": 16,
    "BUZZER_PIN": 26,
    "MOTOR_PIN": 21,
    "security_check_interval": 5,
    "env_interval": 30,
    "sync_interval": 60,
    "camera_enabled": True,
    "cloud_sync_enabled": True,
    "google_drive_enabled": False,
    "google_drive_log_folder_id": "",
    "google_drive_image_folder_id": ""
}

def load_config(path="config.json"):
    cfg = dict(DEFAULTS)
    if os.path.exists(path):
        try:
            with open(path) as f:
                cfg.update(json.load(f))
                log.info(f"✅ Loaded config from {path}")
        except Exception as e:
            log.warning(f"⚠️ Failed reading {path}: {e}")
    else:
        log.warning(f"⚠️ Using default configuration")
    return cfg