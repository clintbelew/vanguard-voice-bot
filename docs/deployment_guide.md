# Twilio Voice Bot - Deployment Guide

## Prerequisites for Deployment

Before deploying the voice bot, you'll need:

1. A Twilio account with:
   - Account SID
   - Auth Token
   - A Twilio phone number with voice capabilities

2. A GoHighLevel account with:
   - API Key
   - Location ID

3. A server or hosting platform for the Flask application:
   - Heroku
   - AWS
   - Google Cloud Platform
   - DigitalOcean
   - Or any other platform that supports Python applications

## Deployment Options

### Option 1: Heroku Deployment

1. Create a Heroku account if you don't have one already
2. Install the Heroku CLI
3. Create a `Procfile` in the project root:
   ```
   web: gunicorn run:app
   ```
4. Add gunicorn to requirements.txt:
   ```
   pip install gunicorn
   pip freeze > requirements.txt
   ```
5. Initialize a git repository:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```
6. Create a Heroku app:
   ```
   heroku create your-app-name
   ```
7. Set environment variables:
   ```
   heroku config:set TWILIO_ACCOUNT_SID=your_account_sid
   heroku config:set TWILIO_AUTH_TOKEN=your_auth_token
   heroku config:set TWILIO_PHONE_NUMBER=your_phone_number
   heroku config:set GOHIGHLEVEL_API_KEY=your_api_key
   heroku config:set GOHIGHLEVEL_LOCATION_ID=your_location_id
   heroku config:set BUSINESS_NAME="Vanguard Chiropractic"
   heroku config:set BUSINESS_PHONE=your_business_phone
   heroku config:set BUSINESS_LOCATION="123 Main Street, Anytown, CA 12345"
   ```
8. Deploy the application:
   ```
   git push heroku master
   ```
9. Configure your Twilio phone number's voice webhook to point to your Heroku app:
   ```
   https://your-app-name.herokuapp.com/voice
   ```

### Option 2: AWS Elastic Beanstalk Deployment

1. Install the AWS CLI and EB CLI
2. Create a `.ebignore` file to exclude unnecessary files
3. Initialize the EB application:
   ```
   eb init -p python-3.10 your-app-name
   ```
4. Create an environment:
   ```
   eb create your-environment-name
   ```
5. Set environment variables:
   ```
   eb setenv TWILIO_ACCOUNT_SID=your_account_sid TWILIO_AUTH_TOKEN=your_auth_token ...
   ```
6. Deploy the application:
   ```
   eb deploy
   ```
7. Configure your Twilio phone number's voice webhook to point to your EB URL

### Option 3: Docker Deployment

1. Create a `Dockerfile` in the project root:
   ```
   FROM python:3.10-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   CMD ["python", "run.py"]
   ```
2. Build the Docker image:
   ```
   docker build -t twilio-voice-bot .
   ```
3. Run the container:
   ```
   docker run -p 5000:5000 --env-file .env twilio-voice-bot
   ```
4. Deploy to a container orchestration platform like Kubernetes or Docker Swarm

## Post-Deployment Configuration

1. Update your Twilio phone number's voice webhook URL to point to your deployed application
2. Test the deployed application by calling your Twilio phone number
3. Monitor the application logs for any errors
4. Set up monitoring and alerting for your deployed application

## Scaling Considerations

1. Use a production-ready WSGI server like Gunicorn
2. Consider using a load balancer if you expect high call volumes
3. Implement caching for GoHighLevel API requests
4. Set up database persistence for call logs and analytics
5. Implement proper error handling and retry mechanisms

## Security Considerations

1. Store sensitive credentials as environment variables, not in code
2. Use HTTPS for all webhook URLs
3. Implement IP restrictions for your webhook endpoints if possible
4. Regularly rotate API keys and tokens
5. Monitor for unusual activity or call patterns
