# Twilio Voice Bot - Testing Guide

## Prerequisites for Testing

Before testing the voice bot, you'll need:

1. A Twilio account with:
   - Account SID
   - Auth Token
   - A Twilio phone number with voice capabilities

2. A GoHighLevel account with:
   - API Key
   - Location ID

3. A way to expose your local server to the internet (for Twilio webhooks)
   - We recommend using ngrok for local testing

## Setup for Testing

1. Create a `.env` file in the project root by copying the `.env.example` file:
   ```
   cp .env.example .env
   ```

2. Fill in your actual credentials in the `.env` file:
   ```
   TWILIO_ACCOUNT_SID=your_actual_account_sid
   TWILIO_AUTH_TOKEN=your_actual_auth_token
   TWILIO_PHONE_NUMBER=your_actual_twilio_phone_number
   GOHIGHLEVEL_API_KEY=your_actual_api_key
   GOHIGHLEVEL_LOCATION_ID=your_actual_location_id
   ```

3. Install ngrok if you don't have it already:
   ```
   npm install -g ngrok
   ```

4. Start the Flask application:
   ```
   python run.py
   ```

5. In a separate terminal, start ngrok to expose your local server:
   ```
   ngrok http 5000
   ```

6. Configure your Twilio phone number's voice webhook:
   - Log in to your Twilio account
   - Go to Phone Numbers > Manage > Active Numbers
   - Click on your Twilio phone number
   - Under "Voice & Fax" > "A Call Comes In", set the webhook URL to:
     ```
     https://your-ngrok-url.ngrok.io/voice
     ```
   - Set the HTTP method to POST
   - Save your changes

## Testing Scenarios

### 1. Test Voice Greeting

- Call your Twilio phone number
- Verify that you hear the greeting message: "Thank you for calling Vanguard Chiropractic. How can I help you today?"
- Verify that the bot is listening for your response

### 2. Test FAQ Responses

- Call your Twilio phone number
- After the greeting, ask about business hours
  - Expected response: Information about business hours
- Call again and ask about services
  - Expected response: Information about available services
- Call again and ask about insurance
  - Expected response: Information about accepted insurance plans
- Call again and ask about location
  - Expected response: Address and parking information

### 3. Test Appointment Booking

- Call your Twilio phone number
- After the greeting, say "I'd like to schedule an appointment"
- Follow the prompts to book an appointment as a new patient
- Verify that you receive an SMS confirmation
- Check GoHighLevel to confirm the contact and appointment were created

### 4. Test Appointment Rescheduling

- Call your Twilio phone number
- After the greeting, say "I need to reschedule my appointment"
- Follow the prompts to identify your existing appointment
- Select a new time slot
- Verify that you receive an SMS confirmation
- Check GoHighLevel to confirm the appointment was updated

### 5. Test Missed Call Follow-up

- Call your Twilio phone number and hang up before the bot answers
- Verify that you receive an SMS about the missed call
- Check GoHighLevel to confirm the contact was created and tagged

### 6. Test Outbound Calls

- Use the Twilio console to simulate an outbound call
- Verify that the appropriate message is played based on the call type

## Troubleshooting

- Check the Flask application logs for any errors
- Verify that your Twilio webhook URL is correctly configured
- Ensure your GoHighLevel API key has the necessary permissions
- Check that your Twilio phone number has voice capabilities enabled
