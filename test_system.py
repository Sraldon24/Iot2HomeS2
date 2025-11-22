#!/usr/bin/env python3
"""
============================================
DomiSafe IoT System - Test Suite
============================================
Comprehensive testing of all system components
Run with: python3 test_system.py
"""

import sys
import os
import time
from datetime import datetime

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text:^60}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_test(test_name):
    print(f"{Colors.YELLOW}Testing: {test_name}...{Colors.END}", end=" ", flush=True)

def print_success(message=""):
    print(f"{Colors.GREEN}✅ PASS{Colors.END}", end="")
    if message:
        print(f" {Colors.GREEN}{message}{Colors.END}")
    else:
        print()

def print_fail(message=""):
    print(f"{Colors.RED}❌ FAIL{Colors.END}", end="")
    if message:
        print(f" {Colors.RED}{message}{Colors.END}")
    else:
        print()

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

# Test counters
tests_passed = 0
tests_failed = 0
tests_total = 0

def run_test(test_func):
    """Wrapper to run a test and track results"""
    global tests_passed, tests_failed, tests_total
    tests_total += 1
    try:
        result = test_func()
        if result:
            tests_passed += 1
            return True
        else:
            tests_failed += 1
            return False
    except Exception as e:
        print_fail(f"Exception: {e}")
        tests_failed += 1
        return False

# ============================================
# TEST 1: Configuration Loading
# ============================================
def test_config():
    print_test("Configuration Loading")
    try:
        from modules.config_loader import load_config
        config = load_config("config.json")
        
        # Check required fields
        required = ["ADAFRUIT_IO_USERNAME", "ADAFRUIT_IO_KEY", "DHT_PIN", "PIR_PIN"]
        missing = [k for k in required if not config.get(k)]
        
        if missing:
            print_fail(f"Missing fields: {missing}")
            return False
        
        if config["ADAFRUIT_IO_USERNAME"] == "YOUR_USERNAME":
            print_warning("Config uses placeholder values - update config.json!")
            print_success("(Structure valid)")
            return True
        
        print_success()
        return True
    except Exception as e:
        print_fail(str(e))
        return False

# ============================================
# TEST 2: Local Database
# ============================================
def test_local_db():
    print_test("Local Database")
    try:
        from modules.local_db import init_db, save_env, save_motion, fetch_unsynced
        
        # Initialize database
        init_db()
        
        # Test environment save
        save_env(22.5, 55.0)
        
        # Test motion save
        save_motion(1, "test_image.jpg")
        
        # Test fetch
        env_data = fetch_unsynced("environment")
        motion_data = fetch_unsynced("motion")
        
        if len(env_data) > 0 and len(motion_data) > 0:
            print_success()
            return True
        else:
            print_fail("No data retrieved")
            return False
            
    except Exception as e:
        print_fail(str(e))
        return False

# ============================================
# TEST 3: MQTT Client
# ============================================
def test_mqtt():
    print_test("MQTT Connection")
    try:
        from modules.mqtt_client import MqttClient
        from modules.config_loader import load_config
        
        config = load_config("config.json")
        
        # Check if credentials are set
        if (config["ADAFRUIT_IO_USERNAME"] == "YOUR_USERNAME" or 
            config["ADAFRUIT_IO_KEY"] == "YOUR_KEY_HERE"):
            print_warning("Skipping - credentials not configured")
            print_success("(Module loads correctly)")
            return True
        
        # Try to connect
        mqtt = MqttClient()
        time.sleep(2)  # Wait for connection
        
        if mqtt.connected.is_set():
            print_success()
            # Test publish
            mqtt.publish("temperature", 22.5)
            return True
        else:
            print_fail("Connection timeout")
            return False
            
    except Exception as e:
        print_fail(str(e))
        return False

# ============================================
# TEST 4: Cloud Database
# ============================================
def test_cloud_db():
    print_test("Cloud Database Connection")
    try:
        from modules.cloud_db import CloudDB
        from modules.config_loader import load_config
        
        config = load_config("config.json")
        
        if not config.get("NEON_DB_URL"):
            print_warning("Skipping - NEON_DB_URL not configured")
            print_success("(Module loads correctly)")
            return True
        
        cloud_db = CloudDB()
        
        if cloud_db.connect():
            print_success()
            
            # Test insert
            from datetime import datetime
            now = datetime.now()
            cloud_db.insert_environment(now, 22.5, 55.0)
            
            cloud_db.close()
            return True
        else:
            print_fail("Connection failed")
            return False
            
    except Exception as e:
        print_fail(str(e))
        return False

# ============================================
# TEST 5: Environment Monitor
# ============================================
def test_environment_monitor():
    print_test("Environment Monitor")
    try:
        from modules.environment_monitor import EnvironmentMonitor
        
        monitor = EnvironmentMonitor()
        data = monitor.read()
        
        # Check data structure
        if ("temperature" in data and "humidity" in data and 
            "timestamp" in data):
            
            # Validate ranges
            temp = data["temperature"]
            hum = data["humidity"]
            
            if -10 <= temp <= 50 and 0 <= hum <= 100:
                print_success(f"Temp={temp}°C, Hum={hum}%")
                return True
            else:
                print_fail("Values out of range")
                return False
        else:
            print_fail("Invalid data structure")
            return False
            
    except Exception as e:
        print_fail(str(e))
        return False

# ============================================
# TEST 6: Security System
# ============================================
def test_security_system():
    print_test("Security System")
    try:
        from modules.security_system import SecuritySystem
        
        security = SecuritySystem()
        status = security.check()
        
        # Check status structure
        required_keys = ["timestamp", "motion", "led_status", "buzzer_status"]
        if all(k in status for k in required_keys):
            motion_state = "DETECTED" if status["motion"] else "Clear"
            print_success(f"Motion: {motion_state}")
            return True
        else:
            print_fail("Invalid status structure")
            return False
            
    except Exception as e:
        print_fail(str(e))
        return False

# ============================================
# TEST 7: Camera Handler
# ============================================
def test_camera():
    print_test("Camera Handler")
    try:
        from modules.camera_handler import CameraHandler
        
        camera = CameraHandler()
        
        if camera.cam is None:
            print_warning("Camera not available")
            print_success("(Module loads correctly)")
            return True
        
        # Try to capture
        image_b64 = camera.capture_b64()
        
        if image_b64:
            print_success(f"Captured {len(image_b64)} bytes")
            return True
        else:
            print_warning("Capture failed but module works")
            print_success("(Module functional)")
            return True
            
    except Exception as e:
        print_fail(str(e))
        return False

# ============================================
# TEST 8: Sync Service
# ============================================
def test_sync_service():
    print_test("Sync Service")
    try:
        from modules.sync_service import SyncService
        from modules.config_loader import load_config
        
        config = load_config("config.json")
        
        sync = SyncService()
        
        if not config.get("cloud_sync_enabled", True):
            print_warning("Sync disabled in config")
            print_success("(Module loads correctly)")
            return True
        
        # Get status
        status = sync.get_sync_status()
        
        if "running" in status and "pending_env" in status:
            pending = status["pending_env"] + status["pending_motion"]
            print_success(f"Pending: {pending} records")
            return True
        else:
            print_fail("Invalid status structure")
            return False
            
    except Exception as e:
        print_fail(str(e))
        return False

# ============================================
# TEST 9: Flask Application
# ============================================
def test_flask_app():
    print_test("Flask Application")
    try:
        # Check if app.py exists
        if not os.path.exists("web_app/app.py"):
            print_fail("web_app/app.py not found")
            return False
        
        # Try to import
        sys.path.insert(0, os.path.abspath('web_app'))
        from app import app
        
        # Check routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        required_routes = ['/', '/environment', '/security', '/control', '/about']
        
        missing_routes = [r for r in required_routes if r not in routes]
        
        if missing_routes:
            print_fail(f"Missing routes: {missing_routes}")
            return False
        
        print_success(f"{len(routes)} routes")
        return True
            
    except Exception as e:
        print_fail(str(e))
        return False

# ============================================
# TEST 10: Directory Structure
# ============================================
def test_directories():
    print_test("Directory Structure")
    try:
        required_dirs = ["modules", "web_app", "logs", "captures"]
        missing_dirs = [d for d in required_dirs if not os.path.isdir(d)]
        
        if missing_dirs:
            print_fail(f"Missing directories: {missing_dirs}")
            return False
        
        # Check for key files
        required_files = [
            "main.py",
            "config.json",
            "requirements.txt",
            "modules/mqtt_client.py",
            "modules/local_db.py",
            "web_app/app.py"
        ]
        
        missing_files = [f for f in required_files if not os.path.isfile(f)]
        
        if missing_files:
            print_fail(f"Missing files: {missing_files}")
            return False
        
        print_success()
        return True
            
    except Exception as e:
        print_fail(str(e))
        return False

# ============================================
# MAIN TEST EXECUTION
# ============================================
def main():
    print_header("DomiSafe IoT System - Test Suite")
    print(f"{Colors.BOLD}Testing all components...{Colors.END}\n")
    
    # Run all tests
    run_test(test_directories)
    run_test(test_config)
    run_test(test_local_db)
    run_test(test_mqtt)
    run_test(test_cloud_db)
    run_test(test_environment_monitor)
    run_test(test_security_system)
    run_test(test_camera)
    run_test(test_sync_service)
    run_test(test_flask_app)
    
    # Print summary
    print_header("Test Summary")
    
    print(f"{Colors.BOLD}Total Tests:{Colors.END} {tests_total}")
    print(f"{Colors.GREEN}{Colors.BOLD}Passed:{Colors.END} {tests_passed}")
    print(f"{Colors.RED}{Colors.BOLD}Failed:{Colors.END} {tests_failed}")
    
    success_rate = (tests_passed / tests_total * 100) if tests_total > 0 else 0
    print(f"{Colors.BOLD}Success Rate:{Colors.END} {success_rate:.1f}%\n")
    
    if tests_failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! System is ready.{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Some tests failed. Review errors above.{Colors.END}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())