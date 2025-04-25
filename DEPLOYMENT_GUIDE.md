# Vanguard Voice Bot Migration - Deployment Guide

## Overview

This document provides detailed instructions for deploying the migrated Vanguard Voice Bot to Railway. The migration has successfully combined the Twilio voice bot functionality from the original Vanguard Voice Bot with OpenAI for intelligent conversation handling, ElevenLabs for voice generation, and GoHighLevel for appointment booking.

## Migration Summary

The following changes have been implemented:

1. **Simplified Structure**: Consolidated the modular structure into a single app.py file while maintaining all functionality
2. **OpenAI Integration**: Added intelligent conversation handling using the o4-mini model
3. **Enhanced Endpoints**:
   - `/health`: Simple health check endpoint
   - `/voice`: OpenAI-powered text processing with ElevenLabs voice generation
   - `/book`: GoHighLevel appointment booking with timezone handling
   - Twilio webhook endpoints for voice interaction
4. **Voice Generation**: Standardized on ElevenLabs for voice generation
5. **Railway Configuration**: Added necessary configuration files for Railway deployment
6. **Environment Variables**: Standardized all environment variables in a single .env file

## Deployment Instructions

### Prerequisites

- GitHub account
- Railway account
- OpenAI API key (for o4-mini model)
- ElevenLabs API key and voice ID
- GoHighLevel API key, location ID, and calendar ID
- Twilio account with a phone number

### Step 1: Upload to GitHub

1. Create a new repository on GitHub (or use an existing one)
2. Upload the files from the provided ZIP package to the repository
3. Ensure all files are at the root level of the repository

### Step 2: Deploy to Railway

1. Log in to your Railway account at https://railway.app
2. Create a new project
3. Select "Deploy from GitHub repo" and choose your repository
4. Railway will automatically detect the Python project and start the deployment

### Step 3: Configure Environment Variables

1. In your Railway project, go to the "Variables" tab
2. Add the following environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `OPENAI_MODEL`: OpenAI model to use (defaults to o4-mini if not set)
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key
   - `ELEVENLABS_VOICE_ID`: Your ElevenLabs voice ID (Jessica)
   - `GHL_API_KEY`: Your GoHighLevel API key
   - `GHL_LOCATION_ID`: Your GoHighLevel location ID
   - `GHL_CALENDAR_ID`: Your GoHighLevel calendar ID
   - `BUSINESS_NAME`: Your business name
   - `BUSINESS_LOCATION`: Your business address
   - `BUSINESS_PHONE`: Your business phone number
   - `FLASK_SECRET_KEY`: Secret key for Flask sessions

### Step 4: Enable Public Access

1. In your Railway project, go to the "Settings" tab
2. Under "Networking", toggle "Public Domain" to ON
3. Note the generated domain URL (e.g., https://vanguard-voice-bot-production.up.railway.app)

### Step 5: Configure Twilio

1. Log in to your Twilio account
2. Navigate to Phone Numbers > Manage > Active Numbers
3. Select your phone number
4. Under "Voice & Fax", set the following:
   - When a call comes in: Webhook
   - URL: `https://your-railway-app.up.railway.app/twilio/voice`
   - HTTP Method: POST
5. Save your changes

## OpenAI Integration

The voice bot uses OpenAI's o4-mini model to provide intelligent conversation handling:

- Processes user speech input to understand intent
- Maintains conversation context throughout the call
- Collects caller information (name, phone, email, preferred time)
- Automatically triggers appointment booking when all information is collected

The OpenAI integration works by default when the environment variables are present, with no additional configuration needed.

## Testing the Deployment

### Testing the Health Endpoint

```bash
curl https://your-railway-app.up.railway.app/health
```

Expected response:
```json
{"service":"Vanguard Voice Bot Backend","status":"healthy"}
```

### Testing the Voice Endpoint

```bash
curl -X POST https://your-railway-app.up.railway.app/voice \
  -H "Content-Type: application/json" \
  -d '{
    "text":"Hello, I'd like to schedule an appointment.",
    "conversation_id":"test-123"
  }'
```

Expected response: Audio file (MP3) with OpenAI-generated content

### Testing the Book Endpoint

```bash
curl -X POST https://your-railway-app.up.railway.app/book \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "phone": "1234567890",
    "email": "test@example.com",
    "selectedSlot": "2025-04-25T10:00:00"
  }'
```

Expected response:
```json
{
  "success": true,
  "message": "Appointment booked successfully",
  "scheduled_time": "2025-04-25T10:00:00-05:00",
  "appointment": { ... }
}
```

### Testing the Twilio Integration

1. Call your Twilio phone number
2. Verify that the voice bot answers and responds to your speech
3. Test the appointment booking flow by asking to schedule an appointment
4. Check the Railway logs for any errors or issues

## Troubleshooting

### Common Issues

1. **Deployment Fails**:
   - Check that all required files are in the repository
   - Verify that the Procfile and runtime.txt are correctly formatted
   - Check the Railway logs for specific error messages

2. **OpenAI Integration Issues**:
   - Verify your OpenAI API key is correct
   - Check that the o4-mini model is available for your account
   - Check the Railway logs for API error responses

3. **Voice Generation Fails**:
   - Verify your ElevenLabs API key and voice ID
   - Check the Railway logs for API error responses
   - Test the /voice endpoint directly to isolate the issue

4. **Appointment Booking Fails**:
   - Verify your GoHighLevel API key, location ID, and calendar ID
   - Check the format of the selectedSlot parameter
   - Check the Railway logs for API error responses

5. **Twilio Integration Issues**:
   - Verify the webhook URL in your Twilio configuration
   - Check that the /twilio/voice endpoint is accessible
   - Test the endpoint directly with a POST request

## Maintenance

### Monitoring

1. Regularly check the Railway logs for errors or warnings
2. Monitor your OpenAI API usage to avoid hitting rate limits
3. Monitor your ElevenLabs API usage to avoid hitting limits
4. Check your GoHighLevel calendar for successful bookings

### Updates

1. Make code changes in your GitHub repository
2. Railway will automatically detect changes and redeploy
3. Test all functionality after each update

## Conclusion

The Vanguard Voice Bot has been successfully migrated from Render to Railway, with enhanced functionality and improved architecture. The bot now uses OpenAI for intelligent conversation handling, ElevenLabs for voice generation, and includes robust appointment booking with GoHighLevel integration.

For any questions or issues, refer to the README.md file or contact the development team.
