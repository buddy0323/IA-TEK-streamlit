import streamlit as st
import json
import base64
import hashlib
from datetime import datetime, timedelta
import logging

log = logging.getLogger(__name__)

# Cookie configuration
COOKIE_NAME = "ia_tek_session"
COOKIE_EXPIRY_DAYS = 7  # Cookie will expire after 7 days
SECRET_KEY = "your-secret-key-here"  # Change this to a secure secret key

def _encode_cookie(data: dict) -> str:
    """Encode cookie data to a secure string."""
    try:
        # Convert data to JSON and encode to base64
        json_data = json.dumps(data)
        encoded = base64.b64encode(json_data.encode()).decode()
        # Add a signature
        signature = hashlib.sha256(f"{encoded}{SECRET_KEY}".encode()).hexdigest()
        return f"{encoded}.{signature}"
    except Exception as e:
        log.error(f"Error encoding cookie: {e}")
        return None

def _decode_cookie(encoded_data: str) -> dict:
    """Decode cookie data from a secure string."""
    try:
        if not encoded_data or '.' not in encoded_data:
            return None
        
        encoded, signature = encoded_data.split('.')
        # Verify signature
        if hashlib.sha256(f"{encoded}{SECRET_KEY}".encode()).hexdigest() != signature:
            log.warning("Invalid cookie signature")
            return None
        
        # Decode base64 and parse JSON
        decoded = base64.b64decode(encoded).decode()
        return json.loads(decoded)
    except Exception as e:
        log.error(f"Error decoding cookie: {e}")
        return None

def set_session_cookie(data: dict):
    """Set a session cookie with the given data."""
    try:
        # Add expiry timestamp
        data['expires'] = (datetime.now() + timedelta(days=COOKIE_EXPIRY_DAYS)).timestamp()
        encoded = _encode_cookie(data)
        if encoded:
            # Set cookie using Streamlit's query_params
            st.query_params["session"] = encoded
    except Exception as e:
        log.error(f"Error setting session cookie: {e}")

def get_session_cookie() -> dict:
    """Get and validate the session cookie."""
    try:
        # Get cookie from query params
        params = st.query_params
        if 'session' not in params:
            return None
        
        encoded = params["session"]
        data = _decode_cookie(encoded)
        
        # Check if cookie has expired
        if data and 'expires' in data:
            if datetime.now().timestamp() > data['expires']:
                log.info("Session cookie expired")
                return None
            return data
        return None
    except Exception as e:
        log.error(f"Error getting session cookie: {e}")
        return None

def clear_session_cookie():
    """Clear the session cookie."""
    try:
        # Clear all query parameters
        st.query_params.clear()
    except Exception as e:
        log.error(f"Error clearing session cookie: {e}") 