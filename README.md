# Vanguard Voice Bot for Railway

A Twilio-powered voice bot with OpenAI and ElevenLabs integration and GoHighLevel appointment booking, deployed on Railway.

## Features

- **OpenAI Integration**: Uses o4-mini model for intelligent conversation handling
- **Twilio Integration**: Handles incoming calls with natural conversation flow
- **ElevenLabs Voice Generation**: High-quality text-to-speech for natural-sounding responses
- **GoHighLevel Appointment Booking**: Creates contacts and books appointments in GoHighLevel
- **Railway Deployment**: Optimized for deployment on Railway platform

## Endpoints

- `/health`: Health check endpoint
- `/voice`: OpenAI-powered text processing with ElevenLabs voice generation
- `/book`: GoHighLevel appointment booking
- `/twilio/voice`: Twilio webhook for incoming calls
- `/twilio/intent`: Twilio webhook for processing speech input
- `/twilio/appointment_confirm`: Twilio webhook for appointment confirmation

## Setup Instructions

### Prerequisites

- Python 3.10+
- OpenAI API key (for o4-mini model)
- ElevenLabs API key
- GoHighLevel API key, location ID, and calendar ID
- Twilio account with a phone number

### Local Development

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on `.env.example`:
   ```
   cp .env.example .env
   ```
5. Edit the `.env` file with your API keys and configuration
6. Run the application:
   ```
   python app.py
   ```
7. The application will be available at http://localhost:5000

### Railway Deployment

1. Create a new project on Railway
2. Connect your GitHub repository
3. Add the required environment variables:
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL` (defaults to o4-mini if not set)
   - `ELEVENLABS_API_KEY`
   - `ELEVENLABS_VOICE_ID`
   - `GHL_API_KEY`
   - `GHL_LOCATION_ID`
   - `GHL_CALENDAR_ID`
   - `BUSINESS_NAME`
   - `BUSINESS_LOCATION`
   - `BUSINESS_PHONE`
   - `FLASK_SECRET_KEY`
4. Railway will automatically detect the Python project and deploy it
5. Once deployed, configure your Twilio phone number to use the Railway URL for voice webhooks:
   - Voice webhook URL: `https://your-railway-app.up.railway.app/twilio/voice`

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `OPENAI_MODEL` | OpenAI model to use (defaults to o4-mini) |
| `ELEVENLABS_API_KEY` | Your ElevenLabs API key |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice ID (Jessica) |
| `GHL_API_KEY` | GoHighLevel API key |
| `GHL_LOCATION_ID` | GoHighLevel location ID |
| `GHL_CALENDAR_ID` | GoHighLevel calendar ID |
| `BUSINESS_NAME` | Your business name |
| `BUSINESS_LOCATION` | Your business address |
| `BUSINESS_PHONE` | Your business phone number |
| `FLASK_SECRET_KEY` | Secret key for Flask sessions |
| `PORT` | Port for local development (default: 5000) |

## OpenAI Integration

The voice bot uses OpenAI's o4-mini model to:

- Handle call prompts intelligently
- Track conversation context throughout the call
- Collect caller information (name, phone, email, preferred time)
- Automatically trigger appointment booking when all information is collected

The OpenAI integration works out of the box when the environment variables are set. No additional configuration is needed.

## Testing

### Testing the Voice Generation Endpoint

```bash
curl -X POST http://localhost:5000/voice \
  -H "Content-Type: application/json" \
  -d '{
    "text":"Hello, I'd like to schedule an appointment.",
    "conversation_id":"test-123"
  }'
```

### Testing the Appointment Booking Endpoint

```bash
curl -X POST http://localhost:5000/book \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "phone": "1234567890",
    "email": "test@example.com",
    "selectedSlot": "2025-04-25T10:00:00"
  }'
```

## Twilio Configuration

1. Log in to your Twilio account
2. Navigate to Phone Numbers > Manage > Active Numbers
3. Select your phone number
4. Under "Voice & Fax", set the following:
   - When a call comes in: Webhook
   - URL: `https://your-railway-app.up.railway.app/twilio/voice`
   - HTTP Method: POST

## License

MIT
