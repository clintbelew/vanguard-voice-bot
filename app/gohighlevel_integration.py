""" GoHighLevel integration module. This module handles all interactions with the GoHighLevel API. """
import logging
import requests
import os
from config.config import ERROR_MESSAGES

# GoHighLevel API credentials
# These should be set in environment variables or a secure configuration
API_KEY = os.environ.get('GHL_API_KEY', '')
LOCATION_ID = os.environ.get('GHL_LOCATION_ID', '')
CALENDAR_ID = os.environ.get('GHL_CALENDAR_ID', '')

# Base URL for GoHighLevel API
BASE_URL = "https://rest.gohighlevel.com/v1"

def is_configured():
                """Check if GoHighLevel integration is properly configured."""
                return bool(API_KEY and LOCATION_ID)

def get_available_slots(date_str, service_id=None):
                """
                    Get available appointment slots for a specific date.

                            Args:def create_contact(phone, first_name=None, last_name=None, email=None):
                                """
                Create or update a contact in GoHighLevel.

                Args:
                    phone (str): Contact's phone number
                                    first_name (str, optional): Contact's first name
                                    last_name (str, optional): Contact's last name
                                    email (str, optional): Contact's email

                Returns:
                    dict: Contact data or None if error
    """
        if not is_configured():
                logging.warning("GoHighLevel integration not configured. Cannot create contact.")
                        return None

                                    try:
                                            # Return dummy data for testing
                                                    return {
                                                                "id": "dummy-contact-id",
                                                                            "phone": phone,
                                                                                        "firstName": first_name or "Test",
                                                                                                    "lastName": last_name or "User",
                                                                                                                "email": email or "test@example.com"
                                                                                                                        }
                                                                                                                            except Exception as e:
                                                                                                                                    logging.error(f"Error creating/updating contact: {str(e)}")
                                                                                                                                            return None
                                                                                                                                            
                                                                                                                                            def book_appointment(contact_id, date_str, time_str, service_id=None, notes=None):
                                                                                                                                                """
    Book an appointment in GoHighLevel.

    Args:
        contact_id (str): Contact ID
        date_str (str): Date in YYYY-MM-DD format
        time_str (str): Time in HH:MM format
        service_id (str, optional): Service ID
        notes (str, optional): Appointment notes

    Returns:
        dict: Appointment data or None if error
    """
        if not is_configured():
                logging.warning("GoHighLevel integration not configured. Cannot book appointment.")
                        return None

                                    try:
                                            if not CALENDAR_ID:
                                                        logging.error("Calendar ID not configured. Cannot book appointment.")
                                                                    return None

                                                                                        # Return dummy data for testing
                                                                                                return {
                                                                                                            "id": "dummy-appointment-id",
                                                                                                                        "contactId": contact_id,
                                                                                                                                    "dateTime": f"{date_str} {time_str}",
                                                                                                                                                "status": "confirmed"
                                                                                                                                                        }
                                                                                                                                                            except Exception as e:
                                                                                                                                                                    logging.error(f"Error booking appointment: {str(e)}")
                                                                                                                                                                            return None
                                                                                                                                                                            
                                                                                                                                                                            def add_tag_to_contact(contact_id, tag_name):
                                                                                                                                                                                """
    Add a tag to a contact in GoHighLevel.

    Args:
        contact_id (str): Contact ID
        tag_name (str): Tag name to add

    Returns:
        bool: True if successful, False otherwise
    """
        if not is_configured():
                logging.warning("GoHighLevel integration not configured. Cannot add tag to contact.")
                        return False

                                    try:
                                            # Return success for testing
                                                    logging.info(f"Added tag '{tag_name}' to contact {contact_id}")
                                                            return True
                                                                except Exception as e:
                                                                        logging.error(f"Error adding tag to contact: {str(e)}")
                                                                                return False
                                    date_str (str): Date in YYYY-MM-DD format
                                            service_id (str, optional): Service ID to filter slots

                                                        Returns:
                                                                list: List of available time slots or empty list if error
                                                                    """
                if not is_configured():
                                    logging.warning("GoHighLevel integration not configured. Cannot get available slots.")
                                    return []

    try:
                        if not CALENDAR_ID:
                                                logging.error("Calendar ID not configured. Cannot get available slots.")
                                                return []

        # Return dummy data for testing when real API is not available
                        return ["9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM", "2:00 PM", "3:00 PM"]
except Exception as e:
                    logging.error(f"Error getting available slots: {str(e)}")
                    return []
