import unittest
from unittest.mock import patch, MagicMock
from app.gohighlevel_integration import (
    is_configured,
    create_contact,
    create_appointment,
    get_available_slots
)

class TestGoHighLevelIntegration(unittest.TestCase):
    
    @patch('app.gohighlevel_integration.API_KEY', 'test_key')
    @patch('app.gohighlevel_integration.LOCATION_ID', 'test_location')
    def test_is_configured_with_credentials(self):
        """Test that is_configured returns True when credentials are set"""
        self.assertTrue(is_configured())
    
    @patch('app.gohighlevel_integration.API_KEY', '')
    @patch('app.gohighlevel_integration.LOCATION_ID', '')
    def test_is_configured_without_credentials(self):
        """Test that is_configured returns False when credentials are not set"""
        self.assertFalse(is_configured())
    
    @patch('app.gohighlevel_integration.is_configured')
    def test_create_contact_with_configuration(self, mock_is_configured):
        """Test that create_contact works when configured"""
        mock_is_configured.return_value = True
        contact_data = {'phone': '1234567890', 'name': 'Test User'}
        result = create_contact(contact_data)
        self.assertIsNotNone(result)
    
    @patch('app.gohighlevel_integration.is_configured')
    def test_create_contact_without_configuration(self, mock_is_configured):
        """Test that create_contact returns dummy data when not configured"""
        mock_is_configured.return_value = False
        contact_data = {'phone': '1234567890', 'name': 'Test User'}
        result = create_contact(contact_data)
        self.assertEqual(result, "contact_123")
    
    @patch('app.gohighlevel_integration.is_configured')
    @patch('app.gohighlevel_integration.CALENDAR_ID', 'test_calendar')
    def test_create_appointment_with_configuration(self, mock_is_configured):
        """Test that create_appointment works when configured"""
        mock_is_configured.return_value = True
        appointment_data = {'date': '2025-04-20', 'time': '10:00 AM'}
        result = create_appointment(appointment_data)
        self.assertIsNotNone(result)
    
    @patch('app.gohighlevel_integration.is_configured')
    @patch('app.gohighlevel_integration.CALENDAR_ID', '')
    def test_create_appointment_without_calendar(self, mock_is_configured):
        """Test that create_appointment returns None when calendar is not configured"""
        mock_is_configured.return_value = True
        appointment_data = {'date': '2025-04-20', 'time': '10:00 AM'}
        result = create_appointment(appointment_data)
        self.assertIsNone(result)
    
    @patch('app.gohighlevel_integration.is_configured')
    def test_get_available_slots_with_configuration(self, mock_is_configured):
        """Test that get_available_slots returns slots when configured"""
        mock_is_configured.return_value = True
        result = get_available_slots()
        self.assertTrue(len(result) > 0)
    
    @patch('app.gohighlevel_integration.is_configured')
    def test_get_available_slots_without_configuration(self, mock_is_configured):
        """Test that get_available_slots returns dummy slots when not configured"""
        mock_is_configured.return_value = False
        result = get_available_slots()
        self.assertEqual(len(result), 4)  # Should return 4 dummy slots

if __name__ == '__main__':
    unittest.main()
