# Twilio Voice Bot - Render Deployment Guide

This guide will walk you through deploying your Twilio Voice Chat Bot to Render.com.

## Prerequisites

1. A GitHub, GitLab, or Bitbucket account
2. A Render.com account (free tier is sufficient)
3. Your Twilio and GoHighLevel credentials (already configured in the files)

## Deployment Steps

### Step 1: Create a New Repository

1. Create a new repository on GitHub, GitLab, or Bitbucket
2. Upload all the files from this package to your repository
   - Make sure to exclude the `.env` file (it's in the .gitignore)
   - All credentials will be added as environment variables in Render

### Step 2: Deploy to Render

1. Log in to your Render account at https://dashboard.render.com/
2. Click on "New" and select "Web Service"
3. Connect your GitHub/GitLab/Bitbucket account and select your repository
4. Configure the following settings:
   - **Name**: `vanguard-chiropractic-voice-bot` (or your preferred name)
   - **Environment**: `Python 3`
   - **Region**: Choose the region closest to your users
   - **Branch**: `main` (or your default branch)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`

5. Under "Advanced" settings, add the following environment variables:
   - `TWILIO_ACCOUNT_SID`: AC756bd7ddebaf9c05130af548a3506722
   - `TWILIO_AUTH_TOKEN`: 53a39f1b4f694a9e6b8437ce1316fe28
   - `TWILIO_PHONE_NUMBER`: +18305900834
   - `GHL_API_KEY`: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVC9J.eyJsb2NhdGlvbl9pZCI6IlwiIiwvb1I6MSw
   - `GHL_LOCATION_ID`: LcYKIYE6VYgMeZDuSBx9
   - `DEBUG`: False
   - `PORT`: 5000
   - `BUSINESS_NAME`: Vanguard Chiropractic
   - `BUSINESS_PHONE`: +18305900834
   - `BUSINESS_LOCATION`: 123 Main Street, Anytown, CA 12345

6. Click "Create Web Service"

Render will now build and deploy your application. This process typically takes 5-10 minutes for the initial deployment.

### Step 3: Configure Twilio Webhook

Once your application is deployed:

1. Note your Render application URL (e.g., `https://vanguard-chiropractic-voice-bot.onrender.com`)
2. Log in to your Twilio account at https://www.twilio.com/console
3. Navigate to Phone Numbers > Manage > Active Numbers
4. Click on your Twilio phone number
5. Under "Voice & Fax" > "A Call Comes In", set the webhook URL to:
   ```
   https://your-render-url.onrender.com/voice
   ```
6. Set the HTTP method to POST
7. Save your changes

### Step 4: Testing

To test your deployed voice bot:

1. Call your Twilio phone number
2. Verify that you hear the greeting message
3. Test the FAQ responses by asking about business hours, services, etc.
4. Test the appointment booking flow
5. Verify that SMS follow-ups are sent
6. Check that appointments sync with GoHighLevel

## Troubleshooting

If you encounter any issues:

1. Check the Render logs for error messages
2. Verify that all environment variables are correctly set
3. Ensure your Twilio webhook URL is correctly configured
4. Check that your Twilio phone number has voice capabilities enabled

## Additional Resources

- Render Documentation: https://render.com/docs
- Twilio Documentation: https://www.twilio.com/docs
- GoHighLevel API Documentation: https://developers.gohighlevel.com/

If you need further assistance, please don't hesitate to reach out.
