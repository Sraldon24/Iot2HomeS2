#!/usr/bin/env python3
"""
==================================================
DomiSafe IoT System - Google Drive Uploader (OAuth)
==================================================
Works with personal Gmail.
No service account. No Workspace. 100% free.

First run → Shows a link → Login once → Paste code.
After that → credentials.json makes everything automatic.
"""

import os
import sys
import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from modules.config_loader import load_config

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger("upload_logs")

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_FILE = "credentials.json"


class GoogleDriveUploader:

    def __init__(self, config_path="config.json"):
        self.config = load_config(config_path)
        self.enabled = self.config.get("google_drive_enabled", False)
        self.log_folder_id = self.config.get("google_drive_log_folder_id", "")
        self.image_folder_id = self.config.get("google_drive_image_folder_id", "")
        self.service = None

        if not os.path.exists("client_secrets.json"):
            log.error("❌ Missing client_secrets.json (OAuth).")
            self.enabled = False

    # ----------------------------------------------------
    # AUTH — OAuth Desktop (Works with personal Gmail)
    # ----------------------------------------------------
    def authenticate(self):
        creds = None

        # Load existing token
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

        # If no token OR invalid token → login flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                log.info("🔄 Token refreshed")
            else:
                # OAuth Desktop mode (console)
                flow = InstalledAppFlow.from_client_secrets_file(
                    "client_secrets.json", SCOPES
                )

                print("\n🔐 LOGIN REQUIRED:")
                print("1. Copy the link below")
                print("2. Open in ANY browser")
                print("3. Login to Google")
                print("4. Paste the code back here\n")

                creds = flow.run_local_server(port=0)

            # Save new token
            with open(TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
                log.info("💾 Credentials saved")

        # Build Drive service
        self.service = build("drive", "v3", credentials=creds)
        log.info("✅ Google Drive API ready")
        return True

    # ----------------------------------------------------
    def upload_file(self, file_path, folder_id, mime):
        file_name = os.path.basename(file_path)

        metadata = {"name": file_name, "parents": [folder_id]}

        try:
            media = MediaFileUpload(file_path, mimetype=mime)

            self.service.files().create(
                body=metadata,
                media_body=media,
                fields="id"
            ).execute()

            log.info(f"📤 Uploaded: {file_name}")
            return True

        except Exception as e:
            log.error(f"❌ Failed to upload {file_name}: {e}")
            return False

    # ----------------------------------------------------
    def upload_logs(self):
        logs = list(Path("logs").glob("*.log"))
        if not logs:
            log.info("📭 No logs found")
            return 0

        uploaded = 0
        for f in logs:
            if self.upload_file(str(f), self.log_folder_id, "text/plain"):
                uploaded += 1

        return uploaded

    # ----------------------------------------------------
    def upload_images(self):
        images = []
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            images.extend(Path("captures").glob(ext))

        if not images:
            log.info("📭 No images found")
            return 0

        uploaded = 0
        for img in images:
            mime = "image/jpeg" if img.suffix.lower() in (".jpg", ".jpeg") else "image/png"
            if self.upload_file(str(img), self.image_folder_id, mime):
                uploaded += 1

        return uploaded

    # ----------------------------------------------------
    def upload_all(self):
        if not self.enabled:
            print("⚠️ Upload disabled in config.json")
            return False

        if not self.authenticate():
            return False

        total = self.upload_logs() + self.upload_images()
        print(f"\n🎉 Upload complete: {total} file(s)")
        return True


# --------------------------------------------------------
def main():
    print("=" * 50)
    print("🏠 DomiSafe - Google Drive Uploader (OAuth)")
    print("=" * 50)

    try:
        return 0 if GoogleDriveUploader().upload_all() else 1
    except KeyboardInterrupt:
        print("\n⚠️ Cancelled")
        return 1


if __name__ == "__main__":
    sys.exit(main())
