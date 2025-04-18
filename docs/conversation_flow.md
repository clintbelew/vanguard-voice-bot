# Twilio Voice Chat Bot - Conversation Flow Design

## Overview
This document outlines the conversation flow for the Vanguard Chiropractic voice bot. The bot is designed to handle incoming calls, answer FAQs, book appointments, and manage follow-ups.

## Main Conversation Flow

### 1. Greeting
- Bot answers call with branded greeting: "Thank you for calling Vanguard Chiropractic. How can I help you today?"
- Bot listens for caller's initial request

### 2. Intent Recognition
The bot will identify the caller's intent from the following categories:
- FAQ inquiry (hours, services, insurance, location)
- Appointment booking/rescheduling
- Urgent issue/emergency
- Speaking with staff member
- Other/unrecognized intent

### 3. FAQ Handling
If the caller asks about:
- **Hours**: Provide business hours for each day of the week
- **Services**: List available chiropractic services
- **Insurance**: Explain accepted insurance plans
- **Location**: Provide address and parking information

### 4. Appointment Booking Flow
1. Ask if caller is a new or existing patient
2. For new patients:
   - Collect name
   - Collect phone number
   - Ask about reason for visit
   - Offer available time slots
   - Confirm appointment details
   - Send confirmation via SMS
   - Create contact in GoHighLevel
3. For existing patients:
   - Ask for name or phone number to locate record
   - Verify identity
   - Offer available time slots
   - Confirm appointment details
   - Send confirmation via SMS
   - Update appointment in GoHighLevel

### 5. Appointment Rescheduling Flow
1. Ask for name or phone number to locate existing appointment
2. Verify identity
3. Confirm current appointment details
4. Offer available new time slots
5. Confirm new appointment details
6. Send confirmation via SMS
7. Update appointment in GoHighLevel

### 6. Missed Call Follow-up
When a call is missed:
1. Record caller's phone number
2. Send automated text message: "Sorry we missed your call to Vanguard Chiropractic. Please call us back at [BUSINESS_PHONE] or reply to this message to schedule an appointment."
3. Create missed call record in GoHighLevel
4. Tag contact for follow-up

### 7. Appointment Reminder/Follow-up Calls
For upcoming appointments:
1. Call patient 24 hours before appointment
2. If answered:
   - Identify as Vanguard Chiropractic automated system
   - Remind of appointment date and time
   - Ask for confirmation
   - Update appointment status in GoHighLevel
3. If not answered:
   - Leave voicemail with appointment details
   - Send text message reminder
   - Update appointment status in GoHighLevel

For missed appointments:
1. Call patient same day of missed appointment
2. If answered:
   - Express concern about missed appointment
   - Offer to reschedule
   - Update appointment status in GoHighLevel
3. If not answered:
   - Leave voicemail expressing concern
   - Send text message offering to reschedule
   - Update appointment status in GoHighLevel

### 8. Fallback/Escalation
If the bot cannot understand or handle the request:
1. Apologize for not understanding
2. Offer to connect to staff member during business hours
3. Offer to take a message outside business hours
4. Provide option to receive a callback

## Dialog Scripts

### Greeting
"Thank you for calling Vanguard Chiropractic. How can I help you today?"

### FAQ Responses

#### Hours
"Our hours of operation are: Monday through Thursday from 9:00 AM to 6:00 PM, Friday from 9:00 AM to 5:00 PM, Saturday from 10:00 AM to 2:00 PM, and we are closed on Sunday. Is there anything else you'd like to know?"

#### Services
"We offer a variety of chiropractic services including spinal adjustments, massage therapy, physical rehabilitation, and nutritional counseling. Would you like to hear more about any specific service or would you like to schedule an appointment?"

#### Insurance
"We accept most major insurance plans including Blue Cross, Aetna, Cigna, and Medicare. Please note that coverage varies by plan. Would you like us to verify your insurance benefits before your appointment?"

#### Location
"We are located at 123 Main Street, Anytown, CA 12345. Free parking is available in our lot. Would you like me to text you directions?"

### Appointment Booking

#### New Patient
"I'd be happy to help you book an appointment. Are you a new patient or have you visited us before?"

"Great! As a new patient, I'll need to collect some information. May I have your full name?"

"Thank you, [NAME]. What's the best phone number to reach you?"

"What's the primary reason for your visit today?"

"We have the following appointments available: [LIST AVAILABLE SLOTS]. Which time works best for you?"

"Perfect! I've scheduled you for [DATE] at [TIME]. You'll receive a text message confirmation shortly. Is there anything else I can help you with today?"

#### Existing Patient
"I'd be happy to help you book an appointment. May I have your name or phone number to locate your record?"

"Thank you for providing that information. I see you're an existing patient. What's the reason for your visit today?"

"We have the following appointments available: [LIST AVAILABLE SLOTS]. Which time works best for you?"

"Perfect! I've scheduled you for [DATE] at [TIME]. You'll receive a text message confirmation shortly. Is there anything else I can help you with today?"

### Missed Call Follow-up Text
"Sorry we missed your call to Vanguard Chiropractic. Please call us back at [BUSINESS_PHONE] or reply to this message to schedule an appointment."

### Appointment Reminder Call
"Hello, this is an automated reminder from Vanguard Chiropractic. You have an appointment scheduled for [DATE] at [TIME]. Please press 1 to confirm this appointment, press 2 to reschedule, or stay on the line to speak with our staff."

### Missed Appointment Follow-up
"Hello, this is Vanguard Chiropractic calling about your missed appointment today. We're concerned about your health and would like to help you reschedule. Please press 1 to reschedule now, or call us back at [BUSINESS_PHONE] at your convenience."

### Fallback Response
"I'm sorry, but I didn't quite understand that. Could you please rephrase your question? Or, if you'd prefer to speak with a staff member, please say 'speak to staff'."

### Emergency Response
"If you're experiencing a medical emergency, please hang up and dial 911 immediately. For urgent but non-emergency issues, please hold and I'll connect you with our staff right away."
