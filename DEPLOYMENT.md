# Health Tracker - Deployment Guide

This guide covers deploying the Health Tracker application to a traditional VPS (Virtual Private Server).

## Table of Contents
- [Prerequisites](#prerequisites)
- [Server Setup](#server-setup)
- [Application Installation](#application-installation)
- [Production Configuration](#production-configuration)
- [Running with Gunicorn](#running-with-gunicorn)
- [Nginx Reverse Proxy](#nginx-reverse-proxy)
- [SSL/HTTPS Setup](#sslhttps-setup)
- [Systemd Service](#systemd-service)
- [Database Backup](#database-backup)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Server Requirements
- **OS**: Ubuntu 22.04 LTS or Debian 11+ (recommended)
- **RAM**: Minimum 512MB (1GB recommended)
- **Storage**: 2GB minimum
- **Python**: 3.10 or higher
- **SSH Access**: Root or sudo user

### Domain Setup (Optional but Recommended)
- Domain name pointed to your server's IP address
- DNS A record configured (e.g., `habits.example.com`)

---

## Server Setup

### 1. Initial Server Configuration

Connect to your server via SSH:
```bash
ssh user@your-server-ip
```

Update system packages:
```bash
sudo apt update
sudo apt upgrade -y
```

Install required system packages:
```bash
sudo apt install -y python3 python3-pip python3-venv nginx git curl
```

### 2. Create Application User

Create a dedicated user for the application:
```bash
sudo adduser --system --group --home /opt/healthtracker healthtracker
```

---

## Application Installation

### 1. Clone Repository

Switch to the healthtracker user:
```bash
sudo su - healthtracker
```

Clone your application (or upload via SCP/SFTP):
```bash
git clone https://github.com/yourusername/HealthTracker.git /opt/healthtracker/app
# OR upload files manually to /opt/healthtracker/app
cd /opt/healthtracker/app
```

### 2. Install Python Dependencies

Install uv (modern Python package manager):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

Create virtual environment and install dependencies:
```bash
cd /opt/healthtracker/app
uv venv
source .venv/bin/activate
uv sync
```

### 3. Initialize Database

Create instance directory:
```bash
mkdir -p /opt/healthtracker/app/instance
```

Initialize the database:
```bash
uv run python -c "from models import init_database; init_database()"
```

Optionally seed with sample data:
```bash
uv run python seed_data.py
```

---

## Production Configuration

### 1. Environment Variables

Create production `.env` file:
```bash
cat > /opt/healthtracker/app/.env << 'EOF'
# Production Configuration
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
APP_PASSWORD=your_secure_password_here
DATABASE_PATH=/opt/healthtracker/app/instance/healthtracker.db
EOF
```

**IMPORTANT**: Replace `your_secure_password_here` with a strong password!

Generate a secure SECRET_KEY:
```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Set proper permissions:
```bash
chmod 600 /opt/healthtracker/app/.env
chown healthtracker:healthtracker /opt/healthtracker/app/.env
```

### 2. Set File Permissions

```bash
sudo chown -R healthtracker:healthtracker /opt/healthtracker
sudo chmod -R 755 /opt/healthtracker/app
sudo chmod 600 /opt/healthtracker/app/.env
sudo chmod 644 /opt/healthtracker/app/instance/healthtracker.db
```

Exit the healthtracker user:
```bash
exit
```

---

## Running with Gunicorn

### 1. Test Gunicorn

Switch to healthtracker user and test:
```bash
sudo su - healthtracker
cd /opt/healthtracker/app
source .venv/bin/activate
gunicorn -w 2 -b 127.0.0.1:8000 app:app
```

Press `Ctrl+C` to stop after verifying it works.

### 2. Gunicorn Configuration

Create Gunicorn config file:
```bash
cat > /opt/healthtracker/app/gunicorn_config.py << 'EOF'
# Gunicorn configuration
bind = "127.0.0.1:8000"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "/opt/healthtracker/logs/access.log"
errorlog = "/opt/healthtracker/logs/error.log"
loglevel = "info"

# Process naming
proc_name = "healthtracker"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
EOF
```

Create logs directory:
```bash
mkdir -p /opt/healthtracker/logs
chown healthtracker:healthtracker /opt/healthtracker/logs
exit
```

---

## Nginx Reverse Proxy

### 1. Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/healthtracker
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logs
    access_log /var/log/nginx/healthtracker_access.log;
    error_log /var/log/nginx/healthtracker_error.log;

    # Static files
    location /static {
        alias /opt/healthtracker/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }

    location ~ /(\.env|\.git) {
        deny all;
    }
}
```

### 2. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/healthtracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## SSL/HTTPS Setup

### Using Certbot (Let's Encrypt)

Install Certbot:
```bash
sudo apt install -y certbot python3-certbot-nginx
```

Obtain SSL certificate:
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

Follow the prompts and select:
- Enter email for renewal notifications
- Agree to terms of service
- Choose to redirect HTTP to HTTPS (option 2)

Test auto-renewal:
```bash
sudo certbot renew --dry-run
```

Certbot will automatically renew certificates before they expire.

---

## Systemd Service

### 1. Create Service File

```bash
sudo nano /etc/systemd/system/healthtracker.service
```

Add the following configuration:

```ini
[Unit]
Description=Health Tracker Flask Application
After=network.target

[Service]
Type=notify
User=healthtracker
Group=healthtracker
WorkingDirectory=/opt/healthtracker/app
Environment="PATH=/opt/healthtracker/app/.venv/bin"
ExecStart=/opt/healthtracker/app/.venv/bin/gunicorn -c /opt/healthtracker/app/gunicorn_config.py app:app

# Restart policy
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable healthtracker
sudo systemctl start healthtracker
```

### 3. Check Service Status

```bash
sudo systemctl status healthtracker
```

View logs:
```bash
sudo journalctl -u healthtracker -f
```

---

## Database Backup

### 1. Create Backup Script

```bash
sudo nano /opt/healthtracker/backup.sh
```

```bash
#!/bin/bash
# Health Tracker Database Backup Script

BACKUP_DIR="/opt/healthtracker/backups"
DB_PATH="/opt/healthtracker/app/instance/healthtracker.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/healthtracker_$DATE.db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Create backup
cp "$DB_PATH" "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "healthtracker_*.db.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

Make executable:
```bash
sudo chmod +x /opt/healthtracker/backup.sh
sudo chown healthtracker:healthtracker /opt/healthtracker/backup.sh
```

### 2. Schedule Daily Backups

```bash
sudo crontab -u healthtracker -e
```

Add this line for daily backups at 2 AM:
```cron
0 2 * * * /opt/healthtracker/backup.sh >> /opt/healthtracker/logs/backup.log 2>&1
```

### 3. Manual Backup

```bash
sudo su - healthtracker
/opt/healthtracker/backup.sh
```

---

## Maintenance

### Viewing Logs

Application logs:
```bash
sudo tail -f /opt/healthtracker/logs/error.log
sudo tail -f /opt/healthtracker/logs/access.log
```

Systemd logs:
```bash
sudo journalctl -u healthtracker -f
```

Nginx logs:
```bash
sudo tail -f /var/log/nginx/healthtracker_access.log
sudo tail -f /var/log/nginx/healthtracker_error.log
```

### Restarting Services

Restart application:
```bash
sudo systemctl restart healthtracker
```

Restart Nginx:
```bash
sudo systemctl restart nginx
```

### Updating Application

1. Pull latest code:
```bash
sudo su - healthtracker
cd /opt/healthtracker/app
git pull
```

2. Update dependencies:
```bash
source .venv/bin/activate
uv sync
```

3. Restart service:
```bash
exit
sudo systemctl restart healthtracker
```

### Database Migrations

If schema changes are needed, create a backup first:
```bash
sudo su - healthtracker
/opt/healthtracker/backup.sh
```

Then apply changes manually or via migration script.

---

## Troubleshooting

### Application Won't Start

Check service status:
```bash
sudo systemctl status healthtracker
```

Check for errors in logs:
```bash
sudo journalctl -u healthtracker -n 50
```

Verify environment variables:
```bash
sudo su - healthtracker
cd /opt/healthtracker/app
cat .env  # Check SECRET_KEY and APP_PASSWORD are set
```

### 502 Bad Gateway

Check if Gunicorn is running:
```bash
sudo systemctl status healthtracker
```

Check Gunicorn is listening on correct port:
```bash
sudo netstat -tlnp | grep 8000
```

Restart services:
```bash
sudo systemctl restart healthtracker
sudo systemctl restart nginx
```

### Database Locked Errors

Check file permissions:
```bash
ls -la /opt/healthtracker/app/instance/
```

Ensure healthtracker user owns the database:
```bash
sudo chown healthtracker:healthtracker /opt/healthtracker/app/instance/healthtracker.db
```

### Permission Denied Errors

Fix ownership recursively:
```bash
sudo chown -R healthtracker:healthtracker /opt/healthtracker
```

Fix .env permissions:
```bash
sudo chmod 600 /opt/healthtracker/app/.env
```

### High Memory Usage

Reduce Gunicorn workers in `/opt/healthtracker/app/gunicorn_config.py`:
```python
workers = 2  # Reduce to 1 if memory is limited
```

Restart:
```bash
sudo systemctl restart healthtracker
```

### SSL Certificate Issues

Check certificate status:
```bash
sudo certbot certificates
```

Renew manually:
```bash
sudo certbot renew
```

---

## Security Checklist

Before going live, verify:

- [ ] `.env` file has strong SECRET_KEY (32+ characters)
- [ ] APP_PASSWORD is strong and unique
- [ ] `.env` file permissions are 600
- [ ] FLASK_ENV is set to "production"
- [ ] SSL/HTTPS is enabled
- [ ] Firewall is configured (UFW or iptables)
- [ ] SSH is secured (key-based auth, disable root login)
- [ ] Automatic security updates enabled
- [ ] Database backups are scheduled
- [ ] Application runs as non-root user

---

## Quick Reference Commands

```bash
# Service management
sudo systemctl start healthtracker
sudo systemctl stop healthtracker
sudo systemctl restart healthtracker
sudo systemctl status healthtracker

# View logs
sudo journalctl -u healthtracker -f
sudo tail -f /opt/healthtracker/logs/error.log

# Backup database
sudo su - healthtracker -c '/opt/healthtracker/backup.sh'

# Update application
cd /opt/healthtracker/app && git pull
sudo systemctl restart healthtracker

# Check Nginx configuration
sudo nginx -t
sudo systemctl reload nginx
```

---

## Support

For issues or questions:
1. Check logs first: `sudo journalctl -u healthtracker -n 100`
2. Verify configuration: `.env` file, Nginx config, systemd service
3. Review security checklist
4. Test with `uv run python app.py` to isolate Gunicorn/Nginx issues

---

## License

MIT License - See LICENSE file for details
