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


class SecuritySystem:
    """
    Cleaned + Fixed:
    - NO more singleton
    - NO duplicated MqttClient
    - Supports both Flask (safe mode) and main.py (GPIO mode)
    """

    def __init__(self, use_gpio=False):
        self.use_gpio = use_gpio and GPIO_AVAILABLE

        cfg = load_config()

        # REAL hardware mode (main.py)
        if self.use_gpio:
            self.led = LED(cfg.get("LED_PIN", 16))
            self.buzzer = Buzzer(cfg.get("BUZZER_PIN", 26))
            self.motion = MotionSensor(cfg.get("PIR_PIN", 6))
            self.motor = OutputDevice(cfg.get("MOTOR_PIN", 21))
            log.info("🔒 SecuritySystem initialized with REAL GPIO")

        # SAFE mode (Flask app)
        else:
            self.led = None
            self.buzzer = None
            self.motion = None
            self.motor = None
            log.info("🟦 SecuritySystem initialized in SAFE MODE (no GPIO)")

        self.cam = CameraHandler()

    # -----------------------------------------------------------
    # DIRECT CONTROL METHODS (called by MQTT or Flask)
    # -----------------------------------------------------------

    def set_led(self, value: int):
        if not self.led:
            return
        if value == 1:
            self.led.on()
        else:
            self.led.off()

    def set_buzzer(self, value: int):
        if not self.buzzer:
            return
        if value == 1:
            self.buzzer.on()
        else:
            self.buzzer.off()

    def set_motor(self, value: int):
        if not self.motor:
            return
        if value == 1:
            self.motor.on()
        else:
            self.motor.off()

    # -----------------------------------------------------------
    # INTERNAL MOTOR PULSE
    # -----------------------------------------------------------
    def _spin_motor(self):
        if not self.motor:
            return
        self.motor.on()
        time.sleep(2)
        self.motor.off()

    # -----------------------------------------------------------
    # MOTION DETECTION LOOP LOGIC
    # -----------------------------------------------------------
    def check(self):
        # In Flask safe mode → motion always off
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

            # Pulse motor async
            threading.Thread(target=self._spin_motor, daemon=True).start()
            motor_pulsed = True

            time.sleep(0.8)

            if self.buzzer:
                self.buzzer.off()
                buzzer_status = 0

            # Capture image
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
