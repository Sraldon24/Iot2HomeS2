import logging, threading, uuid, paho.mqtt.client as mqtt
from modules.config_loader import load_config

log = logging.getLogger(__name__)

class MqttClient:
    def __init__(self, config_file="config.json"):
        self.cfg = load_config(config_file)
        self.client = mqtt.Client(client_id=f"DomiSafe-{uuid.uuid4().hex[:5]}")
        self.client.username_pw_set(
            self.cfg["ADAFRUIT_IO_USERNAME"],
            self.cfg["ADAFRUIT_IO_KEY"]
        )
        self.client.tls_set()
        self.connected = threading.Event()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.connect_async(self.cfg["MQTT_BROKER"], self.cfg["MQTT_PORT"], 60)
        self.client.loop_start()
        if not self.connected.wait(10):
            log.error("❌ MQTT timeout")

    def _on_connect(self, *a):
        log.info("✅ MQTT connected")
        self.connected.set()

    def _on_disconnect(self, *a):
        log.warning("⚠️ MQTT disconnected")

    def publish(self, feed, value):
        try:
            topic = f"{self.cfg['ADAFRUIT_IO_USERNAME']}/feeds/{feed}"
            self.client.publish(topic, str(value))
            log.info(f"📤 {feed}: {value}")
        except Exception as e:
            log.error(f"Publish failed: {e}")