# Agen911 Deployment Guide

This guide provides instructions for deploying the Agen911 application to a production server.

## Prerequisites

Before deploying the application, ensure your server meets the following requirements:

### System Dependencies

The application requires the following system dependencies, especially for the code execution functionality:

```bash
# Update package lists
sudo apt-get update

# Install Xvfb for virtual display
sudo apt-get install xvfb

# Install ImageMagick for screenshot capture
sudo apt-get install imagemagick

# Install additional dependencies for GUI applications
sudo apt-get install python3-tk
sudo apt-get install libgl1-mesa-glx
```

### Python Dependencies

Install the required Python packages:

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Ensure these specific packages are installed for code execution
pip install pygame pyvirtualdisplay xvfbwrapper opencv-python flask-socketio
```

## Environment Setup

1. Create a `.env` file in the project root with the following variables:

```
FLASK_APP=run.py
FLASK_ENV=production
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
SERPER_API_KEY=your_serper_api_key
GOOGLE_API_KEY=your_google_api_key
UNSPLASH_API_KEY=your_unsplash_api_key
GOOGLE_CSE_ID=your_google_cse_id
```

2. Replace the placeholder values with your actual API keys.

## Server Configuration

### Using Gunicorn (Recommended)

For production deployment, we recommend using Gunicorn:

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5001 --workers 4 run:app
```

### Using Nginx as a Reverse Proxy

For better performance and security, use Nginx as a reverse proxy:

1. Install Nginx:

```bash
sudo apt-get install nginx
```

2. Create a new Nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/agen911
```

3. Add the following configuration:

```
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_pass http://localhost:5001/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

4. Enable the configuration:

```bash
sudo ln -s /etc/nginx/sites-available/agen911 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Special Considerations for Code Execution

The code execution functionality requires special attention:

1. **Security**: The code execution runs in a sandboxed environment, but additional security measures may be needed in a production environment.

2. **Resource Limits**: Set up resource limits to prevent abuse:
   - Limit CPU usage
   - Limit memory usage
   - Set execution timeouts

3. **Virtual Display**: Ensure Xvfb is running correctly:

```bash
# Test Xvfb
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99
```

4. **Cleanup**: Set up a cron job to clean up temporary files:

```bash
# Add to crontab
0 * * * * find /tmp -name "code_executor_*" -type d -mmin +60 -exec rm -rf {} \; 2>/dev/null
```

## Monitoring and Maintenance

1. Set up logging:

```bash
# Install logging tools
pip install sentry-sdk

# Add to your app configuration
import sentry_sdk
sentry_sdk.init("your_sentry_dsn")
```

2. Set up monitoring:

```bash
# Install monitoring tools
pip install prometheus_client
```

## Troubleshooting

If you encounter issues with the code execution functionality:

1. Check if Xvfb is installed and running:

```bash
which Xvfb
ps aux | grep Xvfb
```

2. Check if the virtual display is working:

```bash
DISPLAY=:99 xdpyinfo
```

3. Check the application logs:

```bash
tail -f /var/log/agen911/app.log
```

## Contact

For support or questions, please contact:
- Email: your_email@example.com
- GitHub: https://github.com/Udostan/Agent9
