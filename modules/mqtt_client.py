"""
============================================
DomiSafe IoT System - MQTT Client (FIXED)
============================================
Fixed: Added security_enabled to subscriptions
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

        # IMPORTANT: store the real hardware SecuritySystem instance
        self.security = security
        
        # Track security enabled state (for main.py to check)
        self.security_enabled = True

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

        # Flask mode → DO NOT subscribe
        if not self.subscribe:
            log.info("ℹ️ MQTT client running in PUBLISH-ONLY mode (no subscriptions)")
            return

        # Subscribe to control feeds from Adafruit IO
        username = self.cfg["ADAFRUIT_IO_USERNAME"]

        # FIXED: Added security_enabled to the list
        control_feeds = [
            "motor_status",
            "led_status",
            "buzzer_status",
            "security_enabled"  # ← ADDED THIS
        ]

        for feed in control_feeds:
            topic = f"{username}/feeds/{feed}"
            self.client.subscribe(topic)
            log.info(f"📡 Subscribed to: {topic}")

    def _on_disconnect(self, client, userdata, rc):
        log.warning("⚠️ MQTT disconnected")
        self.connected.clear()

    # -----------------------------
    # HANDLE INCOMING COMMANDS
    # -----------------------------
    def _on_message(self, client, userdata, msg):
        # Flask mode should never receive messages
        if not self.subscribe:
            return

        try:
            topic = msg.topic
            value = msg.payload.decode().strip()
            feed = topic.split("/")[-1]

            log.info(f"📥 Received → {feed} = {value}")

            # Handle security_enabled toggle
            if feed == "security_enabled":
                self.security_enabled = (value == "1")
                status = "ENABLED" if self.security_enabled else "DISABLED"
                log.info(f"🔐 Security system {status}")
                return

            # Ensure security instance exists for device control
            if not self.security:
                log.error("❌ No SecuritySystem instance attached to MqttClient")
                return

            value = int(value)

            # Route command to the REAL hardware instance
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

    # -----------------------------
    # CHECK IF SECURITY IS ENABLED
    # -----------------------------
    def is_security_enabled(self):
        """Returns current security enabled state"""
        return self.security_enabled

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