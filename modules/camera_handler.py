import logging, base64, os, cv2
from datetime import datetime
try:
    from picamera2 import Picamera2
except Exception:
    Picamera2 = None

log = logging.getLogger(__name__)

class CameraHandler:
    def __init__(self):
        os.makedirs("captures", exist_ok=True)
        self.cam = None
        if Picamera2:
            try:
                self.cam = Picamera2()
                self.cam.start()
                log.info("📸 Camera ready")
            except Exception as e:
                log.warning(f"Camera init failed: {e}")

    def capture_b64(self):
        if not self.cam:
            return None
        try:
            frame = self.cam.capture_array()
            frame = cv2.resize(frame, (640, 480))
            path = f"captures/motion_{datetime.now():%Y%m%d_%H%M%S}.jpg"
            cv2.imwrite(path, frame)
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except Exception as e:
            log.warning(f"Capture failed: {e}")
            return None