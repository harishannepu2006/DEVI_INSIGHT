"""Supabase client utility."""
from supabase import create_client, Client
from app.config import settings


def get_supabase_client() -> Client:
    """Get Supabase client with service role key (full access)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_anon_client() -> Client:
    """Get Supabase client with anon key (limited access)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


# Singleton instance for service role
_supabase_client: Client | None = None


def get_db() -> Client:
    """Get or create singleton Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = get_supabase_client()
    return _supabase_client
