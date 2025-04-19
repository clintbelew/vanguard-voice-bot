"""
GoHighLevel Integration Module for Voice Bot

This module handles the integration with GoHighLevel API for appointment booking
and calendar management.
"""

import os
import requests
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GHL_API_KEY = os.environ.get('GHL_API_KEY', '')
GHL_LOCATION_ID = os.environ.get('GHL_LOCATION_ID', '')
GHL_CALENDAR_ID = os.environ.get('GHL_CALENDAR_ID', '')
GHL_API_BASE_URL = 'https://services.leadconnectorhq.com'

def is_configured():
    """Check if GoHighLevel API is configured properly."""
    if not GHL_API_KEY:
        logger.warning("GoHighLevel API key is not set")
        return False
    
    if not GHL_LOCATION_ID:
        logger.warning("GoHighLevel location ID is not set")
        return False
    
    if not GHL_CALENDAR_ID:
        logger.warning("GoHighLevel calendar ID is not set")
        return False
    
    logger.info("GoHighLevel API is configured with key, location ID, and calendar ID")
    return True

def check_availability(days_ahead=3):
    """
    Check appointment availability for the next few days.
    
    Args:
        days_ahead (int): Number of days to check ahead (default: 3)
    
    Returns:
        list: List of available appointment slots
    """
    if not is_configured():
        logger.warning("GoHighLevel not configured, cannot check availability")
        return []
    
    try:
        logger.info(f"Checking appointment availability for next {days_ahead} days")
        
        # Calculate date range
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        # API endpoint
        url = f"{GHL_API_BASE_URL}/api/v1/appointments/availability/{GHL_CALENDAR_ID}"
        
        headers = {
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
        
        params = {
            "locationId": GHL_LOCATION_ID,
            "startDate": start_date,
            "endDate": end_date
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Process available slots
            available_slots = []
            for date_key, slots in data.get('availability', {}).items():
                for slot in slots:
                    slot_time = datetime.fromisoformat(slot['startTime'].replace('Z', '+00:00'))
                    
                    # Format the time for speech
                    formatted_time = slot_time.strftime('%A at %-I:%M %p')
                    
                    available_slots.append({
                        'date': date_key,
                        'start_time': slot['startTime'],
                        'end_time': slot['endTime'],
                        'formatted_time': formatted_time
                    })
            
            logger.info(f"Found {len(available_slots)} available slots")
            return available_slots
        else:
            logger.error(f"Error checking availability: {response.status_code} - {response.text}")
            return []
    
    except Exception as e:
        logger.error(f"Exception in check_availability: {str(e)}")
        return []

def book_appointment(slot, contact_info):
    """
    Book an appointment using the specified slot and contact information.
    
    Args:
        slot (dict): The appointment slot to book
        contact_info (dict): Contact information for the appointment
    
    Returns:
        dict: Appointment details if successful, None otherwise
    """
    if not is_configured():
        logger.warning("GoHighLevel not configured, cannot book appointment")
        return None
    
    try:
        logger.info(f"Booking appointment for {contact_info.get('name')} at {slot.get('formatted_time')}")
        
        # API endpoint
        url = f"{GHL_API_BASE_URL}/api/v1/appointments"
        
        headers = {
            "Authorization": f"Bearer {GHL_API_KEY}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }
        
        # Prepare appointment data
        appointment_data = {
            "calendarId": GHL_CALENDAR_ID,
            "locationId": GHL_LOCATION_ID,
            "startTime": slot['start_time'],
            "endTime": slot['end_time'],
            "title": "New Appointment",
            "contact": {
                "name": contact_info.get('name', ''),
                "email": contact_info.get('email', ''),
                "phone": contact_info.get('phone', '')
            }
        }
        
        response = requests.post(url, headers=headers, json=appointment_data)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Appointment booked successfully: {data.get('id')}")
            return data
        else:
            logger.error(f"Error booking appointment: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Exception in book_appointment: {str(e)}")
        return None
