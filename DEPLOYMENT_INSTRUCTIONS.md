# Deployment Instructions for Voice Bot with URL Fix

This package contains the complete voice bot application with comprehensive URL fixes implemented to resolve the issue with malformed audio URLs in Twilio responses.

## Deployment Steps

### 1. Upload to GitHub

Since you've deleted the entire folder in GitHub, you'll need to upload all these files to recreate the repository:

1. Extract this zip file to your local machine
2. Upload all files and folders to your GitHub repository (clintbelew/vanguard-voice-bot)
3. Ensure you maintain the same directory structure as in this package

### 2. Force a Clean Deployment in Render

1. Log into your Render dashboard
2. Navigate to the vanguard-voice-bot service
3. Click the "Manual Deploy" button
4. Select "Clear build cache & deploy" from the dropdown
5. Wait for the deployment to complete (this may take a few minutes)

### 3. Verify the Fix

1. Once deployment is complete, test the /voice endpoint by visiting:
   ```
   https://vanguard-voice-bot.onrender.com/voice
   ```

2. Check that the TwiML response contains properly formatted audio URLs:
   ```
   https://vanguard-voice-bot.onrender.com/audio/[hash].mp3
   ```
   (There should be no duplicate domains or malformed URLs)

3. Test the voice bot by calling (830) 429-4111
   - Verify that it answers with Rachel's voice (not the 3 fast beeps)
   - Test Spanish language support by saying "Español"
   - Confirm that background ambiance plays at ~10% volume

## What's Been Fixed

This version includes a comprehensive three-layer approach to fix the URL issues:

1. **Hardcoded Base URL** - Ensures consistent URL formatting regardless of environment variables
2. **URL Validation** - Catches and fixes malformed URLs at multiple points in the code
3. **TwiML Response Sanitization** - Final safety check on all responses before they're sent to Twilio

For more details on the implementation, see the URL_FIX_DETAILS.md file included in this package.

## Environment Variables

The following environment variables should be set in Render:

- `ELEVENLABS_API_KEY` - Your ElevenLabs API key
- `PUBLIC_URL_BASE` - Set to https://vanguard-voice-bot.onrender.com (no trailing slash)

## Need Help?

If you encounter any issues during deployment, check the logs in Render for error messages and ensure all environment variables are correctly set.
