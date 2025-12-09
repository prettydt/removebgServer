"""API key authentication middleware."""
import os
from typing import Optional
from fastapi import Header, HTTPException, status


def get_allowed_keys() -> set:
    """Get allowed API keys from environment variable."""
    keys_str = os.getenv('ALLOWED_KEYS', '')
    if not keys_str:
        return set()
    return set(key.strip() for key in keys_str.split(',') if key.strip())


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key from request header.
    
    Args:
        x_api_key: API key from x-api-key header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    allowed_keys = get_allowed_keys()
    
    if not allowed_keys:
        # If no keys configured, allow all requests (development mode)
        return x_api_key or "no-key-required"
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Please provide x-api-key header."
        )
    
    if x_api_key not in allowed_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return x_api_key
