"""Authentication router — Google OAuth via Supabase."""
import httpx
from fastapi import APIRouter, HTTPException, Depends
from app.config import settings
from app.middleware.auth_middleware import get_current_user
from app.utils.supabase_client import get_db

router = APIRouter(tags=["Authentication"])


@router.get("/login")
async def login():
    """Get Google OAuth URL from Supabase."""
    redirect_uri = f"{settings.BACKEND_URL}/api/auth/callback"
    auth_url = (
        f"{settings.SUPABASE_URL}/auth/v1/authorize?"
        f"provider=google&"
        f"redirect_to={settings.FRONTEND_URL}/auth/callback"
    )
    return {"auth_url": auth_url}


@router.post("/callback")
async def auth_callback(data: dict):
    """Handle OAuth callback — exchange code for session."""
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Missing access_token")

    try:
        # Verify token with Supabase
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers={"Authorization": f"Bearer {access_token}",
                         "apikey": settings.SUPABASE_ANON_KEY}
            )

            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")

            user_data = response.json()

        # Upsert user in our table
        db = get_db()
        user_record = {
            "id": user_data["id"],
            "email": user_data.get("email", ""),
            "full_name": user_data.get("user_metadata", {}).get("full_name", ""),
            "avatar_url": user_data.get("user_metadata", {}).get("avatar_url", ""),
            "provider": "google",
        }

        db.table("users").upsert(user_record, on_conflict="id").execute()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user_data["id"],
                "email": user_data.get("email", ""),
                "full_name": user_data.get("user_metadata", {}).get("full_name", ""),
                "avatar_url": user_data.get("user_metadata", {}).get("avatar_url", ""),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user


@router.post("/refresh")
async def refresh_token(data: dict):
    """Refresh an expired access token."""
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Missing refresh_token")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
                json={"refresh_token": refresh_token},
                headers={"apikey": settings.SUPABASE_ANON_KEY,
                         "Content-Type": "application/json"}
            )

            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Failed to refresh token")

            return response.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh error: {str(e)}")


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Log out the current user."""
    return {"message": "Logged out successfully"}
