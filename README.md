## Welcome to the dig4el-prod readme. 

### Server preparation
1. Install Docker if needed
```
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker
```
Confirm Docker is installed and runing
```
docker --version
sudo systemctl status docker
```
Make sure docker-compose is also available
```
sudo apt-get install docker-compose-plugin
```

2. Open ports
- Ports 8501 (Streamlit) and 5342 (Postgres) if the service is directly exposed with http
- 80 & 443 if using a reverse proxy through Nginx (as described below)
Using Ubuntu *Uncomplicated Firewall*:
Verify its status with `sudo ufw status`
Enable of not yet enabled with `sudo ufw enable`
```
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```
If you connect to this server through ssh, also add port 22 `sudo ufw allow 22/tcp`
and verify with `sudo ufw status`

3. Clone the dig4el-prod repo in a directory on your server
```
git clone https://github.com/alterfero/dig4el-prod.git dig4el
cd dig4el
```
4. Environment variables
In your project directory, create a .env file with environment variables
```
POSTGRES_USER=your_admin_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=auth_db
DATABASE_URL=postgresql://your_admin_username:your_password@db:5432/auth_db
SECRET_KEY=any_needed_secret_key
```
Never commit this file, it keeps your secrets secret. Add it to `.gitignore`

5. Nginx
Nginx is a (reverse) proxy that enables https through SSL certificates delivered by Certbot.
To install and enable Nginx

Nginx will be installed and mounted automatically via docker-compose. 
the `nginx.conf` file can be adapted if needed. 

6. Obtain the SSL certificates via Certbot and Certificate Authority let`s encrypt
Here, build and run all containers first with 
```
docker-compose up --build -d
```
Then stop the Nginx container (freeing port 80) and run Certbot in standalone mode to prove domain ownership.
```
docker compose stop nginx
docker compose run --rm certbot certonly --standalone \
    --agree-tos --no-eff-email --email sebastien.christian@doctorant.upf.pf \
    -d dig4el.upf.pf -d www.dig4el.upf.pf
```
This writes certificates into the shared volume certbot_certs:/etc/letsencrypt/
Then start Nginx again
```
docker compose up -d nginx
```
Nginx should now find the certs at /etc/letsencrypt/live/dig4el.upf.pf/

Certificates are valid for ~90 days. A cron job can be set to automate the renewal
In the repository, `renew_certs_standalone.sh` is a script designed to go through the sequence 
of stopping Nginx, renewing certificates, and re-starting Nginx.

Make this script executable on your server with `chmod +x ~/renew_certs_standalone.sh`
Then create the cron job:
Open your user crontab with `crontab -e`
Add a line to run the script once a week
```
0 2 * * 1 /home/your-username/renew_certs_standalone.sh >> /home/your-username/renew_cert_standalone.log 2>&1
```
Replacing `/home/your-username` with the actual path to where you placed the script.
`0 2 * * 1` will trigger the script every Monday at 2am local time.
`>> /home/your-username/renew_cert_standalone.log 2>&1` appends output (including errors) to a log file for troubleshooting.

You can check the log with 
`cat /home/your-username/renew_cert_standalone.log`

## Check logs
```
docker compose logs -f
```