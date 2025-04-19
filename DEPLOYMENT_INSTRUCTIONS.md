# Deployment Instructions for Direct URL Fix

## Overview

This document provides step-by-step instructions for deploying the voice bot with the direct URL generation fix.

## Deployment Steps

### 1. Upload to GitHub

1. Extract the contents of this package
2. Navigate to your GitHub repository: https://github.com/clintbelew/vanguard-voice-bot
3. Click on "Add file" > "Upload files"
4. Drag and drop all the files from this package or use the file selector
5. Add a commit message like "Implement direct URL generation fix"
6. Click "Commit changes"

### 2. Deploy to Render

Render should automatically detect the changes in your GitHub repository and start a new deployment. If not:

1. Log in to your Render dashboard: https://dashboard.render.com/
2. Navigate to your voice bot service (vanguard-voice-bot)
3. Click on "Manual Deploy" > "Deploy latest commit"
4. Wait for the deployment to complete (usually takes 1-2 minutes)

### 3. Verify Environment Variables

Ensure these environment variables are set in Render:

- `ELEVENLABS_API_KEY`: Your ElevenLabs Creator plan API key
- `PUBLIC_URL_BASE`: https://vanguard-voice-bot.onrender.com
- `GHL_API_KEY`: Your GoHighLevel API key
- `GHL_LOCATION_ID`: LcYKIYE6VYgMeZDuSBx9
- `GHL_CALENDAR_ID`: 3bZr8JwFmjnXYnntbrZA

### 4. Test the Voice Bot

1. Call (830) 429-4111 to test the voice bot
2. Verify that:
   - The bot answers with Rachel's voice (no more 3 fast beeps)
   - Background office ambiance plays at 10% volume
   - Saying "Español" switches to Antonio's voice
   - Appointment booking works in both languages

## Troubleshooting

If you encounter any issues:

1. Check the Render logs for error messages
2. Verify that the PUBLIC_URL_BASE environment variable is set correctly
3. Ensure the audio_cache directory has proper permissions
4. Test the /voice endpoint directly in a browser to verify TwiML generation

## What's Changed

The main change is in the `elevenlabs_integration.py` file, where we've:

1. Removed the complex URL normalization function
2. Implemented direct URL construction using PUBLIC_URL_BASE
3. Ensured clean, valid audio URLs that Twilio can process

See the DIRECT_URL_FIX.md file for more details about the changes.
