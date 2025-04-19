# Bilingual Voice Bot Deployment Instructions

## Overview
This package contains the updated voice bot with full bilingual support (English and Spanish). The bot can now:
- Automatically detect when callers speak Spanish
- Allow language switching by saying "Español" or "English" at any point
- Provide complete conversation flows in both languages
- Use Rachel for English and Antonio for Spanish voices

## Deployment Steps

1. **Upload to GitHub**
   - Upload all files in this package to your GitHub repository
   - Ensure all files maintain their directory structure

2. **Update Render Environment Variables**
   - Ensure your Render deployment has the following environment variables:
     - `ELEVENLABS_API_KEY`: Your ElevenLabs Creator plan API key
     - `PUBLIC_URL_BASE`: Your Render application URL (e.g., https://vanguard-voice-bot.onrender.com)
     - `GHL_API_KEY`: Your GoHighLevel API key
     - `GHL_LOCATION_ID`: Your GoHighLevel location ID
     - `GHL_CALENDAR_ID`: Your GoHighLevel calendar ID
     - `DEBUG`: Set to "true" or "false" as needed

3. **Deploy to Render**
   - Trigger a manual deployment in Render or push to GitHub to trigger automatic deployment
   - Wait for the deployment to complete

4. **Verify Twilio Configuration**
   - Ensure your Twilio phone number webhook is set to:
     - URL: https://vanguard-voice-bot.onrender.com/voice
     - Method: POST

5. **Test the Voice Bot**
   - Call your Twilio phone number
   - Test both English and Spanish functionality
   - Verify that language switching works correctly

## Bilingual Features

### English Support
- Uses Rachel voice from ElevenLabs
- Handles all existing appointment booking flows
- Responds to common questions about insurance, payments, etc.

### Spanish Support
- Uses Antonio voice from ElevenLabs
- Complete appointment booking flow in Spanish
- Spanish responses for common questions
- Spanish error handling and fallbacks

### Language Detection
- Automatically detects Spanish phrases in caller speech
- Allows explicit language switching with "Español" or "English" commands
- Seamless transitions between languages

## Troubleshooting
- If voices aren't working, verify your ElevenLabs API key is correct and your account is on the Creator plan
- If language detection isn't working, check the logs for speech recognition results
- If appointment booking isn't working, verify your GoHighLevel credentials

For any issues, check the application logs in Render for detailed error messages.
