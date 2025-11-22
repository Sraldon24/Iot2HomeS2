import time, threading, logging, signal, sys, os
from datetime import datetime
from modules.mqtt_client import MqttClient
from modules.security_system import SecuritySystem
from modules.environment_monitor import EnvironmentMonitor
from modules.local_db import init_db, save_env, save_motion
from modules.sync_service import SyncService

os.makedirs("logs", exist_ok=True)
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = f"logs/run_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("domisafe")

RUNNING = True
sync_service = None

def stop_all(signum=None, frame=None):
    global RUNNING, sync_service
    log.info("🛑 Shutting down...")
    RUNNING = False
    if sync_service:
        sync_service.stop()
    time.sleep(1)
    sys.exit(0)

signal.signal(signal.SIGINT, stop_all)
signal.signal(signal.SIGTERM, stop_all)

def main():
    global RUNNING, sync_service
    
    log.info("=" * 50)
    log.info("🏠 DomiSafe IoT System")
    log.info("=" * 50)
    
    try:
        init_db()
        mqtt = MqttClient()
        security = SecuritySystem()
        environment = EnvironmentMonitor()
        sync_service = SyncService()
        sync_service.start()
        log.info("✅ All systems ready")
    except Exception as e:
        log.error(f"❌ Init failed: {e}")
        sys.exit(1)
    
    time.sleep(2)
    
    def environment_loop():
        log.info("🌡️ Environment monitoring started")
        while RUNNING:
            try:
                data = environment.read()
                mqtt.publish("temperature", data["temperature"])
                mqtt.publish("humidity", data["humidity"])
                save_env(data["temperature"], data["humidity"])
            except Exception as e:
                log.error(f"Env error: {e}")
            time.sleep(30)
        log.info("🌡️ Environment stopped")
    
    def security_loop():
        log.info("🔒 Security monitoring started")
        while RUNNING:
            try:
                status = security.check()
                mqtt.publish("motion", int(status["motion"]))
                mqtt.publish("led_status", status["led_status"])
                
                if status.get("buzzer_pulsed"):
                    mqtt.publish("buzzer_status", 1)
                    time.sleep(0.3)
                    mqtt.publish("buzzer_status", 0)
                else:
                    mqtt.publish("buzzer_status", status["buzzer_status"])
                
                if status.get("motor_pulsed"):
                    mqtt.publish("motor_status", 1)
                    time.sleep(0.3)
                    mqtt.publish("motor_status", 0)
                
                if status["image_b64"]:
                    mqtt.publish("camera_last_image", status["image_b64"])
                
                if status["motion"]:
                    img_name = f"motion_{datetime.now():%Y%m%d_%H%M%S}.jpg"
                    save_motion(1, img_name)
            except Exception as e:
                log.error(f"Security error: {e}")
            time.sleep(5)
        log.info("🔒 Security stopped")
    
    threading.Thread(target=environment_loop, daemon=True).start()
    
    try:
        security_loop()
    except KeyboardInterrupt:
        log.info("Keyboard interrupt")
    
    stop_all()

if __name__ == "__main__":
    try:
        main()
    finally:
        log.info("📤 Uploading logs...")
        try:
            if os.path.exists("upload_logs.py"):
                os.system("python3 upload_logs.py")
        except Exception as e:
            log.error(f"Upload failed: {e}")