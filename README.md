## Welcome to the dig4el-prod readme. 

### Server preparation
1. Install Docker if needed
'''
sudo apt-get update
sudo apt-get install docker.io
sudo systemctl start docker
sudo systemctl enable docker
'''
Confirm Docker is installed and runing
'''
docker --version
sudo systemctl status docker
'''
Make sure docker-compose is also available
'''
sudo apt-get install docker-compose-plugin
'''
2. Open ports
- Ports 8501 (Streamlit) and 5342 (Postgres) if the service is directly exposed with http
- 80 & 443 if using a reverse proxy through Nginx (as described below)
Using Ubuntu *Uncomplicated Firewall*:
Verify its status with 'sudo ufw status'
Enable of not yet enabled with 'sudo ufw enable'
'''
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
'''
3. Clone the dig4el-prod repo in a directory on your server
'''
git clone https://github.com/alterfero/dig4el-prod.git myapp
cd myapp
'''
4. Environment variables
In your project directory, create a .env file with environment variables
'''
POSTGRES_USER=your_admin_username
POSTGRES_PASSWORD=your_password
POSTGRES_DB=auth_db
DATABASE_URL=postgresql://your_admin_username:your_password@db:5432/auth_db
SECRET_KEY=any_needed_secret_key
'''
Don't commit this file. Add it to .gitignore. 
5. Nginx
Nginx is a (reverse) proxy that enables https through SSL certificates delivered by Certbot.
Edit the exisiting nginx.conf file or move the one in the repository root folder to the right location '/etc/nginx/nginx.conf'
6. Obtain the SSL certificates via Certbot and let's encrypt
Here, stop the Nginx container (freeing port 80) and run Certbot in standalone mode to prove domain ownership.
'''
docker compose stop nginx
docker compose run --rm certbot certonly --standalone \
    --agree-tos --no-eff-email --email sebastien.christian@doctorant.upf.pf \
    -d yourdomain.com -d www.dig4el.upf.pf
'''
This writes certificates into the shared volume certbot_certs:/etc/letsencrypt/
Then start Nginx again
'''
docker compose up -d nginx
Nginx should now find the certs at /etc/letsencrypt/live/dig4el.upf.pf/.
'''
Certificates are valid for ~90 days. A cron job can be set to automate the renewal
For example:
'''

'''

## Build and start containers
1. Build
'''docker-compose up --build -d'''
2. Generate certs

## Check logs
'''
docker compose logs -f
'''