"""
Test script for the voice bot application.
"""
import requests
import json
import logging
import os
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_voice_bot.log"),
        logging.StreamHandler()
    ]
)

# Base URL for the voice bot application
BASE_URL = "http://localhost:5000"

def test_index_route():
    """Test the index route."""
    try:
        response = requests.get(f"{BASE_URL}/")
        logging.info(f"Index route response: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error testing index route: {str(e)}")
        return False

def test_voice_route():
    """Test the voice route."""
    try:
        # Simulate a Twilio POST request
        data = {
            "From": "+12345678900",
            "CallSid": "CA123456789",
            "AccountSid": "AC123456789"
        }
        response = requests.post(f"{BASE_URL}/voice", data=data)
        logging.info(f"Voice route response: {response.status_code}")
        logging.info(f"Voice route response content: {response.text}")
        return response.status_code == 200 and "<Response>" in response.text
    except Exception as e:
        logging.error(f"Error testing voice route: {str(e)}")
        return False

def test_handle_response_route():
    """Test the handle-response route."""
    try:
        # Simulate a Twilio POST request with speech result
        data = {
            "From": "+12345678900",
            "CallSid": "CA123456789",
            "AccountSid": "AC123456789",
            "SpeechResult": "I need to schedule an appointment"
        }
        response = requests.post(f"{BASE_URL}/handle-response", data=data)
        logging.info(f"Handle response route response: {response.status_code}")
        logging.info(f"Handle response route content: {response.text}")
        return response.status_code == 200 and "<Response>" in response.text
    except Exception as e:
        logging.error(f"Error testing handle-response route: {str(e)}")
        return False

def test_log_speech_route():
    """Test the log-speech route."""
    try:
        # Simulate a POST request to log speech
        data = {
            "speech_text": "This is a test speech input",
            "caller": "+12345678900"
        }
        response = requests.post(f"{BASE_URL}/log-speech", json=data)
        logging.info(f"Log speech route response: {response.status_code}")
        logging.info(f"Log speech route content: {response.text}")
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Error testing log-speech route: {str(e)}")
        return False

def test_error_handling():
    """Test error handling by sending invalid data."""
    try:
        # Send invalid data to trigger an error
        data = {
            "From": "+12345678900",
            "CallSid": "CA123456789",
            "AccountSid": "AC123456789",
            "InvalidParam": "This should cause an error"
        }
        response = requests.post(f"{BASE_URL}/handle-response", data=data)
        logging.info(f"Error handling test response: {response.status_code}")
        logging.info(f"Error handling test content: {response.text}")
        # Even with an error, we should get a 200 response with a TwiML fallback
        return response.status_code == 200 and "<Response>" in response.text
    except Exception as e:
        logging.error(f"Error testing error handling: {str(e)}")
        return False

def check_log_files():
    """Check if log files are being created."""
    log_files = [
        "voice_bot.log",
        "logs/speech_inputs.log",
        "logs/errors.log",
        "logs/requests.log"
    ]
    
    for log_file in log_files:
        if not os.path.exists(log_file):
            logging.warning(f"Log file {log_file} does not exist")
            return False
    
    logging.info("All log files exist")
    return True

def run_tests():
    """Run all tests."""
    logging.info("Starting voice bot tests")
    
    # Wait for the application to start
    time.sleep(2)
    
    tests = [
        ("Index Route", test_index_route),
        ("Voice Route", test_voice_route),
        ("Handle Response Route", test_handle_response_route),
        ("Log Speech Route", test_log_speech_route),
        ("Error Handling", test_error_handling),
        ("Log Files", check_log_files)
    ]
    
    results = {}
    all_passed = True
    
    for name, test_func in tests:
        logging.info(f"Running test: {name}")
        result = test_func()
        results[name] = "PASSED" if result else "FAILED"
        if not result:
            all_passed = False
        logging.info(f"Test {name}: {results[name]}")
    
    # Print summary
    logging.info("Test Summary:")
    for name, result in results.items():
        logging.info(f"{name}: {result}")
    
    if all_passed:
        logging.info("All tests PASSED!")
    else:
        logging.warning("Some tests FAILED!")
    
    return all_passed

if __name__ == "__main__":
    run_tests()
