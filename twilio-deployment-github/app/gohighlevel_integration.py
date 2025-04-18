import requests
import logging
from config.config import (
    GOHIGHLEVEL_API_KEY,
    GOHIGHLEVEL_LOCATION_ID,
    GOHIGHLEVEL_API_URL
)

# Initialize logging
logging.basicConfig(level=logging.INFO)

def make_api_request(endpoint, method='GET', data=None):
    """Make a request to the GoHighLevel API."""
    if not GOHIGHLEVEL_API_KEY:
        logging.error("GoHighLevel API key not configured")
        return None
    
    headers = {
        'Authorization': f'Bearer {GOHIGHLEVEL_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    url = f"{GOHIGHLEVEL_API_URL}{endpoint}"
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        else:
            logging.error(f"Unsupported method: {method}")
            return None
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return None

def create_contact(contact_data):
    """Create a new contact in GoHighLevel."""
    endpoint = f"locations/{GOHIGHLEVEL_LOCATION_ID}/contacts"
    
    # Ensure required fields are present
    if 'phone' not in contact_data:
        logging.error("Phone number is required for contact creation")
        return None
    
    response = make_api_request(endpoint, method='POST', data=contact_data)
    
    if response and 'contact' in response and 'id' in response['contact']:
        return response['contact']['id']
    return None

def update_contact(contact_id, contact_data):
    """Update an existing contact in GoHighLevel."""
    endpoint = f"locations/{GOHIGHLEVEL_LOCATION_ID}/contacts/{contact_id}"
    
    response = make_api_request(endpoint, method='PUT', data=contact_data)
    
    if response and 'contact' in response and 'id' in response['contact']:
        return True
    return False

def get_contact(phone_number):
    """Get contact details by phone number."""
    endpoint = f"locations/{GOHIGHLEVEL_LOCATION_ID}/contacts/lookup?phone={phone_number}"
    
    response = make_api_request(endpoint)
    
    if response and 'contacts' in response and len(response['contacts']) > 0:
        return response['contacts'][0]
    return None

def tag_contact(contact_id, tag_name):
    """Add a tag to a contact in GoHighLevel."""
    endpoint = f"locations/{GOHIGHLEVEL_LOCATION_ID}/contacts/{contact_id}/tags"
    
    data = {
        'tags': [tag_name]
    }
    
    response = make_api_request(endpoint, method='POST', data=data)
    
    if response:
        return True
    return False

def create_appointment(appointment_data):
    """Create a new appointment in GoHighLevel."""
    endpoint = f"locations/{GOHIGHLEVEL_LOCATION_ID}/appointments"
    
    # Ensure required fields are present
    required_fields = ['contactId', 'calendarId', 'startTime', 'endTime']
    for field in required_fields:
        if field not in appointment_data:
            logging.error(f"Required field missing for appointment creation: {field}")
            return None
    
    response = make_api_request(endpoint, method='POST', data=appointment_data)
    
    if response and 'appointment' in response and 'id' in response['appointment']:
        return response['appointment']['id']
    return None

def update_appointment(appointment_id, appointment_data):
    """Update an existing appointment in GoHighLevel."""
    endpoint = f"locations/{GOHIGHLEVEL_LOCATION_ID}/appointments/{appointment_id}"
    
    response = make_api_request(endpoint, method='PUT', data=appointment_data)
    
    if response and 'appointment' in response and 'id' in response['appointment']:
        return True
    return False

def get_appointment(appointment_id):
    """Get appointment details by ID."""
    endpoint = f"locations/{GOHIGHLEVEL_LOCATION_ID}/appointments/{appointment_id}"
    
    response = make_api_request(endpoint)
    
    if response and 'appointment' in response:
        return response['appointment']
    return None

def get_appointments_by_contact(contact_id):
    """Get all appointments for a specific contact."""
    endpoint = f"locations/{GOHIGHLEVEL_LOCATION_ID}/appointments?contactId={contact_id}"
    
    response = make_api_request(endpoint)
    
    if response and 'appointments' in response:
        return response['appointments']
    return []

def get_available_slots(calendar_id, date):
    """Get available appointment slots for a specific date."""
    endpoint = f"locations/{GOHIGHLEVEL_LOCATION_ID}/calendars/{calendar_id}/available-slots?date={date}"
    
    response = make_api_request(endpoint)
    
    if response and 'availableSlots' in response:
        return response['availableSlots']
    return []
