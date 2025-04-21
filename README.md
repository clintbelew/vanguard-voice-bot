# Enhanced Voice Bot for Vanguard Chiropractic

This directory contains enhanced versions of the voice bot files with the following improvements:

## Enhancements

1. **More Natural Voice**: Upgraded to Polly.Joanna for a more natural-sounding text-to-speech experience
2. **Intent Handling for Common Questions**:
   - "Can I talk to someone?" - Offers to connect with a human
   - "Do you take credit cards?" - Confirms acceptance of major credit cards
   - "Is this covered by insurance?" - Explains insurance coverage
   - "Do you offer walk-ins?" - Explains walk-in policy
3. **Improved Fallback Response**: For questions the bot can't answer, it now says "I'm not totally sure how to answer that, but I can connect you with someone if you'd like."

## Implementation Details

- **routes.py**: Main application routes including the voice webhook endpoint
- **twilio_utils.py**: Helper functions for voice interactions
- **config.py**: Configuration settings for the voice bot

## Deployment Instructions

To deploy these enhancements:

1. Log into GitHub and navigate to the repository
2. Replace the existing files with these enhanced versions
3. Commit the changes to trigger a redeployment on Render
4. Test the voice bot by calling (830) 429-4111
