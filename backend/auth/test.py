from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
sb = create_client(url, key)

try:
    # ĐÚNG: chọn schema qua .schema(...) và bảng qua .from_(...)
    res = sb.schema("auth_svc").from_("accounts").select("*").limit(1).execute()
    print("OK:", res.data)
except Exception as e:
    print("ERR:", e)
