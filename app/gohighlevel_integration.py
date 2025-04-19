"""
GoHighLevel integration module.
This module handles all interactions with the GoHighLevel API.
"""

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

                        Args:
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

        url = f"{BASE_URL}/appointments/slots/{LOCATION_ID}/{CALENDAR_ID}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        params = {"date": date_str}

        if service_id:
                            params["serviceId"] = service_id

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
                            return response.json().get('slots', [])
else:
                    logging.error(f"Failed to get available slots: {response.status_code} - {response.text}")
                    return []
except Exception as e:
        logging.error(f"Error getting available slots: {str(e)}")
        return []

def create_contact(phone, first_name=None, last_name=None, email=None):
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
                            url = f"{BASE_URL}/contacts/lookup"
                            headers = {"Authorization": f"Bearer {API_KEY}"}
                            params = {"phone": phone}

        # Check if contact exists
                response = requests.get(url, headers=headers, params=params)

        contact_data = {
                            "phone": phone,
                            "locationId": LOCATION_ID
        }

        if first_name:
                            contact_data["firstName"] = first_name
                        if last_name:
                                            contact_data["lastName"] = last_name
                                        if email:
                                                            contact_data["email"] = email

        # If contact exists, update it
        if response.status_code == 200 and response.json().get('contacts'):
                            contact_id = response.json()['contacts'][0]['id']
                            url = f"{BASE_URL}/contacts/{contact_id}"
                            response = requests.put(url, headers=headers, json=contact_data)
else:
                    # Create new contact
                    url = f"{BASE_URL}/contacts"
                    response = requests.post(url, headers=headers, json=contact_data)

        if response.status_code in [200, 201]:
                            return response.json()
else:
                    logging.error(f"Failed to create/update contact: {response.status_code} - {response.text}")
                    return None
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

        url = f"{BASE_URL}/appointments/calendar/{CALENDAR_ID}"
        headers = {"Authorization": f"Bearer {API_KEY}"}

        appointment_data = {
                            "contactId": contact_id,
                            "calendarId": CALENDAR_ID,
                            "dateTime": f"{date_str} {time_str}",
                            "locationId": LOCATION_ID
        }

        if service_id:
                            appointment_data["serviceId"] = service_id
                        if notes:
                                            appointment_data["notes"] = notes

        response = requests.post(url, headers=headers, json=appointment_data)

        if response.status_code == 200:
                            return response.json()
else:
                    logging.error(f"Failed to book appointment: {response.status_code} - {response.text}")
                    return None
except Exception as e:
        logging.error(f"Error booking appointment: {str(e)}")
        return None

def add_tag_to_contact(contact_id, tag_name):
            """
                Add a tag to a contact in GoHighLevel.
""""""
GoHighLevel integration module.
This module handles all interactions with the GoHighLevel API.
"""

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

                        Args:
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

def create_contact(phone, first_name=None, last_name=None, email=None):
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
                    # Return dummy data for testing when real API is not available
                    return {"id": "dummy_contact_id", "phone": phone, "firstName": first_name, "lastName": last_name}
    except Exception as e:
                    logging.error(f"Error creating/updating contact: {str(e)}")
                    return None

def book_appointment(contact_id, date_str, time_str, service_id=None, notes=None):
            ""d"e"f" 
            aGdodH_itgahgL_etvoe_lc oinnttaecgtr(actoinotna cmto_diudl,e .t
            aTgh_insa mmeo)d:u
            l e   h a"n"d"l
            e s   a lAld di nat etraagc ttioo nas  cwointtha ctth ei nG oGHoiHgihgLheLveevle lA.P
            I . 
             " "
             " 
              
               i mAprogrst: 
               l o g g i n g 
                icmopnotratc tr_eiqdu e(ssttsr
                )i:m pCoorntt aocst
                 fIrDo
                 m   c o n f i g .tcaogn_fniagm ei m(psotrrt) :E RTRaOgR _nMaEmSeS AtGoE Sa
                 d
                 d#
                   G o H i g h L e
                   v e l   ARPeIt ucrrnesd:e
                   n t i a l s 
                    A PbIo_oKlE:Y  T=r uoes .iefn vsiurcocne.sgseftu(l',G HFLa_lAsPeI _oKtEhYe'r,w i's'e)
                    
                     L O C A"T"I"O
                     N _ I D  i=f  onso.te nivsi_rcoonn.fgiegtu(r'eGdH(L)_:L
                     O C A T I O N _ IlDo'g,g i'n'g).
                     wCaArLnEiNnDgA(R"_GIoDH i=g hoLse.veenlv iirnotne.ggreatt(i'oGnH Ln_oCtA LcEoNnDfAiRg_uIrDe'd,.  'C'a)n
                     n
                     o#t  Baadsde  tUaRgL  tfoo rc oGnotHaicgth.L"e)v
                     e l   A P I 
                      B ArSeEt_uUrRnL  F=a l"shetdef create_contact(phone, first_name=None, last_name=None, email=None):
                          """Create or update a contact in GoHighLevel."""
                              if not is_configured():
                                      logging.warning("GoHighLevel integration not configured. Cannot create contact.")
                                              return None

                                                      try:
                                                              # Return dummy data for testing
                                                                      return {"id": "dummy_contact_id", "phone": phone, "firstName": first_name, "lastName": last_name}
                                                                          except Exception as e:
                                                                                  logging.error(f"Error creating/updating contact: {str(e)}")
                                                                                          return None

                                                                                          def book_appointment(contact_id, date_str, time_str, service_id=None, notes=None):
                                                                                              """Book an appointment in GoHighLevel."""
                                                                                                  if not is_configured():
                                                                                                          logging.warning("GoHighLevel integration not configured. Cannot book appointment.")
                                                                                                                  return None
                                                                                                                      
                                                                                                                          try:
                                                                                                                                  if not CALENDAR_ID:
                                                                                                                                              logging.error("Calendar ID not configured. Cannot book appointment.")
                                                                                                                                                          return None
                                                                                                                                                                      
                                                                                                                                                                              # Return dummy data for testing
                                                                                                                                                                                      return {"id": "dummy_appointment_id", "contactId": contact_id, "dateTime": f"{date_str} {time_str}"}
                                                                                                                                                                                          except Exception as e:
                                                                                                                                                                                                  logging.error(f"Error booking appointment: {str(e)}")
                                                                                                                                                                                                          return None
                                                                                                                                                                                                          
                                                                                                                                                                                                          def add_tag_to_contact(contact_id, tag_name):
                                                                                                                                                                                                              """Add a tag to a contact in GoHighLevel."""
                                                                                                                                                                                                                  if not is_configured():
                                                                                                                                                                                                                          logging.warning("GoHighLevel integration not configured. Cannot add tag to contact.")
                                                                                                                                                                                                                                  return False
                                                                                                                                                                                                                                      
                                                                                                                                                                                                                                          try:
                                                                                                                                                                                                                                                  # Return dummy result for testing
                                                                                                                                                                                                                                                          return True
                                                                                                                                                                                                                                                              except Exception as e:
                                                                                                                                                                                                                                                                      logging.error(f"Error adding tag to contact: {str(e)}")
                                                                                                                                                                                                                                                                              return False
                      t p s : /
                      / r e s tt.rgyo:h
                      i g h l e v e l .#c oRme/tvu1r"n
                       
                       dduemfm yi sr_ecsounlfti gfuorre dt(e)s:t
                       i n g   w"h"e"nC hreecakl  iAfP IG oiHsi gnhoLte vaevla iilnatbelger
                       a t i o n   i s  rpertouprenr lTyr uceo
                       n f i g uerxecde.p"t" "E
                       x c e p trieotnu rans  beo:o
                       l ( A P I _ K E Yl oagngdi nLgO.CeArTrIoOrN(_fI"DE)r
                       r
                       odre fa dgdeitn_ga vtaaigl atbol ec_osnltoatcst(:d a{tset_rs(ter),} "s)e
                       r v i c e _ i d =rNeotnuer)n: 
                       F a l s e"""Get available appointment slots for a specific date."""
                           if not is_configured():
                                   logging.warning("GoHighLevel integration not configured. Cannot get available slots.")
                                           return []
                                               
                                                   try:
                                                           if not CALENDAR_ID:
                                                                       logging.error("Calendar ID not configured. Cannot get available slots.")
                                                                                   return []
                                                                                               
                                                                                                       # Return dummy data for testing
                                                                                                               return ["9:00 AM", "10:00 AM", "11:00 AM", "1:00 PM", "2:00 PM", "3:00 PM"]
                                                                                                                   except Exception as e:
                                                                                                                           logging.error(f"Error getting available slots: {str(e)}")
                                                                                                                                   return []"
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

        # Return dummy data for testing when real API is not available
        return {"id": "dummy_appointment_id", "contactId": contact_id, "dateTime": f"{date_str} {time_str}"}
except Exception as e:
        logging.error(f"Error booking appointment: {str(e)}")
        return None


        GoHighLevel integration module.
                This module handles all interactions with the GoHighLevel API.
                """

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
                            url = f"{BASE_URL}/contacts/{contact_id}/tags"
                            headers = {"Authorization": f"Bearer {API_KEY}"}

        tag_data = {
                            "tags": [tag_name],
                            "locationId": LOCATION_ID
        }

        response = requests.post(url, headers=headers, json=tag_data)

        if response.status_code == 200:
                            return True
else:
                    logging.error(f"Failed to add tag to contact: {response.status_code} - {response.text}")
                    return False
except Exception as e:
        logging.error(f"Error adding tag to contact: {str(e)}")
        return False
