# URL Fix Implementation Details

This document explains the comprehensive URL fix implemented to resolve the issue with malformed audio URLs in the voice bot.

## Problem Description

The voice bot was experiencing an issue where audio URLs were being malformed with a duplicate domain pattern:

```
https://vanguard-voice-bot.onrender.coms://vanguard-voice-bot.onrender.com/audio/[hash].mp3
```

This caused Twilio to fail when trying to play the audio, resulting in "3 fast beeps" during calls.

## Comprehensive Fix Implementation

We've implemented a three-layer approach to ensure the issue is resolved:

### 1. Hardcoded Base URL

In `elevenlabs_integration.py`, we've replaced the reliance on environment variables with a hardcoded base URL:

```python
# Hardcoded base URL to ensure consistency
HARDCODED_BASE_URL = 'https://vanguard-voice-bot.onrender.com'
PUBLIC_URL_BASE = os.environ.get('PUBLIC_URL_BASE', HARDCODED_BASE_URL)

def get_audio_url_from_filename(filename):
    """
    Generate a clean, direct URL for an audio file using a hardcoded base URL.
    This ensures consistent URL formatting regardless of environment variables.
    """
    # Use hardcoded base URL instead of environment variable
    base_url = HARDCODED_BASE_URL
    
    # Create a clean URL by directly concatenating the base URL and path
    clean_url = f"{base_url}/audio/{filename}"
    
    logger.info(f"Created hardcoded audio URL: {clean_url}")
    return clean_url
```

### 2. URL Validation

We've added URL validation functions in both `elevenlabs_integration.py` and `response_builder.py` to catch and fix any malformed URLs:

```python
def validate_audio_url(url):
    """
    Validate and fix audio URLs to ensure they don't have the malformed pattern.
    """
    if not url:
        return url
    
    # Check for the specific malformed pattern
    if "onrender.coms://" in url:
        # Fix the malformed URL by replacing the problematic pattern
        fixed_url = url.replace("https://vanguard-voice-bot.onrender.coms://", "https://")
        logger.info(f"Fixed malformed URL: {url} -> {fixed_url}")
        return fixed_url
    
    return url
```

This validation is applied at multiple points in the code to ensure URLs are always properly formatted before being returned.

### 3. TwiML Response Sanitization

As a final safety measure, we've implemented a sanitization function in `response_builder.py` that checks the entire TwiML response string before it's returned:

```python
def sanitize_twiml(twiml_response):
    """
    Final safety check to sanitize the entire TwiML response string before returning it.
    This catches any malformed URLs that might have slipped through other validation layers.
    """
    if not twiml_response:
        return twiml_response
    
    # Check for the specific malformed pattern in the entire TwiML
    if "onrender.coms://" in twiml_response:
        # Fix the malformed URLs by replacing the problematic pattern
        sanitized_twiml = twiml_response.replace("https://vanguard-voice-bot.onrender.coms://", "https://")
        logger.info("Sanitized malformed URLs in final TwiML response")
        return sanitized_twiml
    
    return twiml_response
```

We've updated all route handlers in `routes.py` to apply this sanitization before returning any TwiML response:

```python
# Apply final sanitization to the TwiML response before returning
twiml_str = str(response)
sanitized_twiml = sanitize_twiml(twiml_str)
logger.info("Applied final TwiML sanitization in /voice route")
return sanitized_twiml
```

## Benefits of This Approach

1. **Multiple Layers of Protection**: By implementing three different approaches, we ensure that even if one layer fails, the others will catch and fix the issue.

2. **Improved Logging**: We've added detailed logging at each step to help diagnose any future issues.

3. **Resilience to Environment Changes**: The hardcoded base URL ensures that even if environment variables are misconfigured, the URLs will still be correctly formatted.

4. **Comprehensive Coverage**: The final TwiML sanitization ensures that all responses are checked, regardless of which part of the code generated them.

This comprehensive fix should resolve the issue with malformed audio URLs and ensure that the voice bot works correctly with both English (Rachel) and Spanish (Antonio) voices.
