#!/usr/bin/env python3
"""
============================================
DomiSafe IoT System - Google Drive Uploader
============================================
Uploads logs + captured images using a SERVICE ACCOUNT
NO browser login, NO OAuth screen, works instantly.
"""

import os
import sys
import logging
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from modules.config_loader import load_config

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("upload_logs")

# Required Drive scopes
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

SERVICE_ACCOUNT_FILE = "service_account.json"


class GoogleDriveUploader:

    def __init__(self, config_path="config.json"):
        self.config = load_config(config_path)
        self.enabled = self.config.get("google_drive_enabled", False)
        self.log_folder_id = self.config.get("google_drive_log_folder_id", "")
        self.image_folder_id = self.config.get("google_drive_image_folder_id", "")
        self.service = None

        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            log.error("❌ Missing service_account.json")
            self.enabled = False

    # ----------------------------------------------------
    # AUTH (service account)
    # ----------------------------------------------------
    def authenticate(self):
        if not self.enabled:
            log.warning("⚠️ Google Drive upload disabled in config.json")
            return False

        try:
            creds = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE,
                scopes=SCOPES
            )

            self.service = build("drive", "v3", credentials=creds)
            log.info("✅ Google Drive service ready (service account).")
            return True

        except Exception as e:
            log.error(f"❌ Authentication failed: {e}")
            return False

    # ----------------------------------------------------
    # Upload file
    # ----------------------------------------------------
    def upload_file(self, file_path, folder_id, mime_type):
        if not self.service:
            log.error("❌ Service not initialized")
            return False

        try:
            file_name = os.path.basename(file_path)

            file_metadata = {
                "name": file_name,
                "parents": [folder_id]
            }

            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)

            uploaded = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()

            log.info(f"📤 Uploaded: {file_name}")
            return True

        except Exception as e:
            log.error(f"❌ Failed to upload {file_name}: {e}")
            return False

    # ----------------------------------------------------
    # Upload logs/
    # ----------------------------------------------------
    def upload_logs(self):
        if not self.log_folder_id:
            log.warning("⚠️ log_folder_id not set")
            return 0

        logs_dir = Path("logs")
        if not logs_dir.exists():
            log.warning("⚠️ logs/ not found")
            return 0

        log_files = list(logs_dir.glob("*.log"))
        if not log_files:
            log.info("📭 No logs to upload")
            return 0

        log.info(f"📤 Uploading {len(log_files)} log files…")

        uploaded = 0
        for f in log_files:
            if self.upload_file(str(f), self.log_folder_id, "text/plain"):
                uploaded += 1

        log.info(f"✅ Uploaded {uploaded}/{len(log_files)}")
        return uploaded

    # ----------------------------------------------------
    # Upload captures/
    # ----------------------------------------------------
    def upload_images(self):
        if not self.image_folder_id:
            log.warning("⚠️ image_folder_id not set")
            return 0

        cap_dir = Path("captures")
        if not cap_dir.exists():
            log.warning("⚠️ captures/ not found")
            return 0

        image_files = []
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            image_files.extend(cap_dir.glob(ext))

        if not image_files:
            log.info("📭 No images to upload")
            return 0

        log.info(f"📤 Uploading {len(image_files)} images…")

        uploaded = 0
        for img in image_files:
            mime = "image/jpeg" if img.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
            if self.upload_file(str(img), self.image_folder_id, mime):
                uploaded += 1

        log.info(f"✅ Uploaded {uploaded}/{len(image_files)}")
        return uploaded

    # ----------------------------------------------------
    # Upload all
    # ----------------------------------------------------
    def upload_all(self):
        if not self.enabled:
            log.info("ℹ️ Google Drive upload disabled")
            return False

        if not self.authenticate():
            return False

        total = 0
        total += self.upload_logs()
        total += self.upload_images()

        log.info(f"🎉 Upload complete: {total} files")
        return True


# --------------------------------------------------------
# MAIN
# --------------------------------------------------------
def main():
    print("=" * 50)
    print("🏠 DomiSafe - Google Drive Uploader (Service Account)")
    print("=" * 50)

    try:
        uploader = GoogleDriveUploader()

        if not uploader.enabled:
            print("⚠️ Google Drive upload disabled in config.json")
            return 0

        success = uploader.upload_all()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️ Cancelled by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())
