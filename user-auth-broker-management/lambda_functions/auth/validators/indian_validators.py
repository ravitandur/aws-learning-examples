"""
Indian market specific validators for user registration
Includes phone number validation and complete Indian states list
"""

import re
from typing import Dict, List, Optional

# Complete list of Indian states and union territories
INDIAN_STATES = [
    # States (28)
    "Andhra Pradesh",
    "Arunachal Pradesh", 
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    # Union Territories (8)
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry"
]

# Indian phone number pattern: +91 followed by 10 digits starting with 6-9
INDIAN_PHONE_PATTERN = r'^\+91[6-9]\d{9}$'

def validate_indian_phone_number(phone_number: str) -> Dict[str, any]:
    """
    Validate Indian phone number format
    
    Args:
        phone_number: Phone number to validate
        
    Returns:
        Dict with validation result and message
    """
    if not phone_number:
        return {
            "valid": False,
            "message": "Phone number is required"
        }
    
    if not re.match(INDIAN_PHONE_PATTERN, phone_number):
        return {
            "valid": False,
            "message": "Phone number must be in format +91xxxxxxxxxx with digits 6-9 as first digit"
        }
    
    return {
        "valid": True,
        "message": "Valid Indian phone number"
    }

def validate_indian_state(state: str) -> Dict[str, any]:
    """
    Validate Indian state or union territory
    
    Args:
        state: State name to validate
        
    Returns:
        Dict with validation result and message
    """
    if not state:
        return {
            "valid": False,
            "message": "State is required"
        }
    
    if state not in INDIAN_STATES:
        return {
            "valid": False,
            "message": f"Invalid state. Must be one of: {', '.join(INDIAN_STATES)}"
        }
    
    return {
        "valid": True,
        "message": "Valid Indian state"
    }

def get_indian_states() -> List[str]:
    """
    Get complete list of Indian states and union territories
    
    Returns:
        List of all Indian states and union territories
    """
    return INDIAN_STATES.copy()

def validate_user_registration_data(user_data: Dict[str, str]) -> Dict[str, any]:
    """
    Validate complete user registration data for Indian users
    
    Args:
        user_data: Dictionary containing user registration data
        
    Returns:
        Dict with validation result and any error messages
    """
    errors = []
    
    # Validate phone number
    phone_validation = validate_indian_phone_number(user_data.get('phone_number', ''))
    if not phone_validation['valid']:
        errors.append(phone_validation['message'])
    
    # Validate state
    state_validation = validate_indian_state(user_data.get('state', ''))
    if not state_validation['valid']:
        errors.append(state_validation['message'])
    
    # Validate full name
    full_name = user_data.get('full_name', '').strip()
    if not full_name or len(full_name) < 2:
        errors.append("Full name must be at least 2 characters long")
    
    # Validate email format (basic)
    email = user_data.get('email', '').strip()
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or not re.match(email_pattern, email):
        errors.append("Valid email address is required")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }