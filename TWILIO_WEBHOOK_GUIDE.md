# Twilio Webhook Integration Guide

This guide provides detailed instructions for configuring Twilio webhooks to work with your deployed voice bot application.

## Webhook Configuration

After deploying your Twilio Voice Bot to Render.com, you need to configure Twilio to send incoming calls to your application:

### Step 1: Get Your Application URL

Your application URL will be in one of these formats:
- `https://your-app-name.onrender.com` (default Render domain)
- `https://your-custom-domain.com` (if you configured a custom domain)

### Step 2: Configure Twilio Phone Number

1. Log in to your Twilio account at https://www.twilio.com/console
2. Navigate to Phone Numbers > Manage > Active Numbers
3. Click on your Twilio phone number (+18305900834)
4. Under "Voice & Fax" section, find "A Call Comes In"
5. Set the webhook URL to:
   ```
   https://your-app-name.onrender.com/voice
   ```
   (Replace with your actual application URL)
6. Ensure the HTTP method is set to **POST**
7. Click "Save" at the bottom of the page

### Step 3: Configure Fallback URL (Recommended)

To handle situations where your application might be unavailable:

1. Still on your phone number configuration page
2. Under "Voice & Fax" section, find "Call Status Changes"
3. Set the webhook URL to:
   ```
   https://your-app-name.onrender.com/missed-call
   ```
4. Ensure the HTTP method is set to **POST**
5. Click "Save" at the bottom of the page

## Testing Webhook Integration

To verify your webhook integration is working correctly:

1. Call your Twilio phone number (+18305900834)
2. You should hear the greeting message: "Thank you for calling Vanguard Chiropractic. How can I help you today?"
3. Try asking about business hours or services to test the voice recognition
4. Check your Render logs to see the incoming webhook requests

## Troubleshooting Webhook Issues

If your webhooks aren't working correctly:

1. **Check Render Logs**:
   - Log in to your Render dashboard
   - Select your web service
   - Click on "Logs" to view application logs
   - Look for any error messages when calls come in

2. **Verify Webhook URLs**:
   - Double-check that the URLs in Twilio exactly match your application URLs
   - Ensure the paths (/voice, /missed-call) are correct
   - Verify that HTTPS is being used (not HTTP)

3. **Test Webhook Connectivity**:
   - In the Twilio console, go to Phone Numbers > Manage > Active Numbers
   - Click on your phone number
   - Scroll down to the webhook configuration
   - Click the "Test" link next to your webhook URL
   - You should see a successful response from your application

4. **Check Application Status**:
   - Verify your Render application is running (status should be "Live")
   - Make sure your application hasn't run out of free hours (if using Render's free tier)

## Advanced Webhook Configuration

For more advanced use cases, you might want to configure additional webhooks:

1. **SMS Webhooks**:
   - Under "Messaging" section in your Twilio phone number configuration
   - Set "A Message Comes In" to `https://your-app-name.onrender.com/sms`
   - This allows your application to respond to text messages

2. **Status Callback URLs**:
   - These notify your application about call status changes (started, ringing, answered, completed)
   - Useful for tracking call analytics and debugging
   - Can be configured for each TwiML verb in your application code

Remember that all webhook URLs must use HTTPS, which Render provides automatically.
