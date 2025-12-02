import psycopg2
import logging
from modules.config_loader import load_config
from typing import Optional

log = logging.getLogger(__name__)


class CloudDB:
    def __init__(self, config_path: str = "config.json", db_url: Optional[str] = None):
        """CloudDB can be constructed either with a `db_url` override or
        by loading `NEON_DB_URL` from the provided `config_path`.
        """
        cfg = load_config(config_path)
        # prefer explicit db_url override, otherwise use config
        self.conn_string = db_url if db_url else cfg.get("NEON_DB_URL", "")
        self.conn = None
        self.enabled = cfg.get("cloud_sync_enabled", True)
        
    def connect(self):
        try:
            if not self.conn_string:
                log.warning("⚠️ No NEON_DB_URL in config")
                return False
            
            self.conn = psycopg2.connect(self.conn_string)
            log.info("✅ Connected to cloud database")
            self._init_tables()
            return True
        except Exception as e:
            log.error(f"❌ Cloud DB connection failed: {e}")
            return False
    
    def _init_tables(self):
        if not self.conn:
            return
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS environment (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP,
                        temperature REAL,
                        humidity REAL,
                        device_id VARCHAR(50) DEFAULT 'pi_home_security'
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS motion_events (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP,
                        motion INTEGER,
                        image_name TEXT,
                        device_id VARCHAR(50) DEFAULT 'pi_home_security'
                    )
                """)
                self.conn.commit()
                log.info("✅ Cloud tables initialized")
        except Exception as e:
            log.error(f"Failed to init tables: {e}")
    
    def insert_environment(self, timestamp, temperature, humidity):
        if not self.conn:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO environment (timestamp, temperature, humidity)
                    VALUES (%s, %s, %s)
                """, (timestamp, temperature, humidity))
                self.conn.commit()
            return True
        except Exception as e:
            log.error(f"Insert env failed: {e}")
            self.conn = None
            return False
    
    def insert_motion(self, timestamp, motion, image_name=None):
        if not self.conn:
            return False
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO motion_events (timestamp, motion, image_name)
                    VALUES (%s, %s, %s)
                """, (timestamp, motion, image_name))
                self.conn.commit()
            return True
        except Exception as e:
            log.error(f"Insert motion failed: {e}")
            self.conn = None
            return False
    
    def get_environment_by_date(self, date_str):
        if not self.conn:
            if not self.connect():
                return []
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, temperature, humidity 
                    FROM environment 
                    WHERE DATE(timestamp) = %s
                    ORDER BY timestamp
                """, (date_str,))
                return cur.fetchall()
        except Exception as e:
            log.error(f"Query failed: {e}")
            return []
    
    def get_motion_by_date(self, date_str):
        if not self.conn:
            if not self.connect():
                return []
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, motion, image_name 
                    FROM motion_events 
                    WHERE DATE(timestamp) = %s
                    ORDER BY timestamp DESC
                """, (date_str,))
                return cur.fetchall()
        except Exception as e:
            log.error(f"Query failed: {e}")
            return []
    
    def get_latest_environment(self, limit=10):
        if not self.conn:
            if not self.connect():
                return []
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, temperature, humidity 
                    FROM environment 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (limit,))
                return cur.fetchall()
        except Exception as e:
            log.error(f"Query failed: {e}")
            return []
    
    def get_latest_motion(self, limit=10):
        if not self.conn:
            if not self.connect():
                return []
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, motion, image_name 
                    FROM motion_events 
                    ORDER BY timestamp DESC 
                    LIMIT %s
                """, (limit,))
                return cur.fetchall()
        except Exception as e:
            log.error(f"Query failed: {e}")
            return []
    
    def close(self):
        if self.conn:
            self.conn.close()
            log.info("Cloud DB closed")