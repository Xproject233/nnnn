# Web Deployment Guide for Security Leads Automation

This guide provides comprehensive instructions for deploying the Security Leads Automation system as a web application, making it accessible from anywhere through a browser.

## Overview

The Security Leads Automation system has been transformed from a command-line tool into a full-featured web application with:

- Interactive dashboard with lead statistics and charts
- Comprehensive lead management interface
- Data source configuration and management
- System settings and scheduling controls
- API endpoints for programmatic access

## Deployment Options

There are three main ways to deploy the web application:

### 1. Quick Development Deployment

For testing and development purposes, use the included `deploy.sh` script:

```bash
./deploy.sh
```

This will:
- Build and start the Docker containers
- Map port 8080 to the web application
- Mount data and logs directories for persistence
- Display the URL where you can access the application

### 2. Production Deployment

For permanent production deployment, use the `deploy-production.sh` script:

```bash
./deploy-production.sh
```

This will:
- Build and start the Docker containers using production settings
- Map port 80 (standard HTTP port) to the web application
- Mount data and logs directories for persistence
- Run validation tests to ensure everything is working
- Display the URL where you can access the application

### 3. Manual Deployment

For custom deployment scenarios, you can:

1. Use Docker Compose directly:
   ```bash
   docker-compose -f production-compose.yml up -d
   ```

2. Deploy to a cloud platform using the instructions in `docs/deployment_guide.md`

3. Set up a traditional server deployment with Nginx/Apache as detailed in `docs/deployment_guide.md`

## Validation

After deployment, you can validate that the web application is working correctly:

```bash
./validate_deployment.sh http://your-server-ip
```

This will test all endpoints and API functionality to ensure everything is working as expected.

## Directory Structure

- `Dockerfile`: Container definition for the web application
- `docker-compose.yml`: Development deployment configuration
- `production-compose.yml`: Production deployment configuration
- `requirements.txt`: Python dependencies
- `web_app.py`: Flask web application entry point
- `templates/`: HTML templates for the web interface
- `static/`: CSS, JavaScript, and other static assets
- `scripts/`: Core functionality and scrapers
- `data/`: Database and exported leads (persistent)
- `logs/`: Application logs (persistent)
- `tests/`: Test scripts including deployment validation
- `docs/`: Documentation including detailed deployment guide

## Security Considerations

For a production deployment, consider:

1. Setting up HTTPS with Let's Encrypt or another SSL provider
2. Implementing user authentication
3. Configuring a firewall to restrict access
4. Setting up regular backups of the data directory

## Troubleshooting

If you encounter issues with the deployment:

1. Check the logs in the `logs` directory
2. Run the validation script to identify specific problems
3. Verify that all ports are correctly mapped and accessible
4. Ensure Docker has sufficient resources (CPU, memory)

## Maintenance

To update the application:

1. Pull the latest code
2. Run the deployment script again
3. The Docker containers will be rebuilt with the new code

To back up your data:

1. Simply copy the `data` directory to a secure location
2. For database backups, use the export functionality in the web interface

## Conclusion

The Security Leads Automation system is now ready for permanent deployment as a web application. By following this guide, you can make the system accessible from anywhere, allowing you to manage security service leads through an intuitive web interface rather than command-line tools.

For any additional questions or custom deployment scenarios, refer to the detailed documentation in the `docs` directory.
