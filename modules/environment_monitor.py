import logging, random
from datetime import datetime
from modules.config_loader import load_config

try:
    import adafruit_dht, board
    HAS_DHT = True
except Exception:
    HAS_DHT = False

log = logging.getLogger(__name__)

class EnvironmentMonitor:
    def __init__(self, cfg_path="config.json"):
        cfg = load_config(cfg_path)
        self.pin = int(cfg["DHT_PIN"])
        self.sensor = None
        if HAS_DHT:
            try:
                self.sensor = adafruit_dht.DHT11(getattr(board, f"D{self.pin}"))
            except Exception as e:
                log.warning(f"DHT init failed: {e}")

    def read(self):
        temp, hum = None, None
        if self.sensor:
            try:
                temp = float(self.sensor.temperature or 0)
                hum = float(self.sensor.humidity or 0)
            except Exception as e:
                log.warning(f"DHT read error: {e}")

        if temp is None or hum is None:
            temp = round(22 + random.uniform(-2, 2), 1)
            hum = round(55 + random.uniform(-10, 10), 1)

        return {
            "temperature": temp,
            "humidity": hum,
            "timestamp": datetime.now().isoformat()
        }