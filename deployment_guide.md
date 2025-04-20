# Security Leads Automation - Deployment Guide

This guide provides instructions for deploying the Security Leads Automation web application permanently.

## Deployment Options

There are several ways to deploy the application:

1. **Docker Deployment** - Using Docker and Docker Compose (recommended)
2. **Cloud Platform Deployment** - Using services like Heroku, AWS, or Google Cloud
3. **Traditional Server Deployment** - Using a VPS or dedicated server

## Docker Deployment (Recommended)

### Prerequisites
- Docker and Docker Compose installed on your server
- Git (optional, for cloning the repository)

### Deployment Steps

1. Clone or download the repository to your server:
   ```
   git clone <repository-url>
   cd security_leads_automation
   ```

2. Build and start the Docker containers:
   ```
   docker-compose up -d
   ```

3. Access the application at `http://your-server-ip:8080`

### Configuration

You can modify the `docker-compose.yml` file to change:
- Port mapping (default is 8080)
- Volume mounts for persistent data
- Environment variables

If you want to use PostgreSQL instead of SQLite, uncomment the database section in the `docker-compose.yml` file.

## Cloud Platform Deployment

### Heroku Deployment

1. Create a Heroku account and install the Heroku CLI
2. Initialize a Git repository if not already done:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```

3. Create a Heroku app:
   ```
   heroku create security-leads-automation
   ```

4. Add a Procfile (already included in the repository):
   ```
   web: gunicorn web_app:app
   ```

5. Push to Heroku:
   ```
   git push heroku main
   ```

6. Set up a database add-on:
   ```
   heroku addons:create heroku-postgresql:hobby-dev
   ```

7. Configure environment variables:
   ```
   heroku config:set FLASK_APP=web_app.py
   heroku config:set FLASK_ENV=production
   ```

### AWS Elastic Beanstalk Deployment

1. Install the AWS CLI and EB CLI
2. Initialize the EB application:
   ```
   eb init -p python-3.10 security-leads-automation
   ```

3. Create an environment:
   ```
   eb create security-leads-production
   ```

4. Deploy the application:
   ```
   eb deploy
   ```

## Traditional Server Deployment

### Prerequisites
- Python 3.10 or higher
- Nginx or Apache web server
- Supervisor or systemd for process management

### Deployment Steps

1. Clone or download the repository to your server
2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set up Gunicorn with Supervisor:
   Create a file `/etc/supervisor/conf.d/security_leads.conf`:
   ```
   [program:security_leads]
   directory=/path/to/security_leads_automation
   command=/path/to/security_leads_automation/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8080 web_app:app
   autostart=true
   autorestart=true
   stderr_logfile=/path/to/security_leads_automation/logs/gunicorn.err.log
   stdout_logfile=/path/to/security_leads_automation/logs/gunicorn.out.log
   ```

4. Set up Nginx as a reverse proxy:
   Create a file `/etc/nginx/sites-available/security_leads`:
   ```
   server {
       listen 80;
       server_name your_domain.com;

       location / {
           proxy_pass http://127.0.0.1:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

5. Enable the site and restart Nginx:
   ```
   ln -s /etc/nginx/sites-available/security_leads /etc/nginx/sites-enabled/
   systemctl restart nginx
   ```

## SSL Configuration

For production deployments, it's recommended to set up SSL:

1. Using Let's Encrypt with Certbot:
   ```
   certbot --nginx -d your_domain.com
   ```

2. Or manually configure SSL in your Nginx configuration.

## Maintenance

- Regularly back up the data directory
- Monitor logs for errors
- Set up automated updates for security patches

## Troubleshooting

- Check the application logs in the `logs` directory
- Verify database connectivity
- Ensure proper permissions for data and log directories
