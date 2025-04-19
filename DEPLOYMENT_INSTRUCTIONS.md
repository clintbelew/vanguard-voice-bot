"""
Deployment Instructions for Enhanced Voice Bot with ElevenLabs Integration

This document provides comprehensive instructions for deploying the enhanced
voice bot with ElevenLabs integration to make it sound truly lifelike.
"""

# Enhanced Voice Bot Deployment Instructions

## Overview

The enhanced voice bot now features lifelike speech using ElevenLabs voices, natural conversation patterns, optimized background ambiance, and improved pacing and transitions. This document provides step-by-step instructions for deploying these enhancements to your Render service.

## Prerequisites

1. ElevenLabs API key (sign up at https://elevenlabs.io if you don't have one)
2. Render account with existing voice bot deployment
3. GitHub repository access (https://github.com/clintbelew/vanguard-voice-bot)

## Environment Variables

Add the following environment variables to your Render service:

| Variable Name | Description | Example Value |
|---------------|-------------|---------------|
| ELEVENLABS_API_KEY | Your ElevenLabs API key | abc123xyz456... |
| ELEVENLABS_VOICE_ID | (Optional) Override default voice ID | 21m00Tcm4TlvDq8ikWAM |
| PUBLIC_URL_BASE | Base URL for accessing audio files | https://your-service.onrender.com/audio |

## Deployment Steps

### 1. Update GitHub Repository

1. Download the enhanced voice bot files provided in the ZIP package
2. Extract the files to a local directory
3. Upload all files to your GitHub repository (https://github.com/clintbelew/vanguard-voice-bot)
   - You can use the GitHub web interface or Git commands
   - Make sure to include all new files in the `app` directory

### 2. Configure Render Service

1. Log in to your Render dashboard
2. Navigate to your voice bot service
3. Go to the "Environment" tab
4. Add the environment variables listed above
5. Save changes

### 3. Deploy the Enhanced Voice Bot

1. Go to the "Manual Deploy" tab in your Render dashboard
2. Click "Deploy latest commit" to trigger a new deployment
3. Wait for the deployment to complete (typically 2-5 minutes)

### 4. Verify Deployment

1. Check the deployment logs for any errors
2. Visit your service URL to confirm it's running
3. Test the voice bot by calling (830) 429-4111
4. Verify that the voice sounds lifelike and natural

## File Structure

The enhanced voice bot consists of the following key files:

```
improved_voice_bot/
├── app/
│   ├── __init__.py
│   ├── elevenlabs_integration.py  # ElevenLabs API integration
│   ├── conversation_enhancer.py   # Natural conversation patterns
│   ├── pacing_enhancer.py         # Improved pacing and transitions
│   ├── ambiance_optimizer.py      # Optimized background ambiance
│   ├── audio_manager.py           # Audio file management
│   ├── voice_bot_integration.py   # Unified integration module
│   ├── enhanced_routes.py         # Enhanced route handlers
│   ├── routes.py                  # Original route handlers (backup)
│   ├── twilio_utils.py            # Twilio utility functions
│   └── gohighlevel_integration.py # GoHighLevel integration
├── config/
│   ├── __init__.py
│   └── config.py                  # Configuration settings
├── test_enhanced_voice_bot.py     # Test script for enhancements
├── requirements.txt               # Project dependencies
└── run.py                         # Application entry point
```

## Troubleshooting

### ElevenLabs API Issues

If you encounter issues with the ElevenLabs integration:

1. Verify your API key is correct
2. Check the Render logs for specific error messages
3. The voice bot will automatically fall back to Twilio's Say verb if ElevenLabs fails

### Audio Playback Issues

If audio files aren't playing correctly:

1. Ensure the PUBLIC_URL_BASE environment variable is set correctly
2. Check that the Render service has proper permissions to create and access audio files
3. Verify the /tmp directory is writable in your Render environment

### Deployment Failures

If deployment fails:

1. Check the Render logs for specific error messages
2. Verify all required files are present in your GitHub repository
3. Ensure all dependencies are listed in requirements.txt

## Maintenance and Updates

### Updating Voice Options

To change the default voice:

1. Set the ELEVENLABS_VOICE_ID environment variable to your preferred voice ID
2. Or modify the voice_name parameter in voice_bot_integration.py

### Customizing Ambiance

To customize the background ambiance:

1. Edit the AMBIANCE_OPTIONS dictionary in ambiance_optimizer.py
2. Add new ambiance options with URLs and recommended volume levels

### Adjusting Conversation Patterns

To modify conversation patterns:

1. Edit the relevant constants in conversation_enhancer.py
2. Update the context parameters in enhanced_routes.py for different scenarios

## Support

If you encounter any issues or have questions about the enhanced voice bot, please contact support at support@vanguardchiropractic.com.
