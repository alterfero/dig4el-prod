#!/usr/bin/env bash

# renew_certs_standalone.sh
# Automates Let’s Encrypt certificate renewal in standalone mode for a Docker-based Nginx setup.

set -e  # Exit immediately if a command exits with a non-zero status

echo "=== Starting Let's Encrypt renewal script (standalone mode) ==="
echo "Stopping Nginx container..."
docker compose stop nginx

echo "Attempting to renew certificates..."
docker compose run --rm certbot renew

echo "Restarting Nginx container..."
docker compose up -d nginx

echo "=== Let's Encrypt renewal script completed ==="