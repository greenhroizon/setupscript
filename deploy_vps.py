#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          KUCHLAG INDIA — FULL VPS DEPLOYMENT SCRIPT             ║
║          Domain: kuchalagindia.com                               ║
║          Stack: Node.js + Next.js + Express + MongoDB            ║
╚══════════════════════════════════════════════════════════════════╝

This script automates the COMPLETE deployment of the Jewellery
e-commerce application on a fresh KVM VPS running Ubuntu 22.04/24.04.

Components deployed:
  1. Backend API      (Express.js)  → port 5000
  2. Customer Frontend (Next.js 16) → port 3000
  3. Admin Panel      (React CRA)   → static, served by backend at /admin

Usage:
  1. SCP this file to your VPS:
     scp deploy_vps.py root@YOUR_VPS_IP:/root/

  2. SSH into VPS and run:
     ssh root@YOUR_VPS_IP
     python3 deploy_vps.py

Author: Auto-generated deployment script
"""

import os
import sys
import subprocess
import json
import time
import getpass
import shutil
import textwrap
import secrets
import string

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION — Edit these if needed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DOMAIN = "kuchalagindia.com"
DEPLOY_USER = "deploy"
PROJECT_DIR = "/var/www/jwellery"

REPOS = {
    "backend":  "https://github.com/greenhroizon/Render-Jwellery-Application.git",
    "frontend": "https://github.com/shreyash1231/Jwellery-Frontend-NEXT.git",
    "admin":    "https://github.com/shreyash1231/frontend-jwellery-admin-code.git",
}

BACKEND_PORT = 5000
FRONTEND_PORT = 3000

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLORS & HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

def banner():
    print(f"""{Colors.CYAN}{Colors.BOLD}
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║      💎  KUCHLAG INDIA — VPS AUTO DEPLOYMENT  💎            ║
    ║                                                              ║
    ║      Domain:   {DOMAIN:<40} ║
    ║      Stack:    Express + Next.js + React + MongoDB           ║
    ║      OS:       Ubuntu 22.04 / 24.04 LTS                     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    {Colors.RESET}""")

def log_step(step_num, total, message):
    print(f"\n{Colors.BOLD}{Colors.GREEN}[{step_num}/{total}] ▶ {message}{Colors.RESET}")
    print(f"{Colors.GREEN}{'─' * 60}{Colors.RESET}")

def log_info(message):
    print(f"  {Colors.BLUE}ℹ {message}{Colors.RESET}")

def log_success(message):
    print(f"  {Colors.GREEN}✅ {message}{Colors.RESET}")

def log_warning(message):
    print(f"  {Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def log_error(message):
    print(f"  {Colors.RED}❌ {message}{Colors.RESET}")

def log_cmd(command):
    print(f"  {Colors.MAGENTA}$ {command}{Colors.RESET}")

def run(command, check=True, capture=False, cwd=None, env=None):
    """Run a shell command with live output."""
    log_cmd(command)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        if capture:
            result = subprocess.run(
                command, shell=True, check=check,
                capture_output=True, text=True, cwd=cwd, env=merged_env
            )
            return result.stdout.strip()
        else:
            subprocess.run(
                command, shell=True, check=check, cwd=cwd, env=merged_env
            )
            return True
    except subprocess.CalledProcessError as e:
        if check:
            log_error(f"Command failed: {command}")
            if capture and e.stderr:
                log_error(f"stderr: {e.stderr}")
            return False
        return False

def ask(prompt, default=None, secret=False, required=True):
    """Interactive prompt with optional default."""
    display = f"  {Colors.CYAN}? {prompt}"
    if default:
        display += f" [{default}]"
    display += f": {Colors.RESET}"

    while True:
        if secret:
            value = getpass.getpass(display)
        else:
            value = input(display)

        if not value and default:
            return default
        if value:
            return value
        if not required:
            return ""
        print(f"  {Colors.RED}  This field is required.{Colors.RESET}")

def ask_yn(prompt, default="y"):
    """Yes/No prompt."""
    suffix = "[Y/n]" if default == "y" else "[y/N]"
    value = input(f"  {Colors.CYAN}? {prompt} {suffix}: {Colors.RESET}").strip().lower()
    if not value:
        return default == "y"
    return value in ("y", "yes")

def generate_jwt_secret():
    """Generate a cryptographically secure JWT secret."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(64))

def check_root():
    """Ensure script is run as root."""
    if os.geteuid() != 0:
        log_error("This script must be run as root!")
        print(f"  {Colors.YELLOW}Run: sudo python3 {sys.argv[0]}{Colors.RESET}")
        sys.exit(1)

def detect_ubuntu_version():
    """Detect Ubuntu version for correct repo URLs."""
    try:
        with open("/etc/os-release") as f:
            content = f.read()
        if "VERSION_CODENAME" in content:
            for line in content.split("\n"):
                if line.startswith("VERSION_CODENAME="):
                    return line.split("=")[1].strip().strip('"')
    except:
        pass
    return "jammy"  # Default to 22.04

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOTAL_STEPS = 14

def step_01_collect_env():
    """Collect all environment variables interactively."""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'═' * 60}")
    print(f"  ENVIRONMENT CONFIGURATION")
    print(f"  Fill in your credentials. Press Enter for defaults.")
    print(f"{'═' * 60}{Colors.RESET}")

    config = {}

    # --- MongoDB ---
    print(f"\n  {Colors.BOLD}📦 MongoDB Configuration{Colors.RESET}")
    config["INSTALL_MONGO_LOCAL"] = ask_yn("Install MongoDB locally on this VPS? (No = use Atlas)", "y")
    if config["INSTALL_MONGO_LOCAL"]:
        config["MONGODB_URI"] = "mongodb://localhost:27017/jwellery"
        log_info(f"Will use: {config['MONGODB_URI']}")
    else:
        config["MONGODB_URI"] = ask("MongoDB Atlas URI (mongodb+srv://...)")

    # --- JWT ---
    print(f"\n  {Colors.BOLD}🔐 JWT Authentication{Colors.RESET}")
    jwt_secret = generate_jwt_secret()
    log_info(f"Auto-generated JWT secret (64 chars)")
    config["JWT_SECRET"] = jwt_secret
    config["JWT_EXPIRES_IN"] = ask("JWT Token expiry", default="7d")

    # --- Email ---
    print(f"\n  {Colors.BOLD}📧 Email (Gmail + App Password){Colors.RESET}")
    log_info("Get app password: https://myaccount.google.com/apppasswords")
    config["EMAIL_USER"] = ask("Gmail address")
    config["EMAIL_PASSWORD"] = ask("Gmail App Password (16 chars)", secret=True)

    # --- AWS S3 ---
    print(f"\n  {Colors.BOLD}☁️  AWS S3 (Image/Video Uploads){Colors.RESET}")
    config["AWS_ACCESS_KEY_ID"] = ask("AWS Access Key ID")
    config["AWS_SECRET_ACCESS_KEY"] = ask("AWS Secret Access Key", secret=True)
    config["AWS_S3_BUCKET"] = ask("S3 Bucket Name")
    config["AWS_REGION"] = ask("AWS Region", default="ap-south-1")

    # --- Razorpay ---
    print(f"\n  {Colors.BOLD}💳 Razorpay (Payment Gateway){Colors.RESET}")
    config["RAZORPAY_KEY_ID"] = ask("Razorpay Key ID (rzp_...)")
    config["RAZORPAY_KEY_SECRET"] = ask("Razorpay Key Secret", secret=True)

    # --- Google OAuth ---
    print(f"\n  {Colors.BOLD}🔑 Google OAuth (optional){Colors.RESET}")
    config["GOOGLE_CLIENT_ID"] = ask("Google Client ID", required=False, default="")

    # --- CloudFront ---
    print(f"\n  {Colors.BOLD}🌐 CloudFront / Image CDN{Colors.RESET}")
    config["IMAGE_BASE_URL"] = ask("Image base URL", default="https://dpd52zzi6t5tf.cloudfront.net")

    # --- SSL ---
    print(f"\n  {Colors.BOLD}🔒 SSL Certificate (Let's Encrypt){Colors.RESET}")
    config["SSL_EMAIL"] = ask("Email for SSL certificate notifications", default=config["EMAIL_USER"])
    config["SETUP_SSL"] = ask_yn("Setup SSL with Let's Encrypt now?", "y")

    return config

def step_02_system_update():
    """Update system packages."""
    log_step(2, TOTAL_STEPS, "Updating System Packages")
    run("apt update && apt upgrade -y")
    log_success("System updated")

def step_03_install_dependencies():
    """Install Node.js 22, build tools, Nginx, git, certbot."""
    log_step(3, TOTAL_STEPS, "Installing System Dependencies")

    # Build tools (for argon2 native compilation)
    log_info("Installing build tools (python3, make, g++)...")
    run("apt install -y python3 make g++ gcc build-essential curl git ufw")

    # Node.js 22 LTS
    log_info("Installing Node.js 22 LTS...")
    run("curl -fsSL https://deb.nodesource.com/setup_22.x | bash -")
    run("apt install -y nodejs")
    node_ver = run("node -v", capture=True)
    npm_ver = run("npm -v", capture=True)
    log_success(f"Node.js {node_ver}, npm {npm_ver}")

    # PM2
    log_info("Installing PM2 process manager...")
    run("npm install -g pm2")
    log_success("PM2 installed")

    # Nginx
    log_info("Installing Nginx...")
    run("apt install -y nginx")
    run("systemctl enable nginx")
    run("systemctl start nginx")
    log_success("Nginx installed and running")

    # Certbot
    log_info("Installing Certbot for SSL...")
    run("apt install -y certbot python3-certbot-nginx")
    log_success("Certbot installed")

def step_04_setup_firewall():
    """Configure UFW firewall."""
    log_step(4, TOTAL_STEPS, "Configuring Firewall (UFW)")
    run("ufw allow OpenSSH")
    run("ufw allow 'Nginx Full'")
    run("echo 'y' | ufw enable", check=False)
    log_success("Firewall configured: SSH + HTTP + HTTPS allowed")

def step_05_install_mongodb(config):
    """Install MongoDB 7.0 locally."""
    if not config.get("INSTALL_MONGO_LOCAL"):
        log_step(5, TOTAL_STEPS, "Skipping Local MongoDB (using Atlas)")
        return

    log_step(5, TOTAL_STEPS, "Installing MongoDB 7.0")

    codename = detect_ubuntu_version()
    log_info(f"Detected Ubuntu codename: {codename}")

    # For Ubuntu 24.04 (noble), MongoDB 7.0 may need jammy repos
    mongo_codename = codename if codename in ("jammy", "focal") else "jammy"

    run("curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | "
        "gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor --yes")

    run(f'echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] '
        f'https://repo.mongodb.org/apt/ubuntu {mongo_codename}/mongodb-org/7.0 multiverse" | '
        f'tee /etc/apt/sources.list.d/mongodb-org-7.0.list')

    run("apt update")
    run("apt install -y mongodb-org")
    run("systemctl enable mongod")
    run("systemctl start mongod")

    # Verify
    time.sleep(2)
    result = run("mongosh --eval \"db.adminCommand('ping')\" --quiet", capture=True, check=False)
    if result:
        log_success("MongoDB 7.0 installed and running")
    else:
        log_warning("MongoDB may need a moment to start. Check: systemctl status mongod")

def step_06_create_deploy_user():
    """Create the deploy user if it doesn't exist."""
    log_step(6, TOTAL_STEPS, "Setting Up Deploy User")

    # Check if user exists
    result = run(f"id {DEPLOY_USER}", capture=True, check=False)
    if result:
        log_info(f"User '{DEPLOY_USER}' already exists")
    else:
        run(f"useradd -m -s /bin/bash {DEPLOY_USER}")
        run(f"usermod -aG sudo {DEPLOY_USER}")
        log_success(f"User '{DEPLOY_USER}' created")

    # Create project directory
    os.makedirs(PROJECT_DIR, exist_ok=True)
    run(f"chown -R {DEPLOY_USER}:{DEPLOY_USER} {PROJECT_DIR}")
    log_success(f"Project directory: {PROJECT_DIR}")

def step_07_clone_repos():
    """Clone all three repositories."""
    log_step(7, TOTAL_STEPS, "Cloning Repositories")

    for name, url in REPOS.items():
        target = os.path.join(PROJECT_DIR, name)
        if os.path.exists(target):
            log_warning(f"Directory {target} already exists — pulling latest...")
            run(f"git pull origin main || git pull origin master", cwd=target, check=False)
        else:
            log_info(f"Cloning {name}...")
            run(f"git clone {url} {target}")
            log_success(f"Cloned: {name}")

    run(f"chown -R {DEPLOY_USER}:{DEPLOY_USER} {PROJECT_DIR}")

def step_08_create_env_files(config):
    """Create all .env files for backend, frontend, and admin."""
    log_step(8, TOTAL_STEPS, "Creating Environment Files")

    # ── Backend .env ──
    backend_env = f"""# ============================================
# SERVER
# ============================================
PORT={BACKEND_PORT}
NODE_ENV=production

# ============================================
# DATABASE
# ============================================
MONGODB_URI={config['MONGODB_URI']}

# ============================================
# JWT AUTHENTICATION
# ============================================
JWT_SECRET={config['JWT_SECRET']}
JWT_ALGORITHM=HS256
JWT_EXPIRES_IN={config['JWT_EXPIRES_IN']}

# ============================================
# EMAIL (Gmail with App Password)
# ============================================
EMAIL_SERVICE=gmail
EMAIL_USER={config['EMAIL_USER']}
EMAIL_PASSWORD={config['EMAIL_PASSWORD']}
EMAIL_FROM={config['EMAIL_USER']}
OTP_EXPIRY_MINUTES=5

# ============================================
# AWS S3 (Image/Video Uploads)
# ============================================
AWS_ACCESS_KEY_ID={config['AWS_ACCESS_KEY_ID']}
AWS_SECRET_ACCESS_KEY={config['AWS_SECRET_ACCESS_KEY']}
AWS_S3_BUCKET={config['AWS_S3_BUCKET']}
AWS_REGION={config['AWS_REGION']}

# ============================================
# RAZORPAY (Payment Gateway)
# ============================================
RAZORPAY_KEY_ID={config['RAZORPAY_KEY_ID']}
RAZORPAY_KEY_SECRET={config['RAZORPAY_KEY_SECRET']}

# ============================================
# GOOGLE AUTH
# ============================================
GOOGLE_CLIENT_ID={config.get('GOOGLE_CLIENT_ID', '')}
GOOGLE_CLIENT_IDS={config.get('GOOGLE_CLIENT_ID', '')}

# ============================================
# CORS
# ============================================
CORS_ORIGIN=https://{DOMAIN},https://www.{DOMAIN}

# ============================================
# SECURITY
# ============================================
ENABLE_HELMET=true
ENABLE_HSTS=true
ENFORCE_HTTPS=true
ALLOW_CREDENTIALS=true
"""
    backend_env_path = os.path.join(PROJECT_DIR, "backend", ".env")
    with open(backend_env_path, "w") as f:
        f.write(backend_env)
    os.chmod(backend_env_path, 0o600)
    log_success("Backend .env created")

    # ── Frontend .env.local ──
    frontend_env = f"""NEXT_PUBLIC_API_URL=https://{DOMAIN}
NEXT_PUBLIC_IMAGE_BASE_URL={config['IMAGE_BASE_URL']}
NEXT_PUBLIC_GOOGLE_CLIENT_ID={config.get('GOOGLE_CLIENT_ID', '')}
NEXT_PUBLIC_RAZORPAY_KEY_ID={config['RAZORPAY_KEY_ID']}
"""
    frontend_env_path = os.path.join(PROJECT_DIR, "frontend", ".env.local")
    with open(frontend_env_path, "w") as f:
        f.write(frontend_env)
    log_success("Frontend .env.local created")

    # ── Admin .env ──
    admin_env = f"""REACT_APP_BASE_URL=https://{DOMAIN}
REACT_APP_IMAGE_URL={config['IMAGE_BASE_URL']}
REACT_APP_SHOW_CONSOLE=false
"""
    admin_env_path = os.path.join(PROJECT_DIR, "admin", ".env")
    with open(admin_env_path, "w") as f:
        f.write(admin_env)
    log_success("Admin .env created")

    # Set ownership
    run(f"chown -R {DEPLOY_USER}:{DEPLOY_USER} {PROJECT_DIR}")

def step_09_install_and_build():
    """Install npm dependencies and build all apps."""
    log_step(9, TOTAL_STEPS, "Installing Dependencies & Building Apps")

    build_env = os.environ.copy()
    build_env["NODE_OPTIONS"] = "--max-old-space-size=4096"

    # — Check and add swap if RAM < 3GB —
    log_info("Checking available memory...")
    mem_info = run("free -m | awk '/Mem:/ {print $2}'", capture=True)
    try:
        total_ram = int(mem_info)
        if total_ram < 3072:
            log_warning(f"Low RAM detected ({total_ram}MB). Adding 2GB swap space...")
            swap_exists = run("swapon --show | grep -c /swapfile", capture=True, check=False)
            if not swap_exists or swap_exists == "0":
                run("fallocate -l 2G /swapfile")
                run("chmod 600 /swapfile")
                run("mkswap /swapfile")
                run("swapon /swapfile")
                # Make permanent
                run("grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab")
                log_success("2GB swap space added")
            else:
                log_info("Swap already exists")
    except (ValueError, TypeError):
        pass

    # ── 1. Backend ──
    print(f"\n  {Colors.BOLD}📦 [1/3] Backend — npm install{Colors.RESET}")
    backend_dir = os.path.join(PROJECT_DIR, "backend")
    run(f"npm install --build-from-source=argon2", cwd=backend_dir)
    log_success("Backend dependencies installed")

    # Enable trust proxy in app.js
    log_info("Enabling trust proxy in app.js...")
    app_js_path = os.path.join(backend_dir, "app.js")
    try:
        with open(app_js_path, "r") as f:
            content = f.read()
        content = content.replace(
            '// app.set("trust proxy", 1);',
            'app.set("trust proxy", 1);'
        )
        with open(app_js_path, "w") as f:
            f.write(content)
        log_success("trust proxy enabled in app.js")
    except Exception as e:
        log_warning(f"Could not modify app.js: {e}")

    # ── 2. Admin Panel (build → copy to backend/admin) ──
    print(f"\n  {Colors.BOLD}📦 [2/3] Admin Panel — npm install + build{Colors.RESET}")
    admin_dir = os.path.join(PROJECT_DIR, "admin")
    run("npm install", cwd=admin_dir)
    log_info("Building admin panel (this may take 2–3 minutes)...")
    run("npm run build", cwd=admin_dir, env=build_env)

    # Copy built admin to backend/admin
    admin_dest = os.path.join(backend_dir, "admin")
    if os.path.exists(admin_dest):
        shutil.rmtree(admin_dest)
    admin_build = os.path.join(admin_dir, "build")
    if os.path.exists(admin_build):
        shutil.copytree(admin_build, admin_dest)
        log_success("Admin build copied to backend/admin/")
    else:
        log_warning("Admin build folder not found — admin panel may not work")

    # ── 3. Frontend (Next.js) ──
    print(f"\n  {Colors.BOLD}📦 [3/3] Frontend (Next.js) — npm install + build{Colors.RESET}")
    frontend_dir = os.path.join(PROJECT_DIR, "frontend")
    run("npm install", cwd=frontend_dir)
    log_info("Building Next.js frontend (this may take 3–5 minutes)...")
    run("npm run build", cwd=frontend_dir, env=build_env)
    log_success("Frontend built successfully")

    # Set ownership
    run(f"chown -R {DEPLOY_USER}:{DEPLOY_USER} {PROJECT_DIR}")

def step_10_setup_pm2():
    """Start apps with PM2 and configure auto-start."""
    log_step(10, TOTAL_STEPS, "Starting Apps with PM2")

    backend_dir = os.path.join(PROJECT_DIR, "backend")
    frontend_dir = os.path.join(PROJECT_DIR, "frontend")

    # Stop existing processes if any
    run("pm2 delete all", check=False)

    # Start backend
    log_info("Starting backend (Express.js) on port 5000...")
    run(f"pm2 start server.js --name jwellery-backend --cwd {backend_dir} "
        f"--env production --max-memory-restart 500M")

    # Start frontend
    log_info("Starting frontend (Next.js) on port 3000...")
    run(f"pm2 start npm --name jwellery-frontend --cwd {frontend_dir} "
        f"-- start")

    # Wait for apps to start
    time.sleep(5)

    # Check status
    run("pm2 status")

    # Auto-start on reboot
    log_info("Configuring auto-start on boot...")
    startup_cmd = run("pm2 startup systemd -u root --hp /root | tail -1", capture=True, check=False)
    if startup_cmd and "sudo" in str(startup_cmd):
        run(startup_cmd, check=False)
    run("pm2 save")

    # Install log rotation
    run("pm2 install pm2-logrotate", check=False)
    run("pm2 set pm2-logrotate:max_size 10M", check=False)
    run("pm2 set pm2-logrotate:retain 7", check=False)

    log_success("PM2 configured with auto-restart and log rotation")

def step_11_configure_nginx():
    """Setup Nginx reverse proxy configuration."""
    log_step(11, TOTAL_STEPS, "Configuring Nginx Reverse Proxy")

    nginx_config = f"""# ═══════════════════════════════════════════════════════
# {DOMAIN} — Nginx Configuration
# Auto-generated by deploy_vps.py
# ═══════════════════════════════════════════════════════

# Redirect HTTP → HTTPS (Certbot will update this)
server {{
    listen 80;
    listen [::]:80;
    server_name {DOMAIN} www.{DOMAIN};

    # During initial setup (before SSL), serve directly
    # After Certbot runs, this will redirect to HTTPS

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml application/xml+rss text/javascript
               image/svg+xml;

    # Max upload size (for product images/videos)
    client_max_body_size 50M;

    # ── Backend API ──
    location /api/ {{
        proxy_pass http://127.0.0.1:{BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }}

    # ── Admin Panel (served by Express as static) ──
    location /admin {{
        proxy_pass http://127.0.0.1:{BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}

    # ── Next.js Static Assets (cache-friendly) ──
    location /_next/static/ {{
        proxy_pass http://127.0.0.1:{FRONTEND_PORT};
        proxy_cache_valid 200 60d;
        add_header Cache-Control "public, max-age=5184000, immutable";
    }}

    # ── Frontend (Next.js — catch-all) ──
    location / {{
        proxy_pass http://127.0.0.1:{FRONTEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}
}}
"""
    config_path = "/etc/nginx/sites-available/jwellery"
    with open(config_path, "w") as f:
        f.write(nginx_config)

    # Enable site
    enabled_path = "/etc/nginx/sites-enabled/jwellery"
    if os.path.exists(enabled_path):
        os.remove(enabled_path)
    os.symlink(config_path, enabled_path)

    # Remove default site
    default_site = "/etc/nginx/sites-enabled/default"
    if os.path.exists(default_site):
        os.remove(default_site)

    # Test and reload
    result = run("nginx -t", check=False)
    if result:
        run("systemctl reload nginx")
        log_success("Nginx configured and reloaded")
    else:
        log_error("Nginx config test failed! Check: nginx -t")

def step_12_setup_ssl(config):
    """Setup SSL certificate with Let's Encrypt."""
    if not config.get("SETUP_SSL"):
        log_step(12, TOTAL_STEPS, "Skipping SSL Setup (manual later)")
        log_info(f"Run later: sudo certbot --nginx -d {DOMAIN} -d www.{DOMAIN}")
        return

    log_step(12, TOTAL_STEPS, "Setting Up SSL (Let's Encrypt)")

    log_info(f"Requesting SSL certificate for {DOMAIN} and www.{DOMAIN}...")
    log_warning("Make sure DNS A records point to this server BEFORE this step!")
    print()

    result = run(
        f"certbot --nginx -d {DOMAIN} -d www.{DOMAIN} "
        f"--email {config['SSL_EMAIL']} --agree-tos --no-eff-email --non-interactive",
        check=False
    )

    if result:
        log_success("SSL certificate installed!")
        # Setup auto-renewal
        run("certbot renew --dry-run", check=False)
        # Add cron for renewal
        cron_line = "0 2 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx"
        run(f'(crontab -l 2>/dev/null | grep -v certbot; echo "{cron_line}") | crontab -', check=False)
        log_success("Auto-renewal cron job configured")
    else:
        log_warning("SSL setup failed — DNS may not have propagated yet.")
        log_info(f"Run manually later: sudo certbot --nginx -d {DOMAIN} -d www.{DOMAIN}")

def step_13_security_hardening():
    """Apply basic security hardening."""
    log_step(13, TOTAL_STEPS, "Applying Security Hardening")

    # fail2ban
    log_info("Installing fail2ban...")
    run("apt install -y fail2ban", check=False)
    run("systemctl enable fail2ban", check=False)
    run("systemctl start fail2ban", check=False)
    log_success("fail2ban installed")

    # Automatic security updates
    log_info("Enabling automatic security updates...")
    run("apt install -y unattended-upgrades", check=False)
    run("dpkg-reconfigure -plow unattended-upgrades -f noninteractive", check=False)
    log_success("Automatic security updates enabled")

def step_14_create_helper_scripts():
    """Create helper scripts for daily operations."""
    log_step(14, TOTAL_STEPS, "Creating Helper Scripts")

    # ── Redeploy script ──
    redeploy_script = f"""#!/bin/bash
set -e

echo "🔄 Starting redeployment of {DOMAIN}..."
echo "{'═' * 50}"

export NODE_OPTIONS="--max-old-space-size=4096"

# 1. Backend
echo ""
echo "📦 [1/3] Updating backend..."
cd {PROJECT_DIR}/backend
git pull origin main || git pull origin master
npm install --build-from-source=argon2
pm2 restart jwellery-backend
echo "✅ Backend updated"

# 2. Admin Panel
echo ""
echo "📦 [2/3] Updating admin panel..."
cd {PROJECT_DIR}/admin
git pull origin main || git pull origin master
npm install
npm run build
rm -rf {PROJECT_DIR}/backend/admin/*
cp -r build/* {PROJECT_DIR}/backend/admin/
echo "✅ Admin panel updated"

# 3. Frontend
echo ""
echo "📦 [3/3] Updating frontend..."
cd {PROJECT_DIR}/frontend
git pull origin main || git pull origin master
npm install
npm run build
pm2 restart jwellery-frontend
echo "✅ Frontend updated"

echo ""
echo "{'═' * 50}"
echo "✅ Deployment complete!"
pm2 status
"""
    redeploy_path = os.path.join(PROJECT_DIR, "redeploy.sh")
    with open(redeploy_path, "w") as f:
        f.write(redeploy_script)
    os.chmod(redeploy_path, 0o755)
    log_success(f"Created: {redeploy_path}")

    # ── Status check script ──
    status_script = f"""#!/bin/bash
echo "╔══════════════════════════════════════════════╗"
echo "║    {DOMAIN} — System Status              ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

echo "📊 PM2 Processes:"
pm2 status
echo ""

echo "🌐 Nginx:"
systemctl is-active nginx && echo "  ✅ Running" || echo "  ❌ Stopped"
echo ""

echo "🗄️  MongoDB:"
systemctl is-active mongod 2>/dev/null && echo "  ✅ Running" || echo "  ⚠️  Not local / not running"
echo ""

echo "💾 Disk Usage:"
df -h / | tail -1 | awk '{{print "  Used: "$3" / "$2" ("$5" full)"}}'
echo ""

echo "🧠 Memory:"
free -h | awk '/Mem:/ {{print "  Used: "$3" / "$2}}'
echo ""

echo "🔗 Endpoints:"
echo "  Frontend:  https://{DOMAIN}"
echo "  Admin:     https://{DOMAIN}/admin"
echo "  API:       https://{DOMAIN}/api/v1/user/get-all-banners"
"""
    status_path = os.path.join(PROJECT_DIR, "status.sh")
    with open(status_path, "w") as f:
        f.write(status_script)
    os.chmod(status_path, 0o755)
    log_success(f"Created: {status_path}")

    # ── Logs script ──
    logs_script = f"""#!/bin/bash
echo "Select logs to view:"
echo "  1) Backend logs"
echo "  2) Frontend logs"
echo "  3) All logs"
echo "  4) Nginx error log"
read -p "Choice [1-4]: " choice

case $choice in
    1) pm2 logs jwellery-backend --lines 100 ;;
    2) pm2 logs jwellery-frontend --lines 100 ;;
    3) pm2 logs --lines 50 ;;
    4) tail -100 /var/log/nginx/error.log ;;
    *) echo "Invalid choice" ;;
esac
"""
    logs_path = os.path.join(PROJECT_DIR, "logs.sh")
    with open(logs_path, "w") as f:
        f.write(logs_script)
    os.chmod(logs_path, 0o755)
    log_success(f"Created: {logs_path}")

    run(f"chown -R {DEPLOY_USER}:{DEPLOY_USER} {PROJECT_DIR}")

def print_summary(config):
    """Print final deployment summary."""
    print(f"""
{Colors.GREEN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        🎉  DEPLOYMENT COMPLETE!  🎉                             ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   🌐 Customer Website:  https://{DOMAIN:<30}  ║
║   🔧 Admin Panel:       https://{DOMAIN}/admin{' ' * (24 - len('/admin'))}  ║
║   📡 API Endpoint:      https://{DOMAIN}/api/v1{' ' * (24 - len('/api/v1'))}  ║
║                                                                  ║
║   📂 Project Directory:  {PROJECT_DIR:<35}  ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   Helper Scripts:                                                ║
║   • {PROJECT_DIR}/redeploy.sh   — Redeploy all apps    ║
║   • {PROJECT_DIR}/status.sh     — Check system status  ║
║   • {PROJECT_DIR}/logs.sh       — View application logs║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   Quick Commands:                                                ║
║   • pm2 status              — View running processes             ║
║   • pm2 logs                — View all logs                      ║
║   • pm2 restart all         — Restart all apps                   ║
║   • pm2 monit               — Live monitoring                    ║
║   • {PROJECT_DIR}/redeploy.sh — Update from git  ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   Admin Login:                                                   ║
║   • Email:    admin@yopmail.com                                  ║
║   • Password: Admin@123                                          ║
║   ⚠️  CHANGE THIS IMMEDIATELY after first login!                 ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
{Colors.RESET}""")

    if not config.get("SETUP_SSL") or True:
        print(f"""
{Colors.YELLOW}  📌 If SSL was skipped or failed, run:{Colors.RESET}
     sudo certbot --nginx -d {DOMAIN} -d www.{DOMAIN}

{Colors.YELLOW}  📌 If DNS hasn't propagated yet:{Colors.RESET}
     Check: https://dnschecker.org/#A/{DOMAIN}
     Then run the certbot command above.
""")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN EXECUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    banner()
    check_root()

    print(f"\n{Colors.YELLOW}  This script will set up your ENTIRE VPS from scratch.{Colors.RESET}")
    print(f"  {Colors.YELLOW}It will install: Node.js 22, MongoDB, Nginx, PM2, SSL{Colors.RESET}")
    print(f"  {Colors.YELLOW}and deploy all 3 apps (backend + frontend + admin).{Colors.RESET}\n")

    if not ask_yn("Ready to proceed?"):
        print("Aborted.")
        sys.exit(0)

    # Step 1: Collect configuration
    log_step(1, TOTAL_STEPS, "Collecting Configuration")
    config = step_01_collect_env()

    # Confirm before proceeding
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'═' * 60}")
    print(f"  CONFIGURATION SUMMARY")
    print(f"{'═' * 60}{Colors.RESET}")
    print(f"  Domain:        {DOMAIN}")
    print(f"  MongoDB:       {'Local' if config['INSTALL_MONGO_LOCAL'] else 'Atlas'}")
    print(f"  MongoDB URI:   {config['MONGODB_URI'][:50]}...")
    print(f"  Email:         {config['EMAIL_USER']}")
    print(f"  AWS Region:    {config['AWS_REGION']}")
    print(f"  AWS Bucket:    {config['AWS_S3_BUCKET']}")
    print(f"  Razorpay Key:  {config['RAZORPAY_KEY_ID']}")
    print(f"  Image CDN:     {config['IMAGE_BASE_URL']}")
    print(f"  SSL Setup:     {'Yes' if config['SETUP_SSL'] else 'Skip'}")
    print()

    if not ask_yn("Configuration looks correct? Start deployment?"):
        print("Aborted.")
        sys.exit(0)

    start_time = time.time()

    # Execute all steps
    step_02_system_update()
    step_03_install_dependencies()
    step_04_setup_firewall()
    step_05_install_mongodb(config)
    step_06_create_deploy_user()
    step_07_clone_repos()
    step_08_create_env_files(config)
    step_09_install_and_build()
    step_10_setup_pm2()
    step_11_configure_nginx()
    step_12_setup_ssl(config)
    step_13_security_hardening()
    step_14_create_helper_scripts()

    elapsed = int(time.time() - start_time)
    minutes = elapsed // 60
    seconds = elapsed % 60

    print_summary(config)

    print(f"\n  {Colors.GREEN}⏱  Total time: {minutes}m {seconds}s{Colors.RESET}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}  Interrupted by user. Partial setup may exist.{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}  Fatal error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
