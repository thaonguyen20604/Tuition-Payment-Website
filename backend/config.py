# # config.py
# import os
# from pathlib import Path
# from dotenv import load_dotenv

# # Load .env từ thư mục gốc project
# BASE_DIR = Path(__file__).resolve().parent# quay lên /backend
# ENV_PATH = BASE_DIR / ".env"

# if ENV_PATH.exists():
#     load_dotenv(dotenv_path=ENV_PATH)
#     print(f"[Config] Loaded env from {ENV_PATH}")
# else:
#     print(f"[Config] WARNING: .env not found at {ENV_PATH}, fallback to system env")

# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
# STUDENTFEE_SVC_URL = os.getenv("STUDENTFEE_SVC_URL")
# USER_SVC_URL = os.getenv("USER_SVC_URL")


# JWT_SECRET = os.getenv("JWT_SECRET", "default-secret")
# JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
# JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env từ thư mục gốc project
BASE_DIR = Path(__file__).resolve().parent# quay lên /backend
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
    print(f"[Config] Loaded env from {ENV_PATH}")
else:
    print(f"[Config] WARNING: .env not found at {ENV_PATH}, fallback to system env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

JWT_SECRET = os.getenv("JWT_SECRET", "default-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


# ========================
# Service Endpoints
# ========================
AUTH_SVC_URL: str = os.getenv("AUTH_SVC_URL", "http://localhost:8001")
USER_SVC_URL: str = os.getenv("USER_SVC_URL", "http://localhost:8002")
STUDENTFEE_SVC_URL: str = os.getenv("STUDENTFEE_SVC_URL", "http://localhost:8003")
PAYMENT_SVC_URL: str = os.getenv("PAYMENT_SVC_URL", "http://localhost:8004")

# ========================
# Mailer (SMTP)
# ========================
MAIL_FROM: str = os.getenv("MAIL_FROM", "no-reply@example.com")
SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASS: str = os.getenv("SMTP_PASS", "")

# ========================
# Helper for safe debug
# ========================
def dump_config_safe():
    """In ra config an toàn (ẩn secret/password)."""
    return {
        "SUPABASE_URL": SUPABASE_URL,
        "JWT_ALGORITHM": JWT_ALGORITHM,
        "JWT_EXPIRE_MINUTES": JWT_EXPIRE_MINUTES,
        "AUTH_SVC_URL": AUTH_SVC_URL,
        "USER_SVC_URL": USER_SVC_URL,
        "STUDENTFEE_SVC_URL": STUDENTFEE_SVC_URL,
        "PAYMENT_SVC_URL": PAYMENT_SVC_URL,
        "MAIL_FROM": MAIL_FROM,
        "SMTP_HOST": SMTP_HOST,
        "SMTP_PORT": SMTP_PORT,
        "SMTP_USER": SMTP_USER,
        "SMTP_PASS": "***" if SMTP_PASS else None,
    }