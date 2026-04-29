#!/usr/bin/env python3
"""
Backend Setup & Run Script — Kuchlag India
Clone repo → Create .env → Install deps → PM2 forever → Show URL
"""

import os, sys, subprocess, time

PROJECT_DIR = "/var/www/jwellery/backend"
REPO = "https://github.com/greenhroizon/Render-Jwellery-Application.git"
PORT = 5000

# ── All your credentials ──
ENV = """PORT=5000
NODE_ENV=production
LOG_LEVEL=production
MONGODB_URI=mongodb+srv://kuchalagteam_db_user:WWL9PpXE9Nx4pmuJ@kuchalag.651c2jx.mongodb.net/
JWT_SECRET=K8xvR2mT4nL7qW9pA3yJ6hD1fB5eC0gS8uN2vX4wZ7kM3rP9tQ6jY1dF8aH5lE
JWT_ALGORITHM=HS256
JWT_EXPIRES_IN=7d
EMAIL_SERVICE=gmail
EMAIL_USER=kuchalagteam@gmail.com
EMAIL_PASSWORD=zbzr ampu luur cbed
EMAIL_FROM=noreply@jwellery.com
OTP_EXPIRY_MINUTES=5
AWS_ACCESS_KEY_ID=AKIA4B37UNR3AGCG6QXQ
AWS_SECRET_ACCESS_KEY=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
AWS_S3_BUCKET=kuch-alag-s3
AWS_REGION=ap-south-1
RAZORPAY_KEY_ID=rzp_live_SagXbIhpAynO7y
RAZORPAY_KEY_SECRET=d96tSCJI1yidlYDZlbR2geIz
GOOGLE_CLIENT_ID=266189706891-kn2efti3o0rj3sk12tm6mip4dq2knc6o.apps.googleusercontent.com
GOOGLE_CLIENT_IDS=266189706891-kn2efti3o0rj3sk12tm6mip4dq2knc6o.apps.googleusercontent.com
CORS_ORIGIN=https://www.kuchalagindia.com,https://kuchalagindia.com,https://kuchalagindiarepov2.vercel.app,https://jwellery-frontend-next.vercel.app,https://frontend-jwellery-admin-code-so5o.vercel.app,https://frontend-jwellery-admin-code-ywsf.vercel.app,http://localhost:3000,http://localhost:5173
ENABLE_HELMET=true
ENABLE_HSTS=false
ENFORCE_HTTPS=false
ALLOW_CREDENTIALS=true
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_MS=900000
AUTH_RATE_LIMIT_MAX=20
UPLOAD_RATE_LIMIT_MAX=60
"""

def run(cmd, cwd=None):
    print(f"  \033[95m$ {cmd}\033[0m")
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

def run_capture(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.stdout.strip()

def main():
    print("\n\033[1m\033[96m  💎 Kuchlag India — Backend Setup\033[0m\n")

    # 1. Install Node.js if missing
    if not run_capture("which node"):
        print("\n\033[1m[1] Installing Node.js 22...\033[0m")
        run("curl -fsSL https://deb.nodesource.com/setup_22.x | bash -")
        run("apt install -y nodejs")
    print(f"  \033[92m✅ Node.js {run_capture('node -v')}\033[0m")

    # 2. Install PM2 if missing
    if not run_capture("which pm2"):
        print("\n\033[1m[2] Installing PM2...\033[0m")
        run("npm install -g pm2")
    print(f"  \033[92m✅ PM2 installed\033[0m")

    # 3. Install build tools (for argon2)
    print("\n\033[1m[3] Installing build tools...\033[0m")
    run("apt install -y python3 make g++ build-essential git -qq")
    print(f"  \033[92m✅ Build tools ready\033[0m")

    # 4. Clone repo
    print("\n\033[1m[4] Setting up backend code...\033[0m")
    os.makedirs(os.path.dirname(PROJECT_DIR), exist_ok=True)
    if os.path.exists(os.path.join(PROJECT_DIR, "server.js")):
        print("  Already cloned — pulling latest...")
        run("git pull origin main || git pull origin master", cwd=PROJECT_DIR)
    else:
        if os.path.exists(PROJECT_DIR):
            run(f"rm -rf {PROJECT_DIR}")
        run(f"git clone {REPO} {PROJECT_DIR}")
    print(f"  \033[92m✅ Code ready at {PROJECT_DIR}\033[0m")

    # 5. Create .env
    print("\n\033[1m[5] Creating .env file...\033[0m")
    env_path = os.path.join(PROJECT_DIR, ".env")
    with open(env_path, "w") as f:
        f.write(ENV)
    os.chmod(env_path, 0o600)
    print(f"  \033[92m✅ .env created with all credentials\033[0m")

    # 6. Add swap if low RAM
    try:
        mem = int(run_capture("free -m | awk '/Mem:/ {print $2}'"))
        if mem < 2048:
            print(f"\n  \033[93m⚠️ Low RAM ({mem}MB) — adding swap...\033[0m")
            if run_capture("swapon --show | grep -c /swapfile") == "0":
                run("fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile")
                run("grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab")
    except:
        pass

    # 7. npm install
    print("\n\033[1m[6] Installing npm dependencies...\033[0m")
    run("npm install --build-from-source=argon2", cwd=PROJECT_DIR)
    print(f"  \033[92m✅ Dependencies installed\033[0m")

    # 8. Start with PM2
    print("\n\033[1m[7] Starting backend with PM2...\033[0m")
    run("pm2 delete jwellery-backend 2>/dev/null; true")
    run(f"pm2 start server.js --name jwellery-backend --cwd {PROJECT_DIR} --max-memory-restart 500M")
    time.sleep(3)

    # 9. Start HTTPS Tunnel (Cloudflare)
    if not run_capture("which cloudflared"):
        print("\n\033[1m[8] Installing Cloudflare Tunnel...\033[0m")
        run("wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb")
        run("dpkg -i cloudflared-linux-amd64.deb")
        run("rm cloudflared-linux-amd64.deb")
        
    print("\n\033[1m[9] Starting HTTPS Tunnel with PM2...\033[0m")
    run("pm2 delete jwellery-tunnel 2>/dev/null; true")
    run("pm2 start 'cloudflared tunnel --url http://localhost:5000' --name jwellery-tunnel")
    
    print("  Waiting 5 seconds for tunnel URL...")
    time.sleep(5)
    
    # Extract URL from logs
    log_path = run_capture("ls ~/.pm2/logs/jwellery-tunnel-error*.log 2>/dev/null | tail -1")
    tunnel_url = ""
    if log_path:
        tunnel_url = run_capture(f"grep -o 'https://.*\.trycloudflare.com' {log_path} | tail -1")
        
    if not tunnel_url:
        tunnel_url = "Run 'pm2 logs jwellery-tunnel' to see the trycloudflare.com URL"

    # Auto-start on reboot
    run("pm2 startup systemd -u root --hp /root --no-daemon 2>/dev/null; true")
    run("pm2 save")

    # 9. Get IP and show result
    vps_ip = run_capture("curl -s ifconfig.me 2>/dev/null") or run_capture("hostname -I | awk '{print $1}'")

    print("\n")
    run("pm2 status")

    print(f"""
\033[1m\033[92m
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║           🎉  BACKEND IS RUNNING FOREVER!  🎉               ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   🌐 YOUR FREE HTTPS URL (Use this in Vercel):               ║
║                                                              ║
║      {tunnel_url:<56}║
║                                                              ║
║   🔗 Local VPS IP alternative:                               ║
║      http://{vps_ip}:{PORT:<39}║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   Set in Vercel (Frontend):                                  ║
║     NEXT_PUBLIC_API_URL = {tunnel_url:<31}║
║                                                              ║
║   Set in Vercel (Admin):                                     ║
║     REACT_APP_BASE_URL = {tunnel_url:<32}║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   Commands:                                                  ║
║     pm2 logs jwellery-backend    — View logs                 ║
║     pm2 restart jwellery-backend — Restart                   ║
║     pm2 status                   — Status                    ║
║     pm2 monit                    — Live monitor              ║
║                                                              ║
║   Backend auto-restarts on crash & server reboot.            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
\033[0m""")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("\033[91m  ❌ Run as root: sudo python3 deploy_backend_vps.py\033[0m")
        sys.exit(1)
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Interrupted.")
    except Exception as e:
        print(f"\n\033[91m  ❌ Error: {e}\033[0m")
        import traceback; traceback.print_exc()
        sys.exit(1)
