from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from .config import get_settings

settings = get_settings()
api_key_header = APIKeyHeader(name="X-Admin-Token", auto_error=True)

async def verify_admin_token(token: str = Security(api_key_header)):
    if token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return token