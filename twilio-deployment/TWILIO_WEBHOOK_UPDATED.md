# Twilio Webhook Configuration Guide

This guide will walk you through configuring your Twilio webhook to connect with your deployed Render.com application.

## Prerequisites

- Your Twilio Voice Bot has been successfully deployed to Render.com
- You have your Render application URL (e.g., `https://vanguard-chiropractic-voice-bot.onrender.com`)
- You have access to your Twilio account

## Step 1: Get Your Render Application URL

1. Go to your [Render Dashboard](https://dashboard.render.com/)
2. Select your deployed web service (`vanguard-chiropractic-voice-bot`)
3. Copy the URL displayed at the top of the page
   - It should look like: `https://vanguard-chiropractic-voice-bot.onrender.com`

## Step 2: Configure Twilio Phone Number

1. Log in to your [Twilio Console](https://www.twilio.com/console)
2. Navigate to Phone Numbers > Manage > [Active Numbers](https://www.twilio.com/console/phone-numbers/incoming)
3. Click on your Twilio phone number (+18305900834)

## Step 3: Set Up Voice Webhook

1. In the "Voice & Fax" section, find "A Call Comes In"
2. Set the webhook URL to:
   ```
   https://your-render-url.onrender.com/voice
   ```
   (Replace `your-render-url` with your actual Render application URL)
3. Ensure the HTTP method is set to **POST**
4. Click "Save" at the bottom of the page

## Step 4: Set Up Missed Call Webhook (Optional but Recommended)

1. Still on your phone number configuration page
2. Under "Voice & Fax" section, find "Call Status Changes"
3. Set the webhook URL to:
   ```
   https://your-render-url.onrender.com/missed-call
   ```
   (Replace `your-render-url` with your actual Render application URL)
4. Ensure the HTTP method is set to **POST**
5. Click "Save" at the bottom of the page

## Step 5: Verify Webhook Configuration

1. Call your Twilio phone number (+18305900834)
2. You should hear the greeting message: "Thank you for calling Vanguard Chiropractic. How can I help you today?"
3. If the call connects successfully, your webhook is properly configured

## Troubleshooting Webhook Issues

If your webhook isn't working correctly:

1. **Check Application Status**:
   - Go to your Render dashboard
   - Verify your application is running (status should be "Live")
   - Check the logs for any errors

2. **Verify Webhook URLs**:
   - Double-check that the URLs in Twilio exactly match your Render application URL
   - Ensure the paths (`/voice`, `/missed-call`) are correct
   - Verify that HTTPS is being used (not HTTP)

3. **Test Webhook Connectivity**:
   - In the Twilio console, go to Phone Numbers > Manage > Active Numbers
   - Click on your phone number
   - Scroll down to the webhook configuration
   - Click the "Test" link next to your webhook URL
   - You should see a successful response from your application

4. **Check Render Logs**:
   - Go to your Render dashboard
   - Select your web service
   - Click on "Logs" to view application logs
   - Look for any error messages when calls come in

## Additional Webhook Options

For more advanced use cases, you might want to configure additional webhooks:

1. **SMS Webhooks**:
   - Under "Messaging" section in your Twilio phone number configuration
   - Set "A Message Comes In" to `https://your-render-url.onrender.com/sms`
   - This allows your application to respond to text messages

2. **Status Callback URLs**:
   - These notify your application about call status changes (started, ringing, answered, completed)
   - Useful for tracking call analytics and debugging
   - Can be configured for each TwiML verb in your application code

## Security Considerations

- All webhook URLs must use HTTPS, which Render provides automatically
- Your Twilio credentials are stored as environment variables in Render, not in your code
- Regular security updates are managed by Render's platform

If you need to update your webhook configuration in the future (e.g., if you change your Render URL), simply repeat these steps with the new URL.
