# Railway Deployment Troubleshooting Guide

This guide provides steps to troubleshoot and fix deployment issues with the Vanguard Voice Bot on Railway.

## Common Railway Deployment Issues

1. **404 "The train has not arrived at the station" Error**
   - This indicates that the application is not properly deployed or the domain hasn't been provisioned correctly
   - The application might have failed to build or start

2. **No Logs Appearing**
   - Logs not appearing usually means the application isn't running or is crashing before it can log anything
   - Could be due to environment variable issues, build failures, or runtime errors

## Troubleshooting Steps

### 1. Check Railway Build Logs

First, check the build logs in the Railway dashboard:
- Go to your project in Railway
- Click on the "Deployments" tab
- Look for any failed builds or deployments
- Check the build logs for errors

### 2. Verify Environment Variables

Make sure all required environment variables are set:
- ELEVENLABS_API_KEY
- ELEVENLABS_VOICE_ID
- GHL_API_KEY
- GHL_LOCATION_ID
- GHL_CALENDAR_ID
- OPENAI_API_KEY
- FLASK_SECRET_KEY
- PORT (should be set automatically by Railway)

### 3. Check for Port Configuration Issues

Railway automatically assigns a port to your application. Make sure your app is listening on the correct port:
- The app should use `os.getenv('PORT')` or `os.getenv('RAILWAY_PORT')` to get the port
- The app should bind to `0.0.0.0` to listen on all interfaces

### 4. Verify Project Structure

Make sure your project has the correct structure for Railway to detect and build it:
- `app.py` - Main application file
- `requirements.txt` - Dependencies
- `runtime.txt` - Python version (should be `python-3.10`)
- `Procfile` - Process type definition (should be `web: gunicorn app:app`)

### 5. Restart the Deployment

Sometimes simply restarting the deployment can fix issues:
- Go to your project in Railway
- Click on the "Deployments" tab
- Find your latest deployment
- Click the three dots menu and select "Restart"

### 6. Check Domain Settings

If the application is running but you're still seeing 404 errors:
- Go to your project in Railway
- Click on the "Settings" tab
- Check the "Domains" section
- Make sure your domain is properly configured and provisioned

## Fixes Implemented in This Update

1. **Enhanced Logging**
   - Added print statements at the beginning of each route handler
   - These will appear in Railway logs even if the structured logging fails
   - Added detailed request logging (form data, headers, values)

2. **Improved Error Handling**
   - Added comprehensive try/except blocks
   - Created fallback responses that always return valid TwiML
   - Added a catch-all fallback route for any mistyped Twilio webhook URLs

3. **Immediate Response**
   - Added a simple Say element at the start of the response for immediate feedback
   - Enhanced the TwiML structure to ensure Twilio always gets a valid response

4. **Debugging Helpers**
   - Added detailed logging of all incoming request data
   - Added logging of the generated TwiML before returning it

## Next Steps After Deployment

1. **Verify Application is Running**
   - Visit the root URL (https://vanguard-voice-bot-production.up.railway.app/)
   - You should see "Vanguard Voice Bot for Vanguard Chiropractic is running!"

2. **Check Health Endpoint**
   - Visit https://vanguard-voice-bot-production.up.railway.app/health
   - You should receive a JSON response with status "healthy"

3. **Test Twilio Webhook**
   - Make a POST request to https://vanguard-voice-bot-production.up.railway.app/twilio-voice
   - You should receive a valid TwiML response

4. **Check Railway Logs**
   - After making requests, check the logs in Railway dashboard
   - You should see log entries for each request

If you continue to experience issues after implementing these fixes, please provide the specific error messages or logs from Railway to help diagnose the problem further.
