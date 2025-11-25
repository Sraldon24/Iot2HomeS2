"""
============================================
DomiSafe IoT System - MQTT Client (FIXED)
============================================
Fixes:
- Added security_enabled subscription
- Auto-convert underscore feed names → dash feed keys (MQTT requirement)
"""

import logging
import threading
import uuid
import paho.mqtt.client as mqtt
from modules.config_loader import load_config

log = logging.getLogger(__name__)

class MqttClient:
    def __init__(self, config_file="config.json", subscribe=True, security=None):
        self.cfg = load_config(config_file)
        self.subscribe = subscribe

        # Real hardware
        self.security = security
        
        # Security state for main.py
        self.security_enabled = True

        # Unique client ID
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

        if not self.connected.wait(10):
            log.error("❌ MQTT connection timeout")

    # -------------------------------------------------------
    # MQTT CALLBACKS
    # -------------------------------------------------------
    def _to_feed_key(self, feed: str) -> str:
        """Convert Python-style feed names to Adafruit IO feed keys."""
        return feed.replace("_", "-")

    def _on_connect(self, client, userdata, flags, rc):
        log.info("✅ MQTT connected")
        self.connected.set()

        if not self.subscribe:
            log.info("ℹ️ Publish-only mode active — no subscriptions")
            return

        username = self.cfg["ADAFRUIT_IO_USERNAME"]

        control_feeds = [
            "motor_status",
            "led_status",
            "buzzer_status",
            "security_enabled"
        ]

        for feed in control_feeds:
            feed_key = self._to_feed_key(feed)
            topic = f"{username}/feeds/{feed_key}"
            self.client.subscribe(topic)
            log.info(f"📡 Subscribed → {topic}")

    def _on_disconnect(self, client, userdata, rc):
        log.warning("⚠️ MQTT disconnected")
        self.connected.clear()

    # -------------------------------------------------------
    # INCOMING COMMAND HANDLER
    # -------------------------------------------------------
    def _on_message(self, client, userdata, msg):
        if not self.subscribe:
            return
        
        try:
            topic = msg.topic
            value = msg.payload.decode().strip()

            feed_key = topic.split("/")[-1]           # ex: "motor-status"
            feed = feed_key.replace("-", "_")         # ex: "motor_status"

            log.info(f"📥 Received → {feed} = {value}")

            # Handle security toggle
            if feed == "security_enabled":
                self.security_enabled = (value == "1")
                status = "ENABLED" if self.security_enabled else "DISABLED"
                log.info(f"🔐 Security system {status}")
                return

            # Safety check: hardware available
            if not self.security:
                log.error("❌ No SecuritySystem instance attached")
                return

            value = int(value)

            # Route commands to hardware
            if feed == "motor_status":
                self.security.set_motor(value)
                log.info(f"🔧 Motor set to {value}")

            elif feed == "led_status":
                self.security.set_led(value)
                log.info(f"💡 LED set to {value}")

            elif feed == "buzzer_status":
                self.security.set_buzzer(value)
                log.info(f"🔔 Buzzer set to {value}")

        except Exception as e:
            log.error(f"MQTT on_message error: {e}")

    # -------------------------------------------------------
    def is_security_enabled(self):
        return self.security_enabled

    # -------------------------------------------------------
    # SAFE PUBLISH
    # -------------------------------------------------------
    def publish(self, feed, value):
        try:
            feed_key = self._to_feed_key(feed)
            topic = f"{self.cfg['ADAFRUIT_IO_USERNAME']}/feeds/{feed_key}"

            self.client.publish(topic, str(value))
            log.info(f"📤 Sent → {feed_key}: {value}")
        except Exception as e:
            log.error(f"Publish failed: {e}")
