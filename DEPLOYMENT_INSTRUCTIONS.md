# Fresh Deployment Instructions for Voice Bot with S3 Audio

## Overview

This document provides step-by-step instructions for deploying the completely independent voice bot solution that uses Amazon S3 for audio hosting. This clean implementation removes all dependencies on the problematic audio_manager.py file and ensures reliable audio playback.

## GitHub Setup

1. **Clear your existing GitHub repository**:
   - Go to your GitHub repository: https://github.com/clintbelew/vanguard-voice-bot
   - Navigate to Settings > General > Danger Zone
   - Select "Delete this repository" (or alternatively, you can create a new repository)
   - Create a new repository with the same name if you deleted it

2. **Upload the clean codebase**:
   - Extract the ZIP file to your local machine
   - Initialize a Git repository in the extracted folder:
     ```
     git init
     git add .
     git commit -m "Fresh implementation with S3 audio integration"
     ```
   - Add your GitHub repository as remote and push:
     ```
     git remote add origin https://github.com/clintbelew/vanguard-voice-bot.git
     git branch -M main
     git push -u origin main
     ```

## Render Deployment

1. **Create a new Web Service in Render**:
   - Log in to your Render dashboard: https://dashboard.render.com/
   - Click "New" and select "Web Service"
   - Connect to your GitHub repository
   - Select the repository you just pushed to

2. **Configure the Web Service**:
   - **Name**: vanguard-voice-bot (or your preferred name)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app`
   - **Instance Type**: Free (or your preferred plan)
   - **Region**: Choose the region closest to your users

3. **Set Environment Variables**:
   - Click on "Environment" in the left sidebar
   - Add the following environment variables:
     - `ELEVENLABS_API_KEY`: Your ElevenLabs API key
     - `BASE_URL`: The URL of your Render deployment (will be auto-generated)

4. **Deploy the Service**:
   - Click "Create Web Service"
   - Wait for the deployment to complete (typically 2-3 minutes)

## Twilio Configuration

1. **Update your Twilio phone number**:
   - Log in to your Twilio account
   - Navigate to Phone Numbers > Manage > Active Numbers
   - Select your phone number (830) 429-4111
   - Under "Voice & Fax" section:
     - Set "A CALL COMES IN" to "Webhook"
     - Set the webhook URL to `https://vanguard-voice-bot.onrender.com/voice`
     - Ensure the HTTP method is set to POST

2. **Test the Configuration**:
   - Call your Twilio number (830) 429-4111
   - You should hear the greeting message with background ambiance
   - Test both English and Spanish functionality

## Verification Steps

1. **Check the /test endpoint**:
   - Visit `https://vanguard-voice-bot.onrender.com/test` in your browser
   - You should see "Voice bot is operational!"

2. **Verify the /voice endpoint**:
   - Visit `https://vanguard-voice-bot.onrender.com/voice` in your browser
   - You should see TwiML with the S3 audio URL

3. **Monitor logs in Render**:
   - Go to your service in Render dashboard
   - Click on "Logs" in the left sidebar
   - Watch for any errors or issues

## Troubleshooting

If you encounter any issues:

1. **Check environment variables**:
   - Ensure ELEVENLABS_API_KEY is correctly set
   - Verify BASE_URL matches your Render deployment URL

2. **Verify S3 access**:
   - Ensure the S3 URL is accessible by visiting it directly in a browser
   - Check that the S3 bucket has proper public read permissions

3. **Review Render logs**:
   - Check for any error messages in the Render logs
   - Look for specific Python exceptions or deployment issues

## Future Enhancements

To extend this implementation:

1. **Add more S3 audio files**:
   - Pre-generate common phrases and upload to S3
   - Update the routes.py file to use these URLs

2. **Implement caching**:
   - Add a dictionary to cache frequently used phrases
   - Reduce dependency on external services

3. **Add analytics**:
   - Track call volumes and intents
   - Monitor user interactions for improvements
