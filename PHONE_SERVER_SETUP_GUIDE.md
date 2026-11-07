# 📱 Complete Phone Server Setup Guide
### Transform Your Android Phone into a Personal Media Server

---

## 📑 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Initial Phone Setup](#2-initial-phone-setup)
3. [Install Termux](#3-install-termux)
4. [Install Required Packages](#4-install-required-packages)
5. [Setup Storage Access](#5-setup-storage-access)
6. [Install Python & Dependencies](#6-install-python--dependencies)
7. [Install FFmpeg (Video Transcoding)](#7-install-ffmpeg-video-transcoding)
8. [Setup SSH Server](#8-setup-ssh-server)
9. [Install & Configure Tailscale (VPN)](#9-install--configure-tailscale-vpn)
10. [Clone Media Server Repository](#10-clone-media-server-repository)
11. [Configure Media Server](#11-configure-media-server)
12. [Setup Termux:Boot (Auto-Start)](#12-setup-termuxboot-auto-start)
13. [File Transfer (SFTP/SCP)](#13-file-transfer-sftpscp)
14. [Useful SSH Commands](#14-useful-ssh-commands)
15. [Server Management](#15-server-management)
16. [Troubleshooting](#16-troubleshooting)
17. [Performance Tips](#17-performance-tips)

---

## 1. Prerequisites

### What You Need:
- ✅ Android phone (Android 7.0+)
- ✅ At least 2GB RAM (4GB+ recommended)
- ✅ 10GB+ free storage
- ✅ Stable WiFi connection
- ✅ Computer for initial setup (optional)

### Recommended Specs:
- **CPU:** MediaTek Dimensity or Snapdragon 600+ series
- **RAM:** 4GB+
- **Storage:** 32GB+ with SD card slot
- **Battery:** 4000mAh+ with good thermal management

---

## 2. Initial Phone Setup

### Step 1: Factory Reset (Recommended for dedicated server)
```
Settings → System → Reset → Factory Reset
```

### Step 2: Disable Battery Optimization
```
Settings → Apps → See all apps → Termux
→ Battery → Battery optimization → Don't optimize
```

### Step 3: Enable Developer Options
```
Settings → About phone → Tap "Build number" 7 times
Settings → Developer options → Enable "Stay awake"
```

### Step 4: Disable System Updates (Prevents auto-restart)
```
Settings → System → System update → Disable auto-update
```

---

## 3. Install Termux

### ⚠️ IMPORTANT: Use F-Droid, NOT Google Play Store!
Google Play version is outdated and broken.

### Install F-Droid:
1. Open browser on phone
2. Go to: `https://f-droid.org/`
3. Download **F-Droid.apk**
4. Install (allow "Unknown sources" if prompted)

### Install Termux from F-Droid:
1. Open F-Droid app
2. Search: **Termux**
3. Install: `com.termux` (by Fredrik Fornwall)
4. **Also install:**
   - **Termux:API** (for system integration)
   - **Termux:Boot** (for auto-start)
   - **Termux:Widget** (optional - home screen shortcuts)

### Versions to Install:
```
Termux: Latest (v0.118.0+)
Termux:API: Latest
Termux:Boot: Latest
```

---

## 4. Install Required Packages

### Step 1: Update Package Repository
```bash
# Open Termux app, then run:
pkg update -y && pkg upgrade -y
```

### Step 2: Install Essential Tools
```bash
# Install core utilities
pkg install -y git curl wget openssh termux-api termux-services

# Verify installation
git --version
ssh -V
```

**Expected Output:**
```
git version 2.x.x
OpenSSH_9.x
```

---

## 5. Setup Storage Access

### Grant Termux Storage Permission:
```bash
termux-setup-storage
```

**What happens:**
- Phone will ask for storage permission → **Allow**
- Creates `~/storage/` symlinks to phone storage

### Verify Storage Access:
```bash
ls ~/storage/
```

**You should see:**
```
dcim/      (Camera)
downloads/ (Downloads folder)
movies/    (Movies folder)
music/     (Music folder)
shared/    (Internal storage root)
```

### Create Media Directory:
```bash
# Create folder for your videos
mkdir -p ~/storage/shared/Movies
cd ~/storage/shared/Movies
ls -lah
```

---

## 6. Install Python & Dependencies

### Step 1: Install Python
```bash
pkg install -y python python-pip
```

### Step 2: Verify Python
```bash
python --version
pip --version
```

**Expected:**
```
Python 3.11.x
pip 23.x
```

### Step 3: Install Python Packages
```bash
# Install Flask and dependencies
pip install --upgrade pip
pip install flask requests
```

### Step 4: Test Python
```bash
python -c "import flask; print(flask.__version__)"
```

---

## 7. Install FFmpeg (Video Transcoding)

### Install FFmpeg:
```bash
pkg install -y ffmpeg
```

### Verify FFmpeg:
```bash
ffmpeg -version
ffprobe -version
```

**Expected Output:**
```
ffmpeg version 6.x
ffprobe version 6.x
```

### Test FFmpeg (Optional):
```bash
# Download sample video
wget https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4 -O test.mp4

# Test transcode
ffmpeg -i test.mp4 -c:v libx264 -preset ultrafast -crf 28 -t 5 output.mp4

# Clean up
rm test.mp4 output.mp4
```

---

## 8. Setup SSH Server

### Step 1: Install OpenSSH
```bash
pkg install -y openssh
```

### Step 2: Set Password
```bash
passwd
```

**Enter a strong password!** This protects your server.

### Step 3: Start SSH Server
```bash
sshd
```

### Step 4: Find Your IP Address
```bash
ifconfig wlan0 | grep "inet "
```

**Example Output:**
```
inet 192.168.1.100 netmask 255.255.255.0
```

Your phone IP: `192.168.1.100`

### Step 5: Test SSH from Computer
```bash
# From your computer (replace IP):
ssh -p 8022 u0_a123@192.168.1.100
```

**Note:** Termux SSH runs on port **8022** (not 22)

### Step 6: Get Your Username
```bash
whoami
```

**Output example:** `u0_a123` (your actual username)

---

## 9. Install & Configure Tailscale (VPN)

### What is Tailscale?
Secure VPN to access your server from anywhere without port forwarding.

### Step 1: Download Tailscale
```bash
# Get latest Tailscale binary for ARM64
cd ~
wget https://pkgs.tailscale.com/stable/tailscale_1.56.1_arm64.tgz

# Extract
tar xzf tailscale_1.56.1_arm64.tgz
cd tailscale_1.56.1_arm64
```

### Step 2: Move Binaries
```bash
# Move to PATH
mv tailscale tailscaled $PREFIX/bin/
chmod +x $PREFIX/bin/tailscale*
```

### Step 3: Start Tailscale Daemon
```bash
# Create directory
mkdir -p $PREFIX/var/run

# Start daemon (run in background)
tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &
```

### Step 4: Authenticate
```bash
tailscale up --hostname=my-phone-server
```

**Output:**
```
To authenticate, visit:
https://login.tailscale.com/a/xxxxxxxxxxxx
```

Open that URL on any device → Login → Approve

### Step 5: Verify Connection
```bash
tailscale status
```

**Output:**
```
100.x.x.x   my-phone-server   your-user@   linux   -
```

Your Tailscale IP: `100.x.x.x`

### Step 6: Test SSH via Tailscale
```bash
# From any device on your Tailscale network:
ssh -p 8022 u0_a123@100.x.x.x
```

---

## 10. Clone Media Server Repository

### Step 1: Navigate to Home
```bash
cd ~
```

### Step 2: Clone Repository
```bash
git clone https://github.com/yourusername/Personal_Drive_Media-Player.git
cd Personal_Drive_Media-Player
```

**OR** if you have the files on your computer, use SCP (see Section 13)

### Step 3: Download HLS.js
```bash
# Download HLS.js library
wget https://cdn.jsdelivr.net/npm/hls.js@latest/dist/hls.min.js \
     -O static/js/hls.min.js
```

### Step 4: Verify Files
```bash
ls -lah
```

**You should see:**
```
app.py
config.py
routes/
static/
templates/
transcoding/
README.md
```

---

## 11. Configure Media Server

### Step 1: Edit Configuration
```bash
nano config.py
```

**Set your media root:**
```python
MEDIA_ROOT = "/data/data/com.termux/files/home/storage/shared/Movies"
```

**Or set via environment variable:**
```bash
export MEDIA_ROOT="/data/data/com.termux/files/home/storage/shared/Movies"
```

### Step 2: Create Directories
```bash
# Create required directories
mkdir -p /data/data/com.termux/files/usr/tmp/media-server
mkdir -p ~/.config
```

### Step 3: Test Server
```bash
python3 app.py
```

**Expected Output:**
```
============================================
         TERMUX MEDIA SERVER
============================================

  Media root:  /data/.../Movies
               ✓ Accessible

  FFmpeg:      ✓ Found
  FFprobe:     ✓ Found
  HLS.js:      ✓ Found

  Server:      http://192.168.1.100:8080
               http://100.x.x.x:8080 (Tailscale)

Press Ctrl+C to stop
```

### Step 4: Test in Browser
Open on your computer/phone:
```
http://192.168.1.100:8080
```

**You should see:** Your media server interface!

### Step 5: Stop Server (for now)
```
Press Ctrl+C
```

---

## 12. Setup Termux:Boot (Auto-Start)

### Why?
Automatically start your server when phone boots.

### Step 1: Create Boot Directory
```bash
mkdir -p ~/.termux/boot
```

### Step 2: Create Startup Script
```bash
nano ~/.termux/boot/start-server.sh
```

**Add this content:**
```bash
#!/data/data/com.termux/files/usr/bin/bash

# Wait for network
sleep 30

# Start SSH server
sshd

# Start Tailscale (optional)
# Uncomment if using Tailscale:
# tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &
# sleep 5
# tailscale up --hostname=my-phone-server

# Start Media Server
cd ~/Personal_Drive_Media-Player
export MEDIA_ROOT="/data/data/com.termux/files/home/storage/shared/Movies"
python3 app.py > ~/server.log 2>&1 &

# Log startup
echo "Server started at $(date)" >> ~/boot.log
```

### Step 3: Make Executable
```bash
chmod +x ~/.termux/boot/start-server.sh
```

### Step 4: Test Boot Script
```bash
~/.termux/boot/start-server.sh
```

### Step 5: Verify Auto-Start
```
Restart your phone
Wait 1-2 minutes
Check if server is running:
http://192.168.1.100:8080
```

### Step 6: Check Logs
```bash
cat ~/boot.log
cat ~/server.log
```

---

## 13. File Transfer (SFTP/SCP)

### SFTP - Interactive File Browser

#### Connect to Phone:
```bash
sftp -P 8022 u0_a123@192.168.1.100
```

**Note:** Capital `-P` for SFTP!

#### SFTP Commands:
```bash
# List files on phone
ls

# Navigate
cd storage/shared/Movies

# Download file from phone to computer
get video.mp4

# Upload file from computer to phone
put movie.mkv

# Upload folder
put -r myfolder/

# Exit
exit
```

### SCP - Direct Copy

#### Upload File to Phone:
```bash
scp -P 8022 movie.mkv u0_a123@192.168.1.100:~/storage/shared/Movies/
```

#### Upload Folder to Phone:
```bash
scp -P 8022 -r MyMovies/ u0_a123@192.168.1.100:~/storage/shared/Movies/
```

#### Download File from Phone:
```bash
scp -P 8022 u0_a123@192.168.1.100:~/storage/shared/Movies/video.mp4 .
```

#### Download Folder from Phone:
```bash
scp -P 8022 -r u0_a123@192.168.1.100:~/storage/shared/Movies/ ./Downloads/
```

### Rsync - Sync Folders (Advanced)

#### Install Rsync:
```bash
pkg install -y rsync
```

#### Sync Local → Phone:
```bash
rsync -avz -e "ssh -p 8022" \
  ./MyMovies/ \
  u0_a123@192.168.1.100:~/storage/shared/Movies/
```

#### Sync Phone → Local:
```bash
rsync -avz -e "ssh -p 8022" \
  u0_a123@192.168.1.100:~/storage/shared/Movies/ \
  ./PhoneBackup/
```

**Flags:**
- `-a` = archive mode (preserves permissions, timestamps)
- `-v` = verbose
- `-z` = compress during transfer
- `-e` = specify SSH with custom port

---

## 14. Useful SSH Commands

### SSH Connection

#### Basic Connection:
```bash
ssh -p 8022 u0_a123@192.168.1.100
```

#### With Tailscale:
```bash
ssh -p 8022 u0_a123@100.x.x.x
```

#### Save Connection as Alias:
```bash
# On your computer, edit ~/.ssh/config
nano ~/.ssh/config
```

**Add:**
```
Host myphone
    HostName 192.168.1.100
    Port 8022
    User u0_a123

Host myphone-vpn
    HostName 100.x.x.x
    Port 8022
    User u0_a123
```

**Now connect easily:**
```bash
ssh myphone
ssh myphone-vpn
```

### SSH Flags & Options

#### Common Flags:
```bash
# -p PORT       Specify port (lowercase for SSH)
ssh -p 8022 user@host

# -P PORT       Specify port (uppercase for SFTP/SCP)
sftp -P 8022 user@host

# -i KEYFILE    Use specific SSH key
ssh -i ~/.ssh/mykey -p 8022 user@host

# -v            Verbose (debug connection)
ssh -v -p 8022 user@host

# -L            Port forwarding (local)
ssh -L 8080:localhost:8080 -p 8022 user@host

# -D            SOCKS proxy
ssh -D 1080 -p 8022 user@host

# -N            No command (just forward ports)
ssh -N -L 8080:localhost:8080 -p 8022 user@host

# -f            Background mode
ssh -f -N -L 8080:localhost:8080 -p 8022 user@host

# -T            Disable pseudo-terminal
ssh -T -p 8022 user@host "ls -lah"

# -C            Enable compression
ssh -C -p 8022 user@host
```

### SSH Key Authentication (Passwordless)

#### Generate Key on Computer:
```bash
ssh-keygen -t ed25519 -C "myphone-key"
```

#### Copy Key to Phone:
```bash
ssh-copy-id -p 8022 u0_a123@192.168.1.100
```

**OR manually:**
```bash
cat ~/.ssh/id_ed25519.pub | ssh -p 8022 u0_a123@192.168.1.100 \
  "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

#### Now connect without password:
```bash
ssh -p 8022 u0_a123@192.168.1.100
```

---

## 15. Server Management

### Check Server Status

#### Is server running?
```bash
ps aux | grep python
```

#### Check port 8080:
```bash
netstat -tuln | grep 8080
```

#### Check logs:
```bash
tail -f ~/server.log
```

### Start Server Manually

#### Simple:
```bash
cd ~/Personal_Drive_Media-Player
python3 app.py
```

#### Background (keeps running after logout):
```bash
cd ~/Personal_Drive_Media-Player
nohup python3 app.py > ~/server.log 2>&1 &
```

#### With custom port:
```bash
python3 app.py --port 9090
```

#### With custom media root:
```bash
MEDIA_ROOT=/path/to/movies python3 app.py
```

### Stop Server

#### Find process:
```bash
ps aux | grep "python.*app.py"
```

#### Kill by PID:
```bash
kill 12345
```

#### Kill forcefully:
```bash
kill -9 12345
```

#### Kill all python processes:
```bash
pkill python
```

### Restart Server

#### Stop and start:
```bash
pkill python
sleep 2
cd ~/Personal_Drive_Media-Player
nohup python3 app.py > ~/server.log 2>&1 &
```

### Clear Cache

#### Clear transcode cache:
```bash
python3 app.py --clear-cache
```

#### Clear incomplete jobs:
```bash
python3 app.py --cleanup-cache
```

#### Manual clear:
```bash
rm -rf /data/data/com.termux/files/usr/tmp/media-server/*
```

---

## 16. Troubleshooting

### Server Won't Start

#### Check Python:
```bash
python3 --version
which python3
```

#### Check dependencies:
```bash
pip list | grep -i flask
```

#### Reinstall Flask:
```bash
pip install --force-reinstall flask
```

#### Check FFmpeg:
```bash
ffmpeg -version
```

### Can't Connect via SSH

#### Check SSH daemon:
```bash
ps aux | grep sshd
```

#### Restart SSH:
```bash
pkill sshd
sshd
```

#### Check port:
```bash
netstat -tuln | grep 8022
```

#### Test localhost:
```bash
ssh -p 8022 localhost
```

### Can't Access Server in Browser

#### Check server is running:
```bash
ps aux | grep python
curl localhost:8080
```

#### Check firewall (if applicable):
```bash
# Termux usually has no firewall
```

#### Check IP address:
```bash
ifconfig wlan0 | grep "inet "
```

#### Try different ports:
```bash
python3 app.py --port 9090
```

### Video Won't Play / Stuttering

#### Check FFmpeg:
```bash
ffmpeg -version
```

#### Check CPU usage:
```bash
top
```

#### Reduce quality (edit config.py):
```python
VIDEO_CRF = 30        # Higher = lower quality, faster
VIDEO_PRESET = "ultrafast"
```

#### Clear cache:
```bash
python3 app.py --clear-cache
```

### Termux:Boot Not Working

#### Check boot directory:
```bash
ls -lah ~/.termux/boot/
```

#### Check permissions:
```bash
chmod +x ~/.termux/boot/*.sh
```

#### Test script manually:
```bash
~/.termux/boot/start-server.sh
```

#### Check logs:
```bash
cat ~/boot.log
cat ~/server.log
```

#### Reinstall Termux:Boot:
```
Uninstall from F-Droid
Reinstall from F-Droid
Recreate boot scripts
```

---

## 17. Performance Tips

### Battery Optimization

#### Reduce screen brightness:
```
Settings → Display → Brightness → 0%
```

#### Enable battery saver:
```
Settings → Battery → Battery Saver → Enable
```

#### Use airplane mode + WiFi:
```
Quick Settings → Airplane Mode ON
Quick Settings → WiFi ON
```

### Server Optimization

#### Limit transcoding quality (config.py):
```python
VIDEO_CRF = 28              # 23-28 range
VIDEO_PRESET = "ultrafast"  # fastest encoding
MAX_CACHE_SIZE = 500 * 1024 * 1024  # 500MB cache
```

#### Limit segment time:
```python
HLS_SEGMENT_TIME = 6  # 4-10 seconds
```

#### Reduce max transcodes:
```python
MAX_TRANSCODES = 1  # Only 1 video at a time
```

### Storage Management

#### Check disk usage:
```bash
df -h
du -sh ~/storage/shared/Movies
```

#### Auto-cleanup on startup (add to boot script):
```bash
# Clear old cache on boot
rm -rf /data/data/com.termux/files/usr/tmp/media-server/cache/*
```

#### Compress logs:
```bash
gzip ~/server.log
```

### Network Performance

#### Use 5GHz WiFi:
```
Settings → WiFi → Advanced → 5GHz preferred
```

#### Static IP (prevents IP changes):
```
Settings → WiFi → Your Network → Advanced → IP settings → Static
IP: 192.168.1.100
Gateway: 192.168.1.1
DNS: 8.8.8.8
```

---

## 📝 Quick Reference Card

### Essential Commands:
```bash
# Update packages
pkg update && pkg upgrade

# Start SSH
sshd

# Start server
cd ~/Personal_Drive_Media-Player && python3 app.py

# Stop server
pkill python

# Check logs
tail -f ~/server.log

# SSH from computer
ssh -p 8022 u0_a123@192.168.1.100

# Upload file
scp -P 8022 movie.mkv u0_a123@192.168.1.100:~/storage/shared/Movies/

# Clear cache
python3 app.py --clear-cache
```

### Default Ports:
- **SSH:** 8022
- **Media Server:** 8080
- **Tailscale SOCKS:** 1055

### Important Paths:
- **Termux home:** `~` or `/data/data/com.termux/files/home`
- **Storage:** `~/storage/shared/`
- **Movies:** `~/storage/shared/Movies`
- **Boot scripts:** `~/.termux/boot/`
- **Server logs:** `~/server.log`

---

## 🎉 Congratulations!

You now have a fully functional phone media server!

### What You Can Do:
✅ Stream 1080p videos from your phone  
✅ Access from anywhere via Tailscale VPN  
✅ Transfer files via SSH/SFTP  
✅ Auto-start on boot  
✅ Control remotely via SSH  

### Next Steps:
1. Add more movies to `~/storage/shared/Movies`
2. Bookmark server URL in browser
3. Share Tailscale link with family
4. Set up regular backups
5. Monitor performance with `top`

**Enjoy your personal media server! 🍿**

---

## 📚 Additional Resources

- **Termux Wiki:** https://wiki.termux.com/
- **Tailscale Docs:** https://tailscale.com/kb/
- **FFmpeg Guide:** https://ffmpeg.org/documentation.html
- **Flask Docs:** https://flask.palletsprojects.com/

---

**Guide Version:** 1.0  
**Last Updated:** November 2026  
**Compatible With:** Android 7.0+, Termux 0.118+
