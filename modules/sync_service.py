import logging
import time
import threading
from modules.local_db import fetch_unsynced, mark_synced
from modules.cloud_db import CloudDB
from modules.config_loader import load_config

log = logging.getLogger(__name__)

class SyncService:
    def __init__(self, config_path="config.json"):
        cfg = load_config(config_path)
        self.interval = cfg.get('sync_interval', 60)
        self.enabled = cfg.get('cloud_sync_enabled', True)
        self.cloud_db = CloudDB(config_path)
        self.running = False
        self.thread = None
        self.last_sync_time = None
        
    def start(self):
        if not self.enabled:
            log.info("⚠️ Cloud sync disabled in config")
            return
        if self.running:
            log.warning("Sync already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()
        log.info(f"🔄 Sync started (interval: {self.interval}s)")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.cloud_db.close()
        log.info("Sync stopped")
    
    def _sync_loop(self):
        while self.running:
            try:
                self.sync_all()
            except Exception as e:
                log.error(f"Sync error: {e}")
            time.sleep(self.interval)
    
    def sync_all(self):
        if not self.cloud_db.conn:
            if not self.cloud_db.connect():
                log.debug("Cloud DB unavailable")
                return
        
        env_synced = self._sync_table('environment')
        motion_synced = self._sync_table('motion')
        
        if env_synced > 0 or motion_synced > 0:
            self.last_sync_time = time.time()
            log.info(f"✅ Synced {env_synced} env + {motion_synced} motion")
    
    def _sync_table(self, table_name):
        rows = fetch_unsynced(table_name)
        if not rows:
            return 0
        
        synced_ids = []
        for row in rows:
            row_id = row[0]
            timestamp = row[1]
            
            try:
                if table_name == 'environment':
                    success = self.cloud_db.insert_environment(
                        timestamp, row[2], row[3]
                    )
                elif table_name == 'motion':
                    success = self.cloud_db.insert_motion(
                        timestamp, row[2], row[3] if len(row) > 3 else None
                    )
                else:
                    success = False
                
                if success:
                    synced_ids.append(row_id)
                else:
                    break
            except Exception as e:
                log.error(f"Sync row failed: {e}")
                break
        
        if synced_ids:
            mark_synced(table_name, synced_ids)
        
        return len(synced_ids)
    
    def get_sync_status(self):
        env_unsynced = len(fetch_unsynced('environment'))
        motion_unsynced = len(fetch_unsynced('motion'))
        
        return {
            'running': self.running,
            'connected': self.cloud_db.conn is not None,
            'last_sync': self.last_sync_time,
            'pending_env': env_unsynced,
            'pending_motion': motion_unsynced
        }