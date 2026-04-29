#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║       KUCHLAG INDIA — BACKEND VPS DEPLOYMENT SCRIPT             ║
║       Domain: kuchalagindia.com                                  ║
║       Only Backend (Express.js + MongoDB) on VPS                 ║
║       Frontend & Admin are on Vercel                             ║
╚══════════════════════════════════════════════════════════════════╝

Usage:
  1. Upload to VPS:
     scp deploy_backend_vps.py root@YOUR_VPS_IP:/root/

  2. SSH in and run:
     ssh root@YOUR_VPS_IP
     python3 deploy_backend_vps.py
"""

import os
import sys
import subprocess
import time
import getpass
import secrets
import string

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DOMAIN = "kuchalagindia.com"
DEPLOY_USER = "deploy"
PROJECT_DIR = "/var/www/jwellery"
BACKEND_REPO = "https://github.com/greenhroizon/Render-Jwellery-Application.git"
BACKEND_PORT = 5000

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COLORS & HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class C:
    R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"; B = "\033[94m"
    M = "\033[95m"; CY = "\033[96m"; BD = "\033[1m"; RS = "\033[0m"

TOTAL_STEPS = 12

def banner():
    print(f"""{C.CY}{C.BD}
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║      💎  BACKEND VPS DEPLOYMENT — kuchalagindia.com  💎     ║
    ║                                                              ║
    ║      Backend:   Express.js + MongoDB   →  VPS                ║
    ║      Frontend:  Next.js                →  Vercel             ║
    ║      Admin:     React CRA              →  Vercel             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    {C.RS}""")

def step(num, msg):
    print(f"\n{C.BD}{C.G}[{num}/{TOTAL_STEPS}] ▶ {msg}{C.RS}")
    print(f"{C.G}{'─' * 60}{C.RS}")

def info(msg):    print(f"  {C.B}ℹ {msg}{C.RS}")
def ok(msg):      print(f"  {C.G}✅ {msg}{C.RS}")
def warn(msg):    print(f"  {C.Y}⚠️  {msg}{C.RS}")
def err(msg):     print(f"  {C.R}❌ {msg}{C.RS}")
def cmd_log(c):   print(f"  {C.M}$ {c}{C.RS}")

def run(command, check=True, capture=False, cwd=None, env=None):
    cmd_log(command)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    try:
        if capture:
            r = subprocess.run(command, shell=True, check=check,
                               capture_output=True, text=True, cwd=cwd, env=merged_env)
            return r.stdout.strip()
        else:
            subprocess.run(command, shell=True, check=check, cwd=cwd, env=merged_env)
            return True
    except subprocess.CalledProcessError:
        if check:
            err(f"Command failed: {command}")
        return False

def ask(prompt, default=None, secret=False, required=True):
    display = f"  {C.CY}? {prompt}"
    if default:
        display += f" [{default}]"
    display += f": {C.RS}"
    while True:
        value = getpass.getpass(display) if secret else input(display)
        if not value and default:
            return default
        if value:
            return value
        if not required:
            return ""
        print(f"  {C.R}  Required field.{C.RS}")

def ask_yn(prompt, default="y"):
    suffix = "[Y/n]" if default == "y" else "[y/N]"
    v = input(f"  {C.CY}? {prompt} {suffix}: {C.RS}").strip().lower()
    if not v:
        return default == "y"
    return v in ("y", "yes")

def gen_secret(length=64):
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

def detect_codename():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("VERSION_CODENAME="):
                    return line.split("=")[1].strip().strip('"')
    except:
        pass
    return "jammy"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def step_01_collect():
    """Collect environment variables."""
    print(f"\n{C.BD}{C.Y}{'═' * 60}")
    print(f"  BACKEND CONFIGURATION")
    print(f"  Fill in your credentials. Press Enter for defaults.")
    print(f"{'═' * 60}{C.RS}")

    cfg = {}

    # --- Vercel URLs ---
    print(f"\n  {C.BD}🌐 Vercel Frontend URLs{C.RS}")
    info("These are needed for CORS — backend must allow requests from your Vercel apps")
    cfg["FRONTEND_URL"] = ask("Frontend Vercel URL (e.g. https://kuchalagindia.vercel.app or https://kuchalagindia.com)")
    cfg["ADMIN_URL"] = ask("Admin Panel Vercel URL (e.g. https://admin-kuchalag.vercel.app)", required=False, default="")

    # Build CORS list
    cors_origins = [cfg["FRONTEND_URL"].rstrip("/")]
    if cfg["ADMIN_URL"]:
        cors_origins.append(cfg["ADMIN_URL"].rstrip("/"))
    # Always add domain variants
    cors_origins.append(f"https://{DOMAIN}")
    cors_origins.append(f"https://www.{DOMAIN}")
    # Deduplicate
    cfg["CORS_ORIGINS"] = ",".join(sorted(set(cors_origins)))
    info(f"CORS origins: {cfg['CORS_ORIGINS']}")

    # --- MongoDB ---
    print(f"\n  {C.BD}📦 MongoDB{C.RS}")
    cfg["INSTALL_MONGO"] = ask_yn("Install MongoDB locally on VPS? (No = use Atlas)", "y")
    if cfg["INSTALL_MONGO"]:
        cfg["MONGODB_URI"] = "mongodb://localhost:27017/jwellery"
        info(f"Will use: {cfg['MONGODB_URI']}")
    else:
        cfg["MONGODB_URI"] = ask("MongoDB Atlas URI (mongodb+srv://...)")

    # --- JWT ---
    print(f"\n  {C.BD}🔐 JWT{C.RS}")
    cfg["JWT_SECRET"] = gen_secret()
    info("Auto-generated 64-char JWT secret")
    cfg["JWT_EXPIRES_IN"] = ask("Token expiry", default="7d")

    # --- Email ---
    print(f"\n  {C.BD}📧 Email (Gmail + App Password){C.RS}")
    info("Get app password: https://myaccount.google.com/apppasswords")
    cfg["EMAIL_USER"] = ask("Gmail address")
    cfg["EMAIL_PASSWORD"] = ask("Gmail App Password (16 chars)", secret=True)

    # --- AWS S3 ---
    print(f"\n  {C.BD}☁️  AWS S3{C.RS}")
    cfg["AWS_ACCESS_KEY_ID"] = ask("AWS Access Key ID")
    cfg["AWS_SECRET_ACCESS_KEY"] = ask("AWS Secret Access Key", secret=True)
    cfg["AWS_S3_BUCKET"] = ask("S3 Bucket Name")
    cfg["AWS_REGION"] = ask("AWS Region", default="ap-south-1")

    # --- Razorpay ---
    print(f"\n  {C.BD}💳 Razorpay{C.RS}")
    cfg["RAZORPAY_KEY_ID"] = ask("Razorpay Key ID")
    cfg["RAZORPAY_KEY_SECRET"] = ask("Razorpay Key Secret", secret=True)

    # --- Google OAuth ---
    print(f"\n  {C.BD}🔑 Google OAuth (optional){C.RS}")
    cfg["GOOGLE_CLIENT_ID"] = ask("Google Client ID", required=False, default="")

    # --- SSL ---
    print(f"\n  {C.BD}🔒 SSL{C.RS}")
    cfg["SSL_EMAIL"] = ask("Email for SSL notifications", default=cfg["EMAIL_USER"])
    cfg["SETUP_SSL"] = ask_yn("Setup SSL now? (DNS must point to this server)", "y")

    return cfg


def step_02_update():
    step(2, "Updating System")
    run("apt update && apt upgrade -y")
    ok("System updated")


def step_03_install():
    step(3, "Installing Node.js 22, Nginx, PM2, Certbot")

    info("Installing build tools...")
    run("apt install -y python3 make g++ gcc build-essential curl git ufw")

    info("Installing Node.js 22 LTS...")
    run("curl -fsSL https://deb.nodesource.com/setup_22.x | bash -")
    run("apt install -y nodejs")
    node_v = run("node -v", capture=True)
    ok(f"Node.js {node_v}")

    info("Installing PM2...")
    run("npm install -g pm2")
    ok("PM2 installed")

    info("Installing Nginx...")
    run("apt install -y nginx")
    run("systemctl enable nginx")
    run("systemctl start nginx")
    ok("Nginx running")

    info("Installing Certbot...")
    run("apt install -y certbot python3-certbot-nginx")
    ok("Certbot installed")


def step_04_firewall():
    step(4, "Configuring Firewall")
    run("ufw allow OpenSSH")
    run("ufw allow 'Nginx Full'")
    run("echo 'y' | ufw enable", check=False)
    ok("Firewall: SSH + HTTP + HTTPS")


def step_05_mongodb(cfg):
    if not cfg["INSTALL_MONGO"]:
        step(5, "Skipping Local MongoDB (using Atlas)")
        return

    step(5, "Installing MongoDB 7.0")
    codename = detect_codename()
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
    time.sleep(2)
    ok("MongoDB 7.0 installed")


def step_06_user():
    step(6, "Setting Up Project Directory")
    result = run(f"id {DEPLOY_USER}", capture=True, check=False)
    if not result:
        run(f"useradd -m -s /bin/bash {DEPLOY_USER}")
        run(f"usermod -aG sudo {DEPLOY_USER}")
    os.makedirs(PROJECT_DIR, exist_ok=True)
    run(f"chown -R {DEPLOY_USER}:{DEPLOY_USER} {PROJECT_DIR}")
    ok(f"Project dir: {PROJECT_DIR}")


def step_07_clone():
    step(7, "Cloning Backend Repository")
    target = os.path.join(PROJECT_DIR, "backend")
    if os.path.exists(target):
        warn("Directory exists — pulling latest...")
        run("git pull origin main || git pull origin master", cwd=target, check=False)
    else:
        run(f"git clone {BACKEND_REPO} {target}")
    run(f"chown -R {DEPLOY_USER}:{DEPLOY_USER} {PROJECT_DIR}")
    ok("Backend repo cloned")


def step_08_env(cfg):
    step(8, "Creating .env File")

    env_content = f"""# ═══════════════════════════════════════════════════════
# BACKEND — kuchalagindia.com
# Auto-generated by deploy_backend_vps.py
# ═══════════════════════════════════════════════════════

# ── Server ──
PORT={BACKEND_PORT}
NODE_ENV=production

# ── Database ──
MONGODB_URI={cfg['MONGODB_URI']}

# ── JWT ──
JWT_SECRET={cfg['JWT_SECRET']}
JWT_ALGORITHM=HS256
JWT_EXPIRES_IN={cfg['JWT_EXPIRES_IN']}

# ── Email (Gmail) ──
EMAIL_SERVICE=gmail
EMAIL_USER={cfg['EMAIL_USER']}
EMAIL_PASSWORD={cfg['EMAIL_PASSWORD']}
EMAIL_FROM={cfg['EMAIL_USER']}
OTP_EXPIRY_MINUTES=5

# ── AWS S3 ──
AWS_ACCESS_KEY_ID={cfg['AWS_ACCESS_KEY_ID']}
AWS_SECRET_ACCESS_KEY={cfg['AWS_SECRET_ACCESS_KEY']}
AWS_S3_BUCKET={cfg['AWS_S3_BUCKET']}
AWS_REGION={cfg['AWS_REGION']}

# ── Razorpay ──
RAZORPAY_KEY_ID={cfg['RAZORPAY_KEY_ID']}
RAZORPAY_KEY_SECRET={cfg['RAZORPAY_KEY_SECRET']}

# ── Google Auth ──
GOOGLE_CLIENT_ID={cfg.get('GOOGLE_CLIENT_ID', '')}
GOOGLE_CLIENT_IDS={cfg.get('GOOGLE_CLIENT_ID', '')}

# ── CORS (Vercel frontends + domain) ──
CORS_ORIGIN={cfg['CORS_ORIGINS']}

# ── Security ──
ENABLE_HELMET=true
ENABLE_HSTS=true
ENFORCE_HTTPS=true
ALLOW_CREDENTIALS=true
"""
    env_path = os.path.join(PROJECT_DIR, "backend", ".env")
    with open(env_path, "w") as f:
        f.write(env_content)
    os.chmod(env_path, 0o600)
    ok(".env created with all credentials")


def step_09_build(cfg):
    step(9, "Installing Dependencies & Building")

    backend_dir = os.path.join(PROJECT_DIR, "backend")

    # Add swap if low RAM
    info("Checking memory...")
    try:
        mem = int(run("free -m | awk '/Mem:/ {print $2}'", capture=True))
        if mem < 3072:
            warn(f"Low RAM ({mem}MB) — adding 2GB swap...")
            swap_check = run("swapon --show | grep -c /swapfile", capture=True, check=False)
            if not swap_check or swap_check == "0":
                run("fallocate -l 2G /swapfile")
                run("chmod 600 /swapfile")
                run("mkswap /swapfile")
                run("swapon /swapfile")
                run("grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab")
                ok("2GB swap added")
    except:
        pass

    # Install dependencies
    info("Installing npm dependencies (argon2 needs native build)...")
    run("npm install --build-from-source=argon2", cwd=backend_dir)
    ok("Dependencies installed")

    # Enable trust proxy
    info("Enabling trust proxy in app.js...")
    app_js = os.path.join(backend_dir, "app.js")
    try:
        with open(app_js, "r") as f:
            content = f.read()
        content = content.replace(
            '// app.set("trust proxy", 1);',
            'app.set("trust proxy", 1);'
        )
        with open(app_js, "w") as f:
            f.write(content)
        ok("trust proxy enabled")
    except Exception as e:
        warn(f"Couldn't modify app.js: {e}")

    run(f"chown -R {DEPLOY_USER}:{DEPLOY_USER} {PROJECT_DIR}")


def step_10_pm2():
    step(10, "Starting Backend with PM2")

    backend_dir = os.path.join(PROJECT_DIR, "backend")

    run("pm2 delete jwellery-backend", check=False)

    info("Starting Express.js backend on port 5000...")
    run(f"pm2 start server.js --name jwellery-backend --cwd {backend_dir} "
        f"--max-memory-restart 500M")

    time.sleep(3)
    run("pm2 status")

    # Auto-start on reboot
    info("Configuring auto-start on boot...")
    startup_cmd = run("pm2 startup systemd -u root --hp /root | tail -1", capture=True, check=False)
    if startup_cmd and "sudo" in str(startup_cmd):
        run(startup_cmd, check=False)
    run("pm2 save")

    # Log rotation
    run("pm2 install pm2-logrotate", check=False)
    run("pm2 set pm2-logrotate:max_size 10M", check=False)
    run("pm2 set pm2-logrotate:retain 7", check=False)

    ok("PM2 running with auto-restart")


def step_11_nginx(cfg):
    step(11, "Configuring Nginx")

    nginx_conf = f"""# ═══════════════════════════════════════════════════════
# {DOMAIN} — Backend API Server
# Frontend & Admin are on Vercel
# ═══════════════════════════════════════════════════════

server {{
    listen 80;
    listen [::]:80;
    server_name {DOMAIN} www.{DOMAIN};

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript
               text/xml application/xml text/javascript;

    # Max upload size (product images/videos)
    client_max_body_size 50M;

    # ── All requests → Backend Express.js ──
    location / {{
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
}}
"""
    conf_path = "/etc/nginx/sites-available/jwellery"
    with open(conf_path, "w") as f:
        f.write(nginx_conf)

    enabled = "/etc/nginx/sites-enabled/jwellery"
    if os.path.exists(enabled):
        os.remove(enabled)
    os.symlink(conf_path, enabled)

    default = "/etc/nginx/sites-enabled/default"
    if os.path.exists(default):
        os.remove(default)

    if run("nginx -t", check=False):
        run("systemctl reload nginx")
        ok("Nginx configured and reloaded")
    else:
        err("Nginx config test failed! Run: nginx -t")


def step_12_ssl(cfg):
    if not cfg["SETUP_SSL"]:
        step(12, "Skipping SSL (run manually later)")
        info(f"sudo certbot --nginx -d {DOMAIN} -d www.{DOMAIN}")
        return

    step(12, "Setting Up SSL (Let's Encrypt)")
    warn("DNS A records must point to this server!")

    result = run(
        f"certbot --nginx -d {DOMAIN} -d www.{DOMAIN} "
        f"--email {cfg['SSL_EMAIL']} --agree-tos --no-eff-email --non-interactive",
        check=False
    )

    if result:
        ok("SSL certificate installed!")
        run("certbot renew --dry-run", check=False)
        cron = "0 2 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx"
        run(f'(crontab -l 2>/dev/null | grep -v certbot; echo "{cron}") | crontab -', check=False)
        ok("Auto-renewal configured")
    else:
        warn("SSL failed — DNS may not have propagated yet")
        info(f"Run later: sudo certbot --nginx -d {DOMAIN} -d www.{DOMAIN}")

    # Security extras
    info("Installing fail2ban...")
    run("apt install -y fail2ban", check=False)
    run("systemctl enable fail2ban && systemctl start fail2ban", check=False)
    ok("fail2ban installed")


def create_helper_scripts(cfg):
    """Create redeploy and status scripts."""

    # ── Redeploy ──
    redeploy = f"""#!/bin/bash
set -e
echo "🔄 Redeploying backend..."
cd {PROJECT_DIR}/backend
git pull origin main || git pull origin master
npm install --build-from-source=argon2
pm2 restart jwellery-backend
echo "✅ Backend redeployed!"
pm2 status
"""
    path = os.path.join(PROJECT_DIR, "redeploy.sh")
    with open(path, "w") as f:
        f.write(redeploy)
    os.chmod(path, 0o755)

    # ── Status ──
    status = f"""#!/bin/bash
echo "╔══════════════════════════════════════════╗"
echo "║  {DOMAIN} — Backend Status          ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "📊 PM2:"
pm2 status
echo ""
echo "🌐 Nginx:"
systemctl is-active nginx && echo "  ✅ Running" || echo "  ❌ Stopped"
echo ""
echo "🗄️  MongoDB:"
systemctl is-active mongod 2>/dev/null && echo "  ✅ Running" || echo "  ⚠️  Atlas / not running"
echo ""
echo "💾 Disk:"; df -h / | tail -1 | awk '{{print "  "$3" / "$2" ("$5")"}}'
echo "🧠 RAM:";  free -h | awk '/Mem:/ {{print "  "$3" / "$2}}'
echo ""
echo "🔗 API: https://{DOMAIN}/api/v1/user/get-all-banners"
echo ""
echo "📋 Vercel Frontends:"
echo "  Frontend: {cfg.get('FRONTEND_URL', 'N/A')}"
echo "  Admin:    {cfg.get('ADMIN_URL', 'N/A')}"
"""
    path = os.path.join(PROJECT_DIR, "status.sh")
    with open(path, "w") as f:
        f.write(status)
    os.chmod(path, 0o755)

    run(f"chown -R {DEPLOY_USER}:{DEPLOY_USER} {PROJECT_DIR}")
    ok("Helper scripts created: redeploy.sh, status.sh")


def print_summary(cfg):
    print(f"""
{C.G}{C.BD}
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          🎉  BACKEND DEPLOYMENT COMPLETE!  🎉                   ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   🔗 Backend API:     https://{DOMAIN}/api/v1              ║
║   🔗 Admin (Vercel):  {cfg.get('ADMIN_URL', 'N/A'):<40} ║
║   🔗 Frontend:        {cfg.get('FRONTEND_URL', 'N/A'):<40} ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   📂 Backend Dir:   {PROJECT_DIR}/backend               ║
║   📝 .env File:     {PROJECT_DIR}/backend/.env           ║
║   🔄 Redeploy:      {PROJECT_DIR}/redeploy.sh            ║
║   📊 Status:        {PROJECT_DIR}/status.sh              ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   PM2 Commands:                                                  ║
║   • pm2 status                 — Process status                  ║
║   • pm2 logs jwellery-backend  — View logs                       ║
║   • pm2 restart jwellery-backend — Restart                       ║
║   • pm2 monit                  — Live monitor                    ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║   ⚠️  NEXT: Set these in your Vercel projects:                   ║
║                                                                  ║
║   Frontend (.env on Vercel):                                     ║
║     NEXT_PUBLIC_API_URL = https://{DOMAIN}                  ║
║     NEXT_PUBLIC_IMAGE_BASE_URL = https://dpd52zzi6t5tf...        ║
║     NEXT_PUBLIC_RAZORPAY_KEY_ID = {cfg['RAZORPAY_KEY_ID']:<27} ║
║                                                                  ║
║   Admin (.env on Vercel):                                        ║
║     REACT_APP_BASE_URL = https://{DOMAIN}                   ║
║     REACT_APP_IMAGE_URL = https://dpd52zzi6t5tf...               ║
║     REACT_APP_SHOW_CONSOLE = false                               ║
║                                                                  ║
║   Default Admin Login (change immediately!):                     ║
║     Email:    admin@yopmail.com                                  ║
║     Password: Admin@123                                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
{C.RS}""")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def main():
    banner()

    if os.geteuid() != 0:
        err("Must run as root! Use: sudo python3 deploy_backend_vps.py")
        sys.exit(1)

    print(f"\n{C.Y}  This will install Node.js, MongoDB, Nginx, PM2, SSL on this server")
    print(f"  and deploy ONLY the backend Express.js API.{C.RS}")
    print(f"  {C.Y}Frontend & Admin will remain on Vercel.{C.RS}\n")

    if not ask_yn("Proceed?"):
        sys.exit(0)

    # Step 1: Collect
    step(1, "Collecting Configuration")
    cfg = step_01_collect()

    # Confirm
    print(f"\n{C.BD}{C.Y}{'═' * 60}")
    print(f"  SUMMARY")
    print(f"{'═' * 60}{C.RS}")
    print(f"  Domain:       {DOMAIN}")
    print(f"  MongoDB:      {'Local' if cfg['INSTALL_MONGO'] else 'Atlas'}")
    print(f"  CORS:         {cfg['CORS_ORIGINS']}")
    print(f"  Email:        {cfg['EMAIL_USER']}")
    print(f"  AWS Bucket:   {cfg['AWS_S3_BUCKET']}")
    print(f"  Razorpay:     {cfg['RAZORPAY_KEY_ID']}")
    print(f"  SSL:          {'Yes' if cfg['SETUP_SSL'] else 'Later'}")
    print()

    if not ask_yn("Correct? Start deployment?"):
        sys.exit(0)

    t0 = time.time()

    step_02_update()
    step_03_install()
    step_04_firewall()
    step_05_mongodb(cfg)
    step_06_user()
    step_07_clone()
    step_08_env(cfg)
    step_09_build(cfg)
    step_10_pm2()
    step_11_nginx(cfg)
    step_12_ssl(cfg)
    create_helper_scripts(cfg)

    elapsed = int(time.time() - t0)
    print_summary(cfg)
    print(f"\n  {C.G}⏱  Total time: {elapsed // 60}m {elapsed % 60}s{C.RS}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{C.Y}  Interrupted. Partial setup may exist.{C.RS}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{C.R}  Fatal: {e}{C.RS}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
