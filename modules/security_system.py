import logging, threading, time
from datetime import datetime
from modules.camera_handler import CameraHandler
from modules.config_loader import load_config

try:
    from gpiozero import LED, Buzzer, MotionSensor, OutputDevice
    HW_OK = True
except Exception:
    HW_OK = False

log = logging.getLogger(__name__)

class SecuritySystem:
    def __init__(self):
        cfg = load_config()
        if HW_OK:
            self.led = LED(cfg.get("LED_PIN", 16))
            self.buzzer = Buzzer(cfg.get("BUZZER_PIN", 26))
            self.motion = MotionSensor(cfg.get("PIR_PIN", 6))
            self.motor = OutputDevice(cfg.get("MOTOR_PIN", 21))
        else:
            self.led = None
            self.buzzer = None
            self.motion = None
            self.motor = None
        self.cam = CameraHandler()

    def _spin_motor(self):
        if not self.motor:
            return
        log.info("Motor spin")
        self.motor.on()
        time.sleep(2)
        self.motor.off()

    def check(self):
        motion = self.motion.motion_detected if self.motion else False
        led_status = 0
        buzzer_status = 0
        buzzer_pulsed = False
        motor_pulsed = False
        image = None

        if motion:
            log.info("🚨 MOTION!")
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