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
The command `sudo docker compose version` should return a version 2.x.x
Otherwise, if version is 1.x.x or there is an error message telling you that `compose` is not 
a docker command, installl the v2 plugin (quick online search for 'install and enable docker-compose v2 plugin'
will point you to the process.)

2. Open ports
- Ports 8501 (Streamlit) and 5342 (Postgres) if the service is directly exposed with http
- 80 & 443 if using a reverse proxy through Nginx (as described below)
Using Ubuntu *Uncomplicated Firewall*:
Verify its status with `sudo ufw status`
Enable of not yet enabled with `sudo ufw enable`
```
sudo ufw allow http
sudo ufw allow https
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
CQ_DATABASE_URL=postgresql://your_admin_username:your_password@cq_db:5433/cq_db
TRANSCRIPTION_DATABASE_URL=postgresql://your_admin_username:your_password@transcription_db:5434/transcription_db
LCQ_DATABASE_URL=postgresql://your_admin_username:your_password@lcq_db:5435/lcq_db
SECRET_KEY=any_needed_secret_key
```
Never commit this file, it keeps your secrets secret. Add it to `.gitignore`

5. Nginx
Nginx is a (reverse) proxy that enables https through SSL certificates delivered by Certbot.
To install and enable Nginx

Nginx will be installed and mounted automatically via docker-compose. 
the `nginx.conf` file can be adapted if needed. 

6. Here, build and run all containers first with 
```
sudo docker compose build
sudo docker compose up -d
```

7. Obtain the SSL certificates via Certbot and Certificate Authority let`s encrypt
Stop the Nginx container (freeing port 80) and run Certbot in standalone mode, providing it access
to port 80 to prove domain ownership.

```
sudo docker compose down

sudo docker run --rm -it -p 80:80 \
   -v /etc/letsencrypt:/etc/letsencrypt \
   certbot/certbot:latest certonly --standalone \
   --agree-tos --no-eff-email \
   --email sebastien.christian@doctorant.upf.pf \
   -d dig4el.upf.pf
```
This writes certificates into the shared volume: 
ssl_certificate /etc/letsencrypt/live/dig4el.upf.pf/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/dig4el.upf.pf/privkey.pem;

Then start the containers again
```
sudo docker compose up -d
```
You should see
```
[+] Running 5/5
 ✔ Network dig4el_default     Created                                                                                                                                             0.1s 
 ✔ Container authdb           Started                                                                                                                                             0.4s 
 ✔ Container dig4el_logic_ui  Started                                                                                                                                             0.5s 
 ✔ Container nginx_proxy      Started                                                                                                                                             0.8s 
 ✔ Container certbot          Started 
```

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

## New Features

### Dashboard Page
Once a user is logged in, they will be directed to a new page called 'dashboard'. On this page, users can see all the CQ from cq_db and transcriptions from transcription_db they have access to. This includes the CQ and documents they are the authors of, and the CQ and transcriptions uploaded by others with a "read-only by other registered users" authorization.

### Upload Section
A separate section on the 'dashboard' page invites the user to upload a CQ or a transcription. When uploading a CQ, the user can choose a sharing authorization among: "No sharing", "Can be read by other registered users", "Can be read by unregistered guests".

### Guest Login
The login page now includes a "Login as Guest" button. Guests don't need to register (no username, email, or password needed). They can use the software but are restricted in their actions (they can't upload anything, or read content reserved to registered users).

### Legacy CQ Uploads
Logged in users can also upload and download legacy CQ documents (Word, Excel, PDF...). These files are stored in a dedicated database.
