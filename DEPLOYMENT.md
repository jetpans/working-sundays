# Working Sundays — Deployment & Environment Configuration

## Overview

This document covers all environment variables, setup steps, and configuration needed to deploy Working Sundays to your server.

**Application Details:**
- **Frontend**: Next.js running on port 3001 (proxied via nginx)
- **Backend**: Flask API running on port 5001 (proxied via nginx)
- **Domain**: `sundays.jetpans.com`
- **Data Storage**: Docker named volumes (managed by Docker, not relative paths)
- **Auth**: JWT-based with persistent user store

---

## GitHub Secrets (Required for CI/CD)

These secrets must be configured in your GitHub repository settings under **Settings → Secrets and variables → Actions**:

| Secret | Description | Example |
|--------|-------------|---------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | `jetpans` |
| `DOCKERHUB_TOKEN` | Your Docker Hub personal access token | (generate in Docker Hub) |
| `SSH_HOST` | Your server's IP or hostname | `159.69.223.82` |
| `SSH_USERNAME` | SSH user (usually `root`) | `root` |
| `SSH_PRIVATE_KEY` | Your SSH private key | (paste your ~/.ssh/id_rsa) |

---

## Server Environment Variables

These must be set on your server **before running the deploy script**:

### Required

| Variable | Purpose | Example |
|----------|---------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT token signing (min 32 chars) | Generate with: `openssl rand -base64 48` |

### Optional (with defaults)

| Variable | Default | Purpose |
|----------|---------|---------|
| `FLASK_ENV` | `production` | Flask environment mode |
| `DEBUG` | `false` | Enable Flask debug mode (never true in production) |
| `ALLOWED_ORIGINS` | `https://sundays.jetpans.com` | CORS allowed origins (comma-separated) |
| `JWT_ACCESS_TOKEN_EXPIRES_HOURS` | `12` | JWT token expiration in hours |
| `METRICS_SAMPLE_SECONDS` | `1.0` | Metrics sampling interval |

**Note**: The frontend defaults to connecting to `sundays.jetpans.com` as the API server. Users can override this in the header if needed. |

---

## Setup Steps

### 1. Generate JWT Secret on Your Server

```bash
# SSH into your server
ssh root@your-server-ip

# Generate a secure JWT secret (32+ characters)
JWT_SECRET=$(openssl rand -base64 48)
echo "JWT_SECRET_KEY=$JWT_SECRET"

# Save this for the next step
export JWT_SECRET_KEY="$JWT_SECRET"
```

### 2. Install & Configure Certbot for HTTPS

If you haven't already set up SSL for `sundays.jetpans.com`:

```bash
# Install certbot
apt-get install -y certbot python3-certbot-nginx

# Generate SSL certificate
certbot certonly --standalone -d sundays.jetpans.com
```

### 3. Install Deploy Script

Copy the deploy script to your server:

```bash
# On your local machine, from the repo root:
scp deploy-sundays.sh root@your-server-ip:/

# Or manually create it on the server and paste the contents
```

Make it executable:

```bash
ssh root@your-server-ip
chmod +x /deploy-sundays.sh
```

### 4. Install Nginx Configuration

Copy the nginx configuration to your server:

```bash
# On your local machine:
scp nginx-sundays.conf root@your-server-ip:/etc/nginx/sites-enabled/

# Or manually create it:
ssh root@your-server-ip
cat > /etc/nginx/sites-enabled/sundays.conf << 'EOF'
[paste contents of nginx-sundays.conf here]
EOF
```

Test and reload nginx:

```bash
nginx -t
systemctl reload nginx
```

### 5. First Deployment (Manual)

The first time, run the deploy script manually to pull images and start containers:

```bash
ssh root@your-server-ip
export JWT_SECRET_KEY="your-generated-secret-here"
bash /deploy-sundays.sh
```

Verify containers are running:

```bash
docker ps | grep working-sundays
```

### 6. Test the Deployment

- **Frontend**: https://sundays.jetpans.com
- **API Health Check**: https://sundays.jetpans.com/api/heartbeat
- **Backend Logs**: `docker logs working-sundays-api`
- **Frontend Logs**: `docker logs working-sundays-web`

### 7. Create a User (One-time)

The first user must be created manually via API:

```bash
# Use curl to create a user (use a strong password, min 12 chars)
curl -X POST https://sundays.jetpans.com/api/auth/create-user \
  -H "Content-Type: application/json" \
  -d '{
    "username": "yourname",
    "password": "your-strong-password-12-chars-min"
  }'
```

Then log in via the web interface.

---

## Automated Deployments (GitHub Actions)

### Manual Build & Push

Trigger a build manually from GitHub:

1. Go to **Actions** → **Build backend** (or **Build frontend**)
2. Click **Run workflow**

This will build and push the image to Docker Hub.

### Automatic Deploy on Commit

Push commits to `main` branch with special prefixes:

```bash
# Deploy only backend
git commit -m "(backend) Fix API endpoint"
git push origin main

# Deploy only frontend
git commit -m "(frontend) Update UI"
git push origin main

# Deploy both
git commit -m "(all) Major update"
git push origin main
```

The GitHub Actions workflow will automatically:
1. Build the specified image(s)
2. Push to Docker Hub
3. SSH to your server
4. Run `deploy-sundays.sh` to pull and restart containers

---

## Troubleshooting

### JWT_SECRET_KEY is missing error

```bash
# Check if the variable is set
echo $JWT_SECRET_KEY

# If empty, set it
export JWT_SECRET_KEY="your-secret-here"

# Then run the deploy script
bash /deploy-sundays.sh
```

### Containers not starting

```bash
# Check logs
docker logs working-sundays-api
docker logs working-sundays-web

# Stop all containers and retry
docker stop working-sundays-api working-sundays-web
docker rm working-sundays-api working-sundays-web
bash /deploy-sundays.sh
```

### Port conflicts

If port 3001 or 5001 are already in use:

```bash
# Find what's using the port
lsof -i :5001
lsof -i :3001

# Stop the conflicting service or modify deploy-sundays.sh
```

### Nginx not proxying correctly

```bash
# Test nginx config
nginx -t

# Check nginx error logs
tail -f /var/log/nginx/sundays_error.log

# Reload nginx
systemctl reload nginx
```

---

## Docker Named Volumes

Data is stored in Docker named volumes (managed by Docker):

```bash
# List volumes
docker volume ls | grep working-sundays

# Inspect volume location
docker volume inspect working-sundays-jobs
docker volume inspect working-sundays-auth

# Docker manages the actual storage location (usually /var/lib/docker/volumes/)
# You don't need to worry about relative paths or file locations
```

---

## DNS & SSL Setup

Make sure:
1. `sundays.jetpans.com` DNS A record points to your server IP
2. SSL certificate is valid: `certbot certificates`
3. Nginx is reloading properly: `systemctl status nginx`

---

## Ports Summary

| Service | Container Port | Host Port | Purpose |
|---------|----------------|-----------|---------|
| Backend API | 5000 | 5001 | Flask API (proxied via nginx) |
| Frontend Web | 3000 | 3001 | Next.js frontend (proxied via nginx) |
| Nginx (HTTPS) | — | 443 | Public entry point (sundays.jetpans.com) |
| Nginx (HTTP) | — | 80 | HTTP redirect to HTTPS |

**Note**: xqzite uses ports 5000 and 3000 directly (or 5005/3005). Working Sundays uses 5001 and 3001 to avoid conflicts.

---

## Reference: File Locations

```
GitHub Actions Workflows:
  .github/workflows/build-backend.yml
  .github/workflows/build-frontend.yml
  .github/workflows/deploy.yml

Deployment Scripts:
  deploy-sundays.sh (on server at /)
  nginx-sundays.conf (at /etc/nginx/sites-enabled/)

Docker Images:
  jetpans/working-sundays:backend-latest
  jetpans/working-sundays:frontend-latest

Docker Volumes:
  working-sundays-jobs (job data & results)
  working-sundays-auth (user credentials)
```

---

## Next Steps

1. ✅ Set `JWT_SECRET_KEY` on your server
2. ✅ Copy deploy script to server
3. ✅ Install nginx config
4. ✅ Run deploy script manually once
5. ✅ Verify application is accessible
6. ✅ Configure GitHub secrets for automation
7. ✅ Test automated deployments with commit messages

---
