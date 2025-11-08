from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

_client: Client | None = None

def get_supabase_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in env")
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _client