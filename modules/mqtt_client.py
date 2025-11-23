import logging
import threading
import uuid
import paho.mqtt.client as mqtt
from modules.config_loader import load_config

log = logging.getLogger(__name__)

class MqttClient:
    def __init__(self, config_file="config.json"):
        self.cfg = load_config(config_file)

        # Create random client ID to avoid conflicts
        self.client = mqtt.Client(client_id=f"DomiSafe-{uuid.uuid4().hex[:5]}")

        # Auth
        self.client.username_pw_set(
            self.cfg["ADAFRUIT_IO_USERNAME"],
            self.cfg["ADAFRUIT_IO_KEY"]
        )
        self.client.tls_set()

        # Flags
        self.connected = threading.Event()

        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        # Connect
        self.client.connect_async(
            self.cfg["MQTT_BROKER"],
            self.cfg["MQTT_PORT"],
            60
        )
        self.client.loop_start()

        # Wait for the connection
        if not self.connected.wait(10):
            log.error("❌ MQTT connection timeout")

    # -----------------------------
    # MQTT EVENT CALLBACKS
    # -----------------------------
    def _on_connect(self, client, userdata, flags, rc):
        log.info("✅ MQTT connected")
        self.connected.set()

        # Subscribe to control feeds from Adafruit IO
        username = self.cfg["ADAFRUIT_IO_USERNAME"]

        control_feeds = [
            "motor_status",
            "led_status",
            "buzzer_status"
        ]

        for feed in control_feeds:
            topic = f"{username}/feeds/{feed}"
            self.client.subscribe(topic)
            log.info(f"📡 Subscribed to: {topic}")

    def _on_disconnect(self, client, userdata, rc):
        log.warning("⚠️ MQTT disconnected")

    # -----------------------------
    # HANDLE INCOMING COMMANDS
    # -----------------------------
    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            value = msg.payload.decode().strip()

            feed = topic.split("/")[-1]
            log.info(f"📥 Received → {feed} = {value}")

            # Lazy import to avoid circular imports
            from modules.security_system import SecuritySystem

            # Route command
            if feed == "motor_status":
                SecuritySystem.set_motor(int(value))

            elif feed == "led_status":
                SecuritySystem.set_led(int(value))

            elif feed == "buzzer_status":
                SecuritySystem.set_buzzer(int(value))

        except Exception as e:
            log.error(f"MQTT on_message error: {e}")

    # -----------------------------
    # SAFE PUBLISH WRAPPER
    # -----------------------------
    def publish(self, feed, value):
        try:
            topic = f"{self.cfg['ADAFRUIT_IO_USERNAME']}/feeds/{feed}"
            self.client.publish(topic, str(value))
            log.info(f"📤 Sent → {feed}: {value}")
        except Exception as e:
            log.error(f"Publish failed: {e}")
