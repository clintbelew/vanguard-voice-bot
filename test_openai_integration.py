import requests
import json
import os
import sys
import time

# Test script for OpenAI integration in Vanguard Voice Bot

# Base URL for local testing
BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    """Test the health check endpoint"""
    print("\n=== Testing /health endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_voice_endpoint_with_openai():
    """Test the voice generation endpoint with OpenAI integration"""
    print("\n=== Testing /voice endpoint with OpenAI integration ===")
    try:
        payload = {
            "text": "I'd like to schedule an appointment for next week",
            "conversation_id": f"test-{int(time.time())}"
        }
        response = requests.post(
            f"{BASE_URL}/voice", 
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status code: {response.status_code}")
        print(f"Content type: {response.headers.get('Content-Type')}")
        print(f"Content length: {len(response.content)} bytes")
        
        # Save the audio file for verification
        if response.status_code == 200:
            with open("test_voice_openai_output.mp3", "wb") as f:
                f.write(response.content)
            print("Audio saved to test_voice_openai_output.mp3")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_book_endpoint():
    """Test the appointment booking endpoint"""
    print("\n=== Testing /book endpoint ===")
    try:
        payload = {
            "name": "Test User",
            "phone": "1234567890",
            "email": "test@example.com",
            "selectedSlot": "2025-04-25T10:00:00"
        }
        response = requests.post(
            f"{BASE_URL}/book", 
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2) if response.status_code == 200 else response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_twilio_voice_endpoint():
    """Test the Twilio voice webhook"""
    print("\n=== Testing /twilio/voice endpoint ===")
    try:
        response = requests.post(f"{BASE_URL}/twilio/voice")
        print(f"Status code: {response.status_code}")
        print(f"Content type: {response.headers.get('Content-Type')}")
        print(f"Response length: {len(response.text)} characters")
        return response.status_code == 200 and "TwiML" in response.text
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests and report results"""
    print("Starting Vanguard Voice Bot endpoint tests with OpenAI integration...")
    
    results = {
        "health": test_health_endpoint(),
        "voice_openai": test_voice_endpoint_with_openai(),
        "book": test_book_endpoint(),
        "twilio_voice": test_twilio_voice_endpoint()
    }
    
    print("\n=== Test Results Summary ===")
    for test, result in results.items():
        print(f"{test}: {'PASS' if result else 'FAIL'}")
    
    if all(results.values()):
        print("\nAll tests passed successfully!")
        return 0
    else:
        print("\nSome tests failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
