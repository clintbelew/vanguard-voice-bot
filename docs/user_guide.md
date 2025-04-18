# Twilio Voice Chat Bot - User Guide

## Overview

This voice chat bot for Vanguard Chiropractic is designed to handle incoming calls, answer frequently asked questions, book appointments, and manage follow-ups. The bot uses Twilio for voice communication and integrates with GoHighLevel for contact and appointment management.

## Features

- **Automated Greeting**: Welcomes callers with a branded introduction
- **FAQ Handling**: Answers common questions about hours, services, insurance, and location
- **Appointment Booking**: Helps new and existing patients book appointments
- **Appointment Rescheduling**: Assists patients in changing their appointment times
- **Missed Call Follow-up**: Automatically sends text messages for missed calls
- **Appointment Reminders**: Makes outbound calls to remind patients of upcoming appointments
- **Missed Appointment Follow-up**: Contacts patients who missed their appointments
- **GoHighLevel Integration**: Syncs all contact and appointment data with your CRM

## System Requirements

- Python 3.10 or higher
- Flask web framework
- Twilio account with a phone number
- GoHighLevel account with API access
- Web server for hosting the application

## Setup Instructions

1. **Environment Configuration**:
   - Copy the `.env.example` file to `.env`
   - Fill in your Twilio and GoHighLevel credentials
   - Update business information as needed

2. **Twilio Configuration**:
   - Log in to your Twilio account
   - Configure your Twilio phone number's voice webhook to point to your application's `/voice` endpoint
   - Ensure your Twilio number has voice capabilities enabled

3. **GoHighLevel Configuration**:
   - Generate an API key in your GoHighLevel account
   - Note your location ID
   - Add these to your environment variables

4. **Application Deployment**:
   - Deploy the application using the instructions in the deployment guide
   - Test the deployment by calling your Twilio number

## Customization Options

### Business Information

You can customize the business information in the `config.py` file or through environment variables:

- Business name
- Business hours
- Business location
- Business phone number

### FAQ Content

Modify the FAQ responses in the `config.py` file to match your specific business information:

- Hours of operation
- Services offered
- Insurance accepted
- Location details
- Emergency information

### Voice Settings

Customize the voice settings in the `config.py` file:

- Voice name (e.g., Polly.Joanna)
- Voice language
- Greeting message

## Call Flow

1. **Incoming Call**:
   - Bot answers with greeting: "Thank you for calling Vanguard Chiropractic. How can I help you today?"
   - Caller responds with their request

2. **Intent Recognition**:
   - Bot identifies the caller's intent (FAQ, appointment, etc.)
   - Processes the request accordingly

3. **FAQ Handling**:
   - If the caller asks about hours, services, insurance, or location
   - Bot provides the relevant information
   - Asks if there's anything else the caller needs

4. **Appointment Booking**:
   - Asks if caller is a new or existing patient
   - Collects necessary information
   - Offers available time slots
   - Confirms appointment details
   - Sends confirmation via SMS
   - Updates GoHighLevel

5. **Call Completion**:
   - Thanks the caller
   - Ends the call

## Maintenance

### Monitoring

- Check application logs regularly for errors
- Monitor Twilio console for call statistics
- Review GoHighLevel for contact and appointment data

### Updates

- Update FAQ information as needed
- Adjust business hours when they change
- Update service offerings as they evolve

### Troubleshooting

- If calls aren't being answered, check your Twilio webhook configuration
- If appointments aren't syncing, verify your GoHighLevel API credentials
- If SMS messages aren't being sent, check your Twilio account balance

## Support

For technical support or questions about the voice bot:

1. Review the documentation in the `docs` folder
2. Check the application logs for error messages
3. Contact your system administrator or developer

## Best Practices

- Regularly test the voice bot by calling your Twilio number
- Update FAQ content to reflect common questions from patients
- Monitor call recordings (if enabled) to improve the conversation flow
- Keep your Twilio and GoHighLevel credentials secure
- Backup your configuration files regularly
