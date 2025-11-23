import logging
import threading
import time
from datetime import datetime
from modules.camera_handler import CameraHandler
from modules.config_loader import load_config

try:
    from gpiozero import LED, Buzzer, MotionSensor, OutputDevice
    GPIO_AVAILABLE = True
except Exception:
    GPIO_AVAILABLE = False

log = logging.getLogger(__name__)

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

class SecuritySystem:
    _instance = None  # Singleton

    def __new__(cls, *a, **kw):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, use_gpio=False):
        """
        use_gpio=False → Flask mode (NO hardware)
        use_gpio=True  → main.py mode (full hardware)
        """
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.use_gpio = use_gpio and GPIO_AVAILABLE

        cfg = load_config()

        if self.use_gpio:
            self.led = LED(cfg.get("LED_PIN", 16))
            self.buzzer = Buzzer(cfg.get("BUZZER_PIN", 26))
            self.motion = MotionSensor(cfg.get("PIR_PIN", 6))
            self.motor = OutputDevice(cfg.get("MOTOR_PIN", 21))
            log.info("🔒 SecuritySystem initialized with REAL GPIO")
        else:
            self.led = None
            self.buzzer = None
            self.motion = None
            self.motor = None
            log.info("🟦 SecuritySystem initialized in SAFE MODE (no GPIO)")

        self.cam = CameraHandler()

    # -----------------------------------------------------------
    # REMOTE CONTROL (MQTT → main.py only)
    # -----------------------------------------------------------
    @staticmethod
    def set_led(value: int):
        ss = SecuritySystem()
        if not ss.led:
            return
        ss.led.on() if value == 1 else ss.led.off()

    @staticmethod
    def set_buzzer(value: int):
        ss = SecuritySystem()
        if not ss.buzzer:
            return
        ss.buzzer.on() if value == 1 else ss.buzzer.off()

    @staticmethod
    def set_motor(value: int):
        ss = SecuritySystem()
        if not ss.motor:
            return
        ss.motor.on() if value == 1 else ss.motor.off()

    # -----------------------------------------------------------
    # MOTION HANDLING
    # -----------------------------------------------------------
    def _spin_motor(self):
        if not self.motor:
            return
        self.motor.on()
        time.sleep(2)
        self.motor.off()

    def check(self):
        # Flask mode → motion always false
        motion = self.motion.motion_detected if self.motion else False

        led_status = 0
        buzzer_status = 0
        buzzer_pulsed = False
        motor_pulsed = False
        image = None

        if motion:
            log.info("🚨 MOTION DETECTED!")

            if self.led:
                self.led.on()
                led_status = 1

            if self.buzzer:
                self.buzzer.on()
                buzzer_status = 1
                buzzer_pulsed = True

            threading.Thread(target=self._spin_motor, daemon=True).start()
            motor_pulsed = True

            time.sleep(0.8)

            if self.buzzer:
                self.buzzer.off()
                buzzer_status = 0

            image = self.cam.capture_b64()

        else:
            if self.led:
                self.led.off()
            if self.buzzer:
                self.buzzer.off()

        return {
            "timestamp": datetime.now().isoformat(),
            "motion": motion,
            "led_status": led_status,
            "buzzer_status": buzzer_status,
            "buzzer_pulsed": buzzer_pulsed,
            "motor_pulsed": motor_pulsed,
            "image_b64": image
        }
