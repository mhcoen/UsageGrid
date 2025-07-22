"""
Secure credential management utilities
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict
from cryptography.fernet import Fernet
import keyring

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manage API credentials securely"""
    
    KEYRING_SERVICE = "llm-costs"
    
    @classmethod
    def get_credential(cls, provider: str, credential_name: str, env_var: Optional[str] = None) -> str:
        """
        Get a credential with fallback order:
        1. System keychain (most secure)
        2. Environment variable
        3. Empty string
        """
        # Try keychain first
        try:
            keychain_value = keyring.get_password(cls.KEYRING_SERVICE, f"{provider}-{credential_name}")
            if keychain_value:
                logger.debug(f"Retrieved {provider} {credential_name} from keychain")
                return keychain_value
        except Exception as e:
            logger.debug(f"Keychain not available: {e}")
            
        # Fall back to environment variable
        if env_var:
            env_value = os.getenv(env_var, "")
            if env_value:
                logger.debug(f"Retrieved {provider} {credential_name} from environment")
                return env_value
                
        return ""
        
    @classmethod
    def set_credential(cls, provider: str, credential_name: str, value: str) -> bool:
        """Store a credential in the system keychain"""
        try:
            keyring.set_password(cls.KEYRING_SERVICE, f"{provider}-{credential_name}", value)
            logger.info(f"Stored {provider} {credential_name} in keychain")
            return True
        except Exception as e:
            logger.error(f"Failed to store credential: {e}")
            return False
            
    @classmethod
    def delete_credential(cls, provider: str, credential_name: str) -> bool:
        """Remove a credential from the system keychain"""
        try:
            keyring.delete_password(cls.KEYRING_SERVICE, f"{provider}-{credential_name}")
            logger.info(f"Removed {provider} {credential_name} from keychain")
            return True
        except Exception as e:
            logger.error(f"Failed to delete credential: {e}")
            return False
            
    @classmethod
    def list_providers(cls) -> list:
        """List providers with stored credentials"""
        # This is platform-dependent and may not work on all systems
        providers = set()
        try:
            # Try to get all stored credentials (platform-specific)
            import keyring.backends
            # Implementation depends on the keyring backend
            pass
        except:
            pass
        return list(providers)