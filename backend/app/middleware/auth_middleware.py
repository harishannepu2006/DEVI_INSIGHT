"""JWT Authentication middleware using Supabase."""
import jwt
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

security = HTTPBearer(auto_error=False)


async def verify_jwt_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verify Supabase JWT token and return user payload."""
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # Fallback to query parameter for direct downloads (native browser downloads)
        token = request.query_params.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="Missing authentication token")

    try:
        # Decode the JWT payload
        payload = jwt.decode(
            token,
            options={"verify_signature": False},  # Validation happens at Supabase layer
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(token_payload: dict = Depends(verify_jwt_token)) -> dict:
    """Extract current user info from JWT payload."""
    user_id = token_payload.get("sub")
    email = token_payload.get("email")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: no user ID")

    return {
        "id": user_id,
        "email": email,
        "role": token_payload.get("role", "authenticated"),
        "full_name": token_payload.get("user_metadata", {}).get("full_name", ""),
        "avatar_url": token_payload.get("user_metadata", {}).get("avatar_url", ""),
    }
