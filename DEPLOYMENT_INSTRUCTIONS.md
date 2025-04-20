# Deployment Instructions for Full Project Package

Follow these step-by-step instructions to deploy the comprehensive URL and CORS fix for your voice bot.

## 1. Update Your GitHub Repository

1. Extract the contents of the provided zip file
2. Delete the entire existing repository content in GitHub
3. Upload all files from the extracted package to your GitHub repository
   - This includes all app files, config files, and documentation
   - Make sure to maintain the same directory structure

## 2. Force a Clean Deployment in Render

1. Log into your Render dashboard: https://dashboard.render.com/
2. Navigate to your vanguard-voice-bot service
3. Click the "Manual Deploy" button in the top right
4. Select "Clear build cache & deploy" from the dropdown
5. Wait for the deployment to complete (2-3 minutes)

## 3. Verify the Fix

1. Check the /voice endpoint: https://vanguard-voice-bot.onrender.com/voice
2. Verify that the URLs in the response are properly formatted as:
   ```
   https://vanguard-voice-bot.onrender.com/audio/[hash].mp3
   ```
3. There should be no duplicate domains or malformed patterns

## 4. Test the Voice Bot

1. Call (830) 429-4111 to test the full experience
2. Verify that it answers with Rachel's voice (not the 3 fast beeps)
3. Test Spanish language support by saying "Español"
4. Confirm that Antonio's voice is used for Spanish responses

## What's Changed in This Package

1. **Fixed URL Generation**:
   - `app/elevenlabs_integration.py` now uses a hardcoded base URL
   - Added URL validation functions to catch and fix malformed URLs
   - Implemented TwiML sanitization as a final safety check

2. **Added CORS Support**:
   - Added Flask-CORS extension to the application
   - Configured CORS headers for the audio file routes
   - Added support for CORS preflight requests

3. **Updated Dependencies**:
   - Added `flask-cors==5.0.1` to requirements.txt

## Troubleshooting

If you encounter any issues:

1. Check the Render logs for any errors
2. Verify that the `flask-cors` package is properly installed
3. Confirm that all files were properly uploaded to GitHub
4. Ensure the deployment completed successfully

The comprehensive fix includes three layers of protection for URLs and proper CORS configuration, so even if one approach fails, the others should catch and fix the issue.
