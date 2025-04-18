# Testing Guide for Deployed Twilio Voice Bot

This guide provides comprehensive instructions for testing your deployed Twilio Voice Bot to ensure all functionality is working correctly.

## Prerequisites for Testing

Before testing, ensure:
1. Your application is successfully deployed to Render.com
2. Your Twilio webhook is configured to point to your deployed application
3. Your Twilio phone number has voice capabilities enabled

## Test Scenarios

### 1. Basic Voice Greeting Test

**Objective**: Verify that the voice bot answers calls and plays the greeting message.

**Steps**:
1. Call your Twilio phone number (+18305900834)
2. Listen for the greeting: "Thank you for calling Vanguard Chiropractic. How can I help you today?"
3. Verify the voice quality and that the message plays completely

**Expected Result**: The call should be answered promptly, and the greeting should play clearly.

### 2. FAQ Response Testing

**Objective**: Verify that the voice bot correctly responds to FAQ questions.

**Steps**:
1. Call your Twilio phone number
2. After the greeting, ask one of the following questions:
   - "What are your hours?"
   - "What services do you offer?"
   - "Do you accept insurance?"
   - "Where are you located?"
3. Listen to the response
4. Repeat with each question to test all FAQ responses

**Expected Result**: The bot should correctly recognize each question and provide the appropriate response from the configured FAQ information.

### 3. Appointment Booking Test

**Objective**: Verify the appointment booking functionality.

**Steps**:
1. Call your Twilio phone number
2. After the greeting, say "I'd like to schedule an appointment"
3. When asked if you're a new or existing patient, press 1 for new patient
4. Follow the prompts to provide:
   - Your name (speak a test name)
   - Your phone number (speak a test number)
   - Reason for visit (speak a test reason)
5. Select an available time slot when offered

**Expected Result**: 
- The bot should guide you through the appointment booking process
- You should receive an SMS confirmation to the phone number you called from
- A new contact and appointment should be created in GoHighLevel

### 4. Appointment Rescheduling Test

**Objective**: Verify the appointment rescheduling functionality.

**Steps**:
1. Call your Twilio phone number
2. After the greeting, say "I need to reschedule my appointment"
3. Provide your phone number when prompted
4. Follow the prompts to select a new appointment time

**Expected Result**: 
- The bot should locate your existing appointment
- Guide you through selecting a new time
- Send an SMS confirmation of the rescheduled appointment
- Update the appointment in GoHighLevel

### 5. Missed Call Follow-up Test

**Objective**: Verify that missed calls trigger SMS follow-ups.

**Steps**:
1. Call your Twilio phone number
2. Hang up before the bot answers or during the greeting
3. Wait a few minutes

**Expected Result**: 
- You should receive an SMS message about the missed call
- The message should include a callback number
- A missed call record should be created in GoHighLevel

### 6. GoHighLevel Integration Test

**Objective**: Verify that data is correctly syncing with GoHighLevel.

**Steps**:
1. Complete the appointment booking test above
2. Log in to your GoHighLevel account
3. Check for:
   - New contact creation with correct phone number
   - New appointment creation with correct details
   - Proper tagging of contacts

**Expected Result**: All data should be correctly synced to GoHighLevel with appropriate details.

## Monitoring and Debugging

### Checking Render Logs

If you encounter issues, checking the application logs can help identify problems:

1. Go to your [Render Dashboard](https://dashboard.render.com/)
2. Select your web service
3. Click on "Logs" in the left sidebar
4. Look for any error messages related to your issue

### Checking Twilio Logs

Twilio also provides detailed logs for debugging:

1. Log in to your [Twilio Console](https://www.twilio.com/console)
2. Navigate to Monitor > Logs > Calls
3. Find your test calls and check their status
4. Click on a call SID to see detailed information about that call

## Common Issues and Solutions

### Voice Recognition Problems
- Speak clearly and in a quiet environment
- Try using simple, direct phrases
- If voice recognition fails, try using keypad inputs (DTMF)

### SMS Not Received
- Verify your Twilio account has SMS capabilities enabled
- Check that your account has sufficient credits
- Ensure the phone number you're testing with can receive SMS

### GoHighLevel Integration Issues
- Verify your API key and location ID are correct in your Render environment variables
- Check Render logs for any API errors
- Ensure your GoHighLevel account has the necessary permissions

## Next Steps After Testing

Once you've verified all functionality is working correctly:

1. Consider setting up monitoring alerts for application errors
2. Establish a regular testing schedule to ensure continued functionality
3. Collect user feedback to improve the voice bot experience
4. Consider expanding the FAQ responses based on common questions

If you encounter any issues that you cannot resolve, please refer to the documentation or reach out for additional support.
