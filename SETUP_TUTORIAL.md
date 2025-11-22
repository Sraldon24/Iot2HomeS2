# 🚀 Complete Setup Tutorial - DomiSafe IoT System

This guide will walk you through setting up EVERYTHING from scratch - no steps skipped!

**Total Time:** ~30 minutes  
**Required:** Computer, Raspberry Pi, Internet

---

## 📋 Table of Contents

1. [Adafruit IO Setup](#1-adafruit-io-setup) (5 min) - **REQUIRED**
2. [Neon Database Setup](#2-neon-database-setup) (10 min) - **REQUIRED**
3. [Google Drive Setup](#3-google-drive-setup) (15 min) - Optional
4. [Raspberry Pi Setup](#4-raspberry-pi-setup) (10 min) - **REQUIRED**
5. [Getting Submission Links](#5-getting-submission-links) (5 min)

---

## 1️⃣ **Adafruit IO Setup** (5 minutes) ⭐ REQUIRED

### Why you need this:
Adafruit IO is your MQTT broker - it receives all sensor data from your Raspberry Pi and lets you control devices remotely.

### Step A: Create Account

1. Open browser and go to: **https://io.adafruit.com**

2. Click the green **"Get Started for Free"** button (top right)

3. Fill in the form:
   - **Username:** Choose something simple (e.g., `john_tech`)
   - **Email:** Your email address
   - **Password:** Create a strong password
   - **Confirm Password:** Same password again

4. Click **"Sign Up"**

5. Check your email for verification
   - Look for email from "Adafruit"
   - Click the verification link
   - This takes you back to Adafruit IO

### Step B: Get Your Credentials

1. After logging in, look at the top-right corner

2. You'll see a **yellow key icon** 🔑 - Click it
   - It says "My Key" when you hover over it

3. A page opens showing:
   ```
   Username: your_username
   Active Key: aio_Abc123DefGhi456JklMno789PqrStu
   ```

4. **COPY BOTH OF THESE!** You need them for `config.json`
   - Click the copy icon next to each one
   - Paste into a text file temporarily

### Step C: Create Feeds (8 feeds needed)

Feeds are like "channels" where your data flows.

1. Click **"Feeds"** in the left sidebar menu

2. Click the blue **"+ New Feed"** button

3. Create each feed ONE BY ONE:

**Feed #1: Temperature**
- Name: `temperature`
- Description: (leave blank or write "Temperature sensor data")
- Click **"Create"**

**Feed #2: Humidity**
- Name: `humidity`
- Description: (optional)
- Click **"Create"**

**Feed #3: Motion**
- Name: `motion`
- Description: (optional)
- Click **"Create"**

**Feed #4: LED Status**
- Name: `led_status`
- Description: (optional)
- Click **"Create"**

**Feed #5: Buzzer Status**
- Name: `buzzer_status`
- Description: (optional)
- Click **"Create"**

**Feed #6: Motor Status**
- Name: `motor_status`
- Description: (optional)
- Click **"Create"**

**Feed #7: Security Enabled**
- Name: `security_enabled`
- Description: (optional)
- Click **"Create"**

**Feed #8: Camera Last Image**
- Name: `camera_last_image`
- Description: (optional)
- Click **"Create"**

### Step D: Create Dashboard (for submission)

1. Click **"Dashboards"** in the left menu

2. Click blue **"+ New Dashboard"** button

3. Fill in:
   - **Name:** `DomiSafe Home Security`
   - **Description:** (optional)
   - Click **"Create"**

4. Your new dashboard opens - it's empty now

5. Click the **"+"** button or **"Create New Block"** 

6. Add these blocks (one at a time):

**Block 1: Temperature Gauge**
- Choose **"Gauge"** from the block types
- Select feed: **temperature**
- Block Title: "Temperature"
- Min: `0`
- Max: `50`
- Click **"Create Block"**

**Block 2: Humidity Gauge**
- Choose **"Gauge"**
- Select feed: **humidity**
- Block Title: "Humidity"
- Min: `0`
- Max: `100`
- Click **"Create Block"**

**Block 3: Motion Indicator**
- Choose **"Indicator"**
- Select feed: **motion**
- Block Title: "Motion Detection"
- Click **"Create Block"**

**Block 4: LED Toggle**
- Choose **"Toggle"**
- Select feed: **led_status**
- Block Title: "LED Control"
- Button On Text: "ON"
- Button Off Text: "OFF"
- Click **"Create Block"**

**Block 5: Buzzer Toggle**
- Choose **"Toggle"**
- Select feed: **buzzer_status**
- Block Title: "Buzzer Control"
- Click **"Create Block"**

**Block 6: Motor Toggle**
- Choose **"Toggle"**
- Select feed: **motor_status**
- Block Title: "Motor/Fan Control"
- Click **"Create Block"**

**Block 7: Temperature Chart**
- Choose **"Line Chart"**
- Select feed: **temperature**
- Block Title: "Temperature History"
- Hours of History: `12`
- Click **"Create Block"**

**Block 8: Humidity Chart**
- Choose **"Line Chart"**
- Select feed: **humidity**
- Block Title: "Humidity History"
- Hours of History: `12`
- Click **"Create Block"**

7. **Arrange the blocks nicely** - drag them around to look good

8. **Make dashboard PUBLIC** (for submission):
   - Click the gear icon ⚙️ (Settings)
   - Find "Privacy" section
   - Change from "Private" to **"Public"**
   - Click **"Save Settings"**

9. **COPY THE DASHBOARD URL:**
   - Look at your browser address bar
   - It will be: `https://io.adafruit.com/your_username/dashboards/domisafe-home-security`
   - **SAVE THIS LINK!** You need it for submission

---

## 2️⃣ **Neon Database Setup** (10 minutes) ⭐ REQUIRED

### Why you need this:
Neon provides the cloud PostgreSQL database where historical data is stored. The Flask app needs this to show historical graphs.

### Step A: Create Account

1. Go to: **https://neon.tech**

2. Click **"Sign Up"** (top right)

3. **EASIEST:** Click **"Continue with GitHub"**
   - If you don't have GitHub, use **"Continue with Google"**
   - OR use email + password

4. Authorize the connection if asked

5. You're now in the Neon dashboard!

### Step B: Create Project

1. You'll see a big button: **"Create Project"** or **"Create your first project"**

2. Click it

3. Fill in the form:

   **Project Name:**
   - Enter: `DomiSafe`

   **Region:** (Choose closest to you)
   - 🇺🇸 **US East (Ohio)** - If you're in North America
   - 🇪🇺 **Europe (Frankfurt)** - If you're in Europe  
   - 🇸🇬 **Asia Pacific (Singapore)** - If you're in Asia
   - Just pick the one closest to Montreal (US East probably)

   **Postgres Version:**
   - Leave as default (probably 16)

   **Compute Size:**
   - Leave as **"0.25 CU"** (free tier)

4. Click **"Create Project"**

5. Wait 10-30 seconds while it creates...

### Step C: Get Connection String

1. After creation, you'll see a screen with connection details

2. Look for **"Connection String"** section

3. You'll see a long string that looks like:
   ```
   postgresql://neondb_owner:AbCd123EfGh456@ep-cool-name-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

4. **Click the COPY button** 📋 next to it

5. **PASTE IT SOMEWHERE SAFE!** You need this for `config.json`

**Understanding the connection string:**
```
postgresql://  username : password  @ hostname                           / database ?sslmode=require
              │          │            │                                   │          │
              └──────────┴────────────┴───────────────────────────────────┴──────────┘
                   These are auto-generated - don't change them
```

### Step D: Verify It Works (Optional but recommended)

1. In Neon dashboard, click **"SQL Editor"** (left menu)

2. You can run test queries here

3. Try this test:
   ```sql
   SELECT version();
   ```

4. Click **"Run"**

5. If you see PostgreSQL version info = ✅ **It works!**

### Step E: Save Your Info

Write these down:
```
Neon Project: DomiSafe
Connection String: postgresql://neondb_owner:...
Region: US East (Ohio)
```

**Note:** Your Python code will automatically create the tables (`environment` and `motion_events`) when it first runs - you don't need to create them manually!

---

## 3️⃣ **Google Drive Setup** (15 minutes) - OPTIONAL

### Do you need this?

**NO if:**
- You just want to get the project working
- You're okay with logs only being local
- You don't want to deal with OAuth setup

**YES if:**
- You want automatic cloud backup of logs
- Professor requires it
- You want to submit Google Drive links

### If you DON'T want it:
Just set in `config.json`:
```json
{
  "google_drive_enabled": false
}
```
**Skip to Step 4!**

### If you DO want it:

#### Part A: Google Cloud Console Setup

1. Go to: **https://console.cloud.google.com**

2. Sign in with your Google account

3. **Create Project:**
   - Click the dropdown at the top (says "Select a project")
   - Click **"New Project"**
   - Project name: `DomiSafe-IoT`
   - Organization: Leave as "No organization"
   - Click **"Create"**
   - Wait 10-20 seconds

4. **Select your project:**
   - Click the dropdown again
   - Click on **"DomiSafe-IoT"**

5. **Enable Google Drive API:**
   - In the search bar at top, type: `Google Drive API`
   - Click on the result **"Google Drive API"**
   - Click the blue **"Enable"** button
   - Wait a few seconds

6. **Create OAuth Credentials:**
   - Click **"Credentials"** (left menu)
   - You might see a banner saying "To create OAuth client ID, you must first set a product name"
   - If so, click **"Configure Consent Screen"**
     - Choose **"External"**
     - Click **"Create"**
     - Fill in:
       - App name: `DomiSafe`
       - User support email: Your email
       - Developer contact: Your email
     - Click **"Save and Continue"**
     - On "Scopes" page, click **"Save and Continue"** (skip it)
     - On "Test users" page, click **"Save and Continue"** (skip it)
     - Click **"Back to Dashboard"**

7. **Now create OAuth client:**
   - Click **"Credentials"** (left menu)
   - Click **"+ Create Credentials"** (top)
   - Choose **"OAuth client ID"**
   - Application type: **"Desktop app"**
   - Name: `DomiSafe Pi`
   - Click **"Create"**

8. **Download credentials:**
   - A popup appears with your credentials
   - Click **"Download JSON"** button
   - Save the file (it's named like `client_secret_123456789.json`)
   - **RENAME IT TO:** `client_secrets.json`
   - **MOVE IT TO YOUR PROJECT FOLDER:** `~/Iot2HomeS/client_secrets.json`

#### Part B: Create Google Drive Folders

1. Go to: **https://drive.google.com**

2. **Create Logs Folder:**
   - Click **"+ New"** (top left)
   - Click **"New folder"**
   - Name: `DomiSafe Logs`
   - Click **"Create"**

3. **Get Folder ID:**
   - Right-click the folder
   - Click **"Share"**
   - Click **"Copy link"**
   - The link looks like: `https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz`
   - **The folder ID is the part after `/folders/`:** `1AbCdEfGhIjKlMnOpQrStUvWxYz`
   - **SAVE THIS ID!**

4. **Create Images Folder:**
   - Click **"+ New"** again
   - Click **"New folder"**
   - Name: `DomiSafe Images`
   - Click **"Create"**

5. **Get Images Folder ID:**
   - Same process as above
   - Right-click → Share → Copy link
   - Extract the ID from the URL
   - **SAVE THIS ID TOO!**

#### Part C: First Run Authentication

When you first run `upload_logs.py`:
1. A browser window will open automatically
2. Sign in to Google (if not already)
3. Click **"Allow"** to give permission
4. Browser will show "Authentication complete"
5. A file `credentials.json` is created (access token)
6. Future runs will use this token - no more browser popups!

---

## 4️⃣ **Raspberry Pi Setup** (10 minutes) ⭐ REQUIRED

### Step A: Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y python3-pip python3-venv git
```

### Step B: Clone Repository

```bash
cd ~
git clone https://github.com/Sraldon24/Iot2HomeS.git
cd Iot2HomeS
```

### Step C: Run Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Initialize database
- Create directory structure

### Step D: Configure Credentials

```bash
cp config.example.json config.json
nano config.json
```

Fill in:
```json
{
  "ADAFRUIT_IO_USERNAME": "your_username_from_step1",
  "ADAFRUIT_IO_KEY": "aio_your_key_from_step1",
  "MQTT_BROKER": "io.adafruit.com",
  "MQTT_PORT": 8883,
  
  "NEON_DB_URL": "postgresql://user:pass@host/db?sslmode=require",
  
  "DHT_PIN": 4,
  "PIR_PIN": 6,
  "LED_PIN": 16,
  "BUZZER_PIN": 26,
  "MOTOR_PIN": 21,
  
  "security_check_interval": 5,
  "env_interval": 30,
  "sync_interval": 60,
  
  "camera_enabled": true,
  "cloud_sync_enabled": true,
  "google_drive_enabled": false,
  
  "google_drive_log_folder_id": "",
  "google_drive_image_folder_id": ""
}
```

**Press:** Ctrl+X, then Y, then Enter (to save)

### Step E: Test System

```bash
source venv/bin/activate
python3 test_system.py
```

You should see all green ✅ checkmarks!

### Step F: Run Main Application

```bash
python3 main.py
```

Expected output:
```
==================================================
🏠 DomiSafe IoT System
==================================================
✅ Loaded config from config.json
✅ MQTT connected
✅ Connected to cloud database
✅ All systems ready
🌡️ Environment monitoring started
🔒 Security monitoring started
```

### Step G: Run Flask App (New Terminal)

```bash
cd ~/Iot2HomeS
source venv/bin/activate
cd web_app
python3 app.py
```

Expected:
```
 * Running on http://0.0.0.0:5000
```

### Step H: Access Dashboard

1. Find your Pi's IP:
   ```bash
   hostname -I
   ```
   Example output: `192.168.1.100`

2. On your computer, open browser:
   ```
   http://192.168.1.100:5000
   ```

3. You should see the DomiSafe dashboard!

---

## 5️⃣ **Getting Submission Links** (5 minutes)

### Link 1: GitHub Repository ✅
```
https://github.com/Sraldon24/Iot2HomeS
```
*You already have this!*

### Link 2: Adafruit IO Dashboard
1. Go to https://io.adafruit.com
2. Click "Dashboards"
3. Click your "DomiSafe Home Security" dashboard
4. Copy URL from browser:
   ```
   https://io.adafruit.com/YOUR_USERNAME/dashboards/domisafe-home-security
   ```
5. Verify it's PUBLIC (Settings → Privacy → Public)

### Link 3: Google Drive Folder (if using)
1. Go to https://drive.google.com
2. Right-click "DomiSafe Logs" folder
3. Click "Share"
4. Click "Change to anyone with the link"
5. Click "Copy link"
6. This is your submission link!

### Link 4: YouTube Video ✅
```
https://youtube.com/shorts/6NvQyifem0k?si=NhJyaJJdsLLMG1LM
```
*You already have this!*

---

## ✅ **Verification Checklist**

Before submitting, verify:

- [ ] **Adafruit IO:**
  - [ ] Account created
  - [ ] 8 feeds exist
  - [ ] Dashboard is PUBLIC
  - [ ] Dashboard link copied

- [ ] **Neon Database:**
  - [ ] Account created
  - [ ] Project "DomiSafe" exists
  - [ ] Connection string copied

- [ ] **Raspberry Pi:**
  - [ ] `config.json` has real credentials
  - [ ] `python3 test_system.py` passes all tests
  - [ ] `main.py` runs without errors
  - [ ] Flask app accessible at `http://PI_IP:5000`
  - [ ] Can see live data on dashboard

- [ ] **Submission Links:**
  - [ ] GitHub repo link
  - [ ] Adafruit IO dashboard link
  - [ ] Cloud folder link (if using Drive)
  - [ ] YouTube video link

---

## 🆘 **Common Issues**

### Issue: "MQTT Connection Failed"
**Solution:**
```bash
# Check credentials
nano config.json
# Verify ADAFRUIT_IO_USERNAME and ADAFRUIT_IO_KEY match exactly
```

### Issue: "Cloud DB Connection Failed"
**Solution:**
```bash
# Test connection string
python3 << EOF
import psycopg2
conn = psycopg2.connect("YOUR_NEON_URL_HERE")
print("✅ Connected!")
conn.close()
EOF
```

### Issue: "Port 5000 already in use"
**Solution:**
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
```

### Issue: "Camera not working"
**Solution:**
```bash
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot
```

### Issue: "Permission denied on GPIO"
**Solution:**
```bash
sudo usermod -a -G gpio $USER
sudo reboot
```

---

## 🎉 **You're Done!**

All setup is complete! You now have:

✅ Adafruit IO receiving live sensor data  
✅ Neon database storing historical data  
✅ Flask web app showing everything  
✅ All submission links ready  

**Next:** Test the entire system and record your demo video if needed!

---

## 📝 **Quick Reference Card**

Save this for easy access:

```
ADAFRUIT IO
URL: io.adafruit.com
Username: _______________
Key: aio_______________
Dashboard: https://io.adafruit.com/_____/dashboards/domisafe

NEON DATABASE
URL: neon.tech
Connection: postgresql://_____@_____/domisafe?sslmode=require

FLASK APP
Local: http://localhost:5000
Network: http://___.___.___:5000

GITHUB
Repo: https://github.com/Sraldon24/Iot2HomeS
```

**Good luck with your project! 🚀**