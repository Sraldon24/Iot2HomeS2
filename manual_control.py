#!/usr/bin/env python3
"""
============================================
DomiSafe IoT System - Manual Control
============================================
Interactive CLI for testing individual devices
Run with: python3 manual_control.py
"""

import sys
import time
from modules.config_loader import load_config

try:
    from gpiozero import LED, Buzzer, OutputDevice, MotionSensor
    HW_OK = True
except ImportError:
    HW_OK = False
    print("⚠️  gpiozero not available - simulation mode")

try:
    import adafruit_dht
    import board
    DHT_OK = True
except ImportError:
    DHT_OK = False
    print("⚠️  DHT library not available")

from modules.camera_handler import CameraHandler
from modules.mqtt_client import MqttClient
from modules.environment_monitor import EnvironmentMonitor

class ManualControl:
    """Interactive control interface for DomiSafe devices"""
    
    def __init__(self):
        self.config = load_config()
        
        # Initialize hardware
        if HW_OK:
            self.led = LED(self.config.get("LED_PIN", 16))
            self.buzzer = Buzzer(self.config.get("BUZZER_PIN", 26))
            self.motor = OutputDevice(self.config.get("MOTOR_PIN", 21))
            self.pir = MotionSensor(self.config.get("PIR_PIN", 6))
        else:
            self.led = None
            self.buzzer = None
            self.motor = None
            self.pir = None
        
        # Initialize modules
        self.camera = CameraHandler()
        self.mqtt = None
        self.env_monitor = EnvironmentMonitor()
    
    def print_menu(self):
        """Display main menu"""
        print("\n" + "="*50)
        print("🏠 DomiSafe - Manual Control Interface")
        print("="*50)
        print("\n🔧 Device Controls:")
        print("  1. Toggle LED")
        print("  2. Toggle Buzzer")
        print("  3. Pulse Motor (2 sec)")
        print("  4. Test All Actuators")
        print("\n📊 Sensors:")
        print("  5. Read Temperature/Humidity")
        print("  6. Check Motion Sensor")
        print("  7. Capture Camera Image")
        print("\n📡 MQTT:")
        print("  8. Connect to Adafruit IO")
        print("  9. Publish Test Data")
        print("  10. Disconnect MQTT")
        print("\n⚙️  System:")
        print("  11. Test All Systems")
        print("  12. Show Config")
        print("  0. Exit")
        print("="*50)
    
    def toggle_led(self):
        """Toggle LED on/off"""
        if not self.led:
            print("❌ LED not available")
            return
        
        if self.led.is_lit:
            self.led.off()
            print("💡 LED: OFF")
        else:
            self.led.on()
            print("💡 LED: ON")
    
    def toggle_buzzer(self):
        """Toggle buzzer on/off"""
        if not self.buzzer:
            print("❌ Buzzer not available")
            return
        
        if self.buzzer.is_active:
            self.buzzer.off()
            print("🔇 Buzzer: OFF")
        else:
            self.buzzer.on()
            print("🔊 Buzzer: ON")
            print("⚠️  Remember to turn off manually!")
    
    def pulse_motor(self):
        """Pulse motor for 2 seconds"""
        if not self.motor:
            print("❌ Motor not available")
            return
        
        print("🌀 Motor: ON")
        self.motor.on()
        time.sleep(2)
        self.motor.off()
        print("🌀 Motor: OFF")
    
    def test_all_actuators(self):
        """Test all actuators in sequence"""
        print("\n🔧 Testing all actuators...")
        
        # LED
        print("💡 Testing LED...")
        if self.led:
            self.led.on()
            time.sleep(1)
            self.led.off()
            print("✅ LED OK")
        
        # Buzzer
        print("🔊 Testing Buzzer...")
        if self.buzzer:
            self.buzzer.on()
            time.sleep(0.5)
            self.buzzer.off()
            print("✅ Buzzer OK")
        
        # Motor
        print("🌀 Testing Motor...")
        if self.motor:
            self.motor.on()
            time.sleep(1)
            self.motor.off()
            print("✅ Motor OK")
        
        print("✅ All actuators tested")
    
    def read_environment(self):
        """Read temperature and humidity"""
        print("\n🌡️  Reading environment sensor...")
        data = self.env_monitor.read()
        
        print(f"  Temperature: {data['temperature']}°C")
        print(f"  Humidity: {data['humidity']}%")
        print(f"  Timestamp: {data['timestamp']}")
    
    def check_motion(self):
        """Check motion sensor status"""
        if not self.pir:
            print("❌ Motion sensor not available")
            return
        
        print("\n👁️  Motion Sensor Status:")
        if self.pir.motion_detected:
            print("  🔴 MOTION DETECTED!")
        else:
            print("  🟢 No motion")
        
        print("\n  Monitoring for 10 seconds...")
        print("  (Wave hand in front of PIR sensor)")
        
        start = time.time()
        detected = False
        
        while time.time() - start < 10:
            if self.pir.motion_detected and not detected:
                print("  🔴 MOTION! " + time.strftime("%H:%M:%S"))
                detected = True
            time.sleep(0.1)
        
        if not detected:
            print("  No motion detected during test")
    
    def capture_image(self):
        """Capture an image"""
        print("\n📸 Capturing image...")
        
        image_b64 = self.camera.capture_b64()
        
        if image_b64:
            print(f"✅ Image captured ({len(image_b64)} bytes)")
            print(f"  Saved to: captures/")
        else:
            print("❌ Image capture failed")
    
    def connect_mqtt(self):
        """Connect to Adafruit IO"""
        if self.mqtt and self.mqtt.connected.is_set():
            print("✅ Already connected to MQTT")
            return
        
        print("\n📡 Connecting to Adafruit IO...")
        try:
            self.mqtt = MqttClient()
            if self.mqtt.connected.wait(10):
                print("✅ Connected to Adafruit IO")
            else:
                print("❌ Connection timeout")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    
    def publish_test_data(self):
        """Publish test data to Adafruit IO"""
        if not self.mqtt or not self.mqtt.connected.is_set():
            print("❌ Not connected to MQTT. Run option 8 first.")
            return
        
        print("\n📤 Publishing test data...")
        
        # Read real sensor data
        env_data = self.env_monitor.read()
        
        # Publish
        self.mqtt.publish("temperature", env_data["temperature"])
        self.mqtt.publish("humidity", env_data["humidity"])
        self.mqtt.publish("motion", 1 if (self.pir and self.pir.motion_detected) else 0)
        
        print("✅ Test data published")
    
    def disconnect_mqtt(self):
        """Disconnect from MQTT"""
        if not self.mqtt:
            print("❌ Not connected")
            return
        
        print("\n📡 Disconnecting from MQTT...")
        self.mqtt.client.loop_stop()
        self.mqtt.client.disconnect()
        self.mqtt = None
        print("✅ Disconnected")
    
    def test_all_systems(self):
        """Run comprehensive system test"""
        print("\n" + "="*50)
        print("🧪 COMPREHENSIVE SYSTEM TEST")
        print("="*50)
        
        # Test 1: Configuration
        print("\n1️⃣  Configuration:")
        if self.config:
            print("  ✅ Config loaded")
            print(f"  - Adafruit username: {self.config.get('ADAFRUIT_IO_USERNAME')}")
            print(f"  - DHT pin: {self.config.get('DHT_PIN')}")
            print(f"  - PIR pin: {self.config.get('PIR_PIN')}")
        else:
            print("  ❌ Config failed")
        
        # Test 2: Hardware
        print("\n2️⃣  Hardware:")
        hw_count = sum([self.led is not None, self.buzzer is not None, 
                       self.motor is not None, self.pir is not None])
        print(f"  {hw_count}/4 devices available")
        
        # Test 3: Sensors
        print("\n3️⃣  Sensors:")
        try:
            data = self.env_monitor.read()
            print(f"  ✅ Environment: {data['temperature']}°C, {data['humidity']}%")
        except Exception as e:
            print(f"  ❌ Environment: {e}")
        
        if self.pir:
            print(f"  ✅ Motion: {'Detected' if self.pir.motion_detected else 'Clear'}")
        
        # Test 4: Camera
        print("\n4️⃣  Camera:")
        if self.camera.cam:
            print("  ✅ Camera available")
        else:
            print("  ⚠️  Camera not available")
        
        # Test 5: MQTT
        print("\n5️⃣  MQTT:")
        if self.mqtt and self.mqtt.connected.is_set():
            print("  ✅ Connected to Adafruit IO")
        else:
            print("  ⚠️  Not connected (use option 8)")
        
        print("\n" + "="*50)
        print("✅ System test complete")
        print("="*50)
    
    def show_config(self):
        """Display current configuration"""
        print("\n⚙️  Current Configuration:")
        print("="*50)
        
        # Hardware pins
        print("\n📌 GPIO Pins:")
        print(f"  DHT11:  BCM {self.config.get('DHT_PIN')}")
        print(f"  PIR:    BCM {self.config.get('PIR_PIN')}")
        print(f"  LED:    BCM {self.config.get('LED_PIN')}")
        print(f"  Buzzer: BCM {self.config.get('BUZZER_PIN')}")
        print(f"  Motor:  BCM {self.config.get('MOTOR_PIN')}")
        
        # MQTT
        print("\n📡 MQTT:")
        print(f"  Broker: {self.config.get('MQTT_BROKER')}")
        print(f"  Port:   {self.config.get('MQTT_PORT')}")
        print(f"  User:   {self.config.get('ADAFRUIT_IO_USERNAME')}")
        
        # Database
        print("\n💾 Database:")
        neon_url = self.config.get('NEON_DB_URL', '')
        if neon_url:
            # Hide password
            import re
            masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', neon_url)
            print(f"  Neon: {masked}")
        else:
            print("  Neon: Not configured")
        
        # Features
        print("\n🔧 Features:")
        print(f"  Camera:      {self.config.get('camera_enabled', False)}")
        print(f"  Cloud Sync:  {self.config.get('cloud_sync_enabled', False)}")
        print(f"  Google Drive: {self.config.get('google_drive_enabled', False)}")
        
        print("="*50)
    
    def cleanup(self):
        """Clean up resources"""
        if self.led:
            self.led.off()
        if self.buzzer:
            self.buzzer.off()
        if self.motor:
            self.motor.off()
        if self.mqtt:
            self.mqtt.client.loop_stop()
    
    def run(self):
        """Main control loop"""
        print("\n🏠 Welcome to DomiSafe Manual Control")
        
        try:
            while True:
                self.print_menu()
                choice = input("\nEnter choice: ").strip()
                
                if choice == "1":
                    self.toggle_led()
                elif choice == "2":
                    self.toggle_buzzer()
                elif choice == "3":
                    self.pulse_motor()
                elif choice == "4":
                    self.test_all_actuators()
                elif choice == "5":
                    self.read_environment()
                elif choice == "6":
                    self.check_motion()
                elif choice == "7":
                    self.capture_image()
                elif choice == "8":
                    self.connect_mqtt()
                elif choice == "9":
                    self.publish_test_data()
                elif choice == "10":
                    self.disconnect_mqtt()
                elif choice == "11":
                    self.test_all_systems()
                elif choice == "12":
                    self.show_config()
                elif choice == "0":
                    print("\n👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice")
                
                input("\nPress Enter to continue...")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
        finally:
            self.cleanup()

def main():
    """Entry point"""
    controller = ManualControl()
    controller.run()

if __name__ == "__main__":
    main()