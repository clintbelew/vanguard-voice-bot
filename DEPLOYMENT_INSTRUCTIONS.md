# Deployment Instructions

Follow these step-by-step instructions to deploy the comprehensive URL fix for your voice bot.

## 1. Update Your GitHub Repository

1. Extract the contents of the provided zip file
2. Upload the following files to your GitHub repository:
   - `app/elevenlabs_integration.py` - Replace with the fixed version
   - `app/response_builder.py` - Replace with the fixed version
   - `app/routes.py` - Replace with the fixed version
   - `requirements.txt` - Ensure it includes `flask-cors==5.0.1`

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

## Troubleshooting

If you encounter any issues:

1. Check the Render logs for any errors
2. Verify that the `flask-cors` package is properly installed
3. Confirm that all three fixed files were properly uploaded to GitHub
4. Ensure the deployment completed successfully

The comprehensive fix includes three layers of protection, so even if one approach fails, the others should catch and fix the issue.
