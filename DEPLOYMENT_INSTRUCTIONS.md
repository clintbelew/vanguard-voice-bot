# Deployment Instructions for Vanguard Voice Bot

This document provides instructions for deploying the Vanguard Voice Bot application to Render.

## Prerequisites

- GitHub account
- Render account
- Twilio account with a phone number
- ElevenLabs API key
- GoHighLevel API key, location ID, and calendar ID

## Environment Variables

The following environment variables must be set in your Render deployment:

- `ELEVENLABS_API_KEY`: Your ElevenLabs API key
- `PUBLIC_URL_BASE`: The base URL of your deployed application (e.g., https://vanguard-voice-bot.onrender.com)
- `GHL_API_KEY`: Your GoHighLevel API key
- `GHL_LOCATION_ID`: Your GoHighLevel location ID
- `GHL_CALENDAR_ID`: Your GoHighLevel calendar ID
- `DEBUG`: Set to "true" for debug mode, "false" for production

## Deployment Steps

1. Push the code to a GitHub repository
2. In Render, create a new Web Service
3. Connect to your GitHub repository
4. Configure the following settings:
   - Name: vanguard-voice-bot
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app`
5. Add the environment variables listed above
6. Click "Create Web Service"

## Directory Structure

The application has the following directory structure:

```
vanguard-voice-bot/
├── app/
│   ├── __init__.py
│   ├── audio_manager.py
│   ├── elevenlabs_integration.py
│   ├── error_handler.py
│   ├── gohighlevel_integration.py
│   ├── response_builder.py
│   ├── routes.py
│   └── twilio_utils.py
├── config/
│   └── config.py
├── audio_cache/
├── logs/
├── requirements.txt
└── run.py
```

## Troubleshooting

If you encounter any issues during deployment:

1. Check the Render logs for error messages
2. Verify that all environment variables are set correctly
3. Ensure the audio_cache and logs directories exist and are writable
4. Test the ElevenLabs integration by visiting the /test endpoint

## Testing

After deployment, you can test the voice bot by:

1. Calling your Twilio phone number
2. Visiting the /test endpoint to verify ElevenLabs integration
3. Trying to book an appointment by saying "I'd like to make an appointment"
