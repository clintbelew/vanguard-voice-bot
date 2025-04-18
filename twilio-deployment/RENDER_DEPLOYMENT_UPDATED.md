# Render.com Deployment Instructions

This guide will walk you through deploying your Twilio Voice Chat Bot to Render.com after uploading the code to GitHub.

## Prerequisites

- You have uploaded the provided code to your GitHub repository (https://github.com/clintbelew/vanguard-voice-bot)
- You have a Render.com account (free tier is sufficient)

## Step 1: Connect to Render.com

1. Go to [Render Dashboard](https://dashboard.render.com/) and sign in
2. Click on "New" in the top right corner
3. Select "Web Service" from the dropdown menu

## Step 2: Connect Your GitHub Repository

1. If this is your first time using Render, you'll need to connect your GitHub account
   - Click "Connect account" and follow the prompts to authorize Render
2. Once connected, select your repository: `clintbelew/vanguard-voice-bot`
3. Click "Connect"

## Step 3: Configure Your Web Service

Configure the following settings:

1. **Name**: `vanguard-chiropractic-voice-bot` (or your preferred name)
2. **Environment**: Select `Python 3`
3. **Region**: Choose the region closest to your users
4. **Branch**: `main` (or your default branch)
5. **Build Command**: `pip install -r requirements.txt`
6. **Start Command**: `gunicorn run:app`
7. **Plan**: Free (or select a paid plan if you need more resources)

## Step 4: Configure Environment Variables

1. Expand the "Advanced" section
2. Scroll down to "Environment Variables"
3. Add the following key-value pairs:

```
TWILIO_ACCOUNT_SID=AC756bd7ddebaf9c05130af548a3506722
TWILIO_AUTH_TOKEN=53a39f1b4f694a9e6b8437ce1316fe28
TWILIO_PHONE_NUMBER=+18305900834
GHL_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVC9J.eyJsb2NhdGlvbl9pZCI6IlwiIiwvb1I6MSw
GHL_LOCATION_ID=LcYKIYE6VYgMeZDuSBx9
DEBUG=False
PORT=5000
BUSINESS_NAME=Vanguard Chiropractic
BUSINESS_PHONE=+18305900834
BUSINESS_LOCATION=123 Main Street, Anytown, CA 12345
```

## Step 5: Create Web Service

1. Click "Create Web Service" at the bottom of the page
2. Render will now build and deploy your application
3. This process typically takes 5-10 minutes for the initial deployment

## Step 6: Access Your Deployed Application

1. Once the deployment is complete, Render will provide a URL for your application
   - It will look like: `https://vanguard-chiropractic-voice-bot.onrender.com`
2. Click on the URL to verify that your application is running
3. You should see a message: "Twilio Voice Bot for Vanguard Chiropractic is running!"

## Troubleshooting Deployment Issues

If you encounter any issues during deployment:

1. Check the build logs in the Render dashboard for error messages
2. Verify that all environment variables are correctly set
3. Ensure your repository contains all the necessary files
4. Check that the `requirements.txt` file includes all dependencies

## Next Steps

After successful deployment:

1. Configure your Twilio webhook to point to your new Render URL (see TWILIO_WEBHOOK_GUIDE.md)
2. Test your voice bot functionality (see TESTING_GUIDE.md)

## Additional Information

- Render automatically provides HTTPS for all web services
- Your application will automatically scale based on traffic
- Render's free tier has some limitations on usage hours and may sleep after periods of inactivity
- For production use, consider upgrading to a paid plan
