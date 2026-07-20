import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
FAKE_USERNAME = os.getenv("FAKE_USERNAME")
FAKE_PASSWORD = os.getenv("FAKE_PASSWORD")

required_env_vars = ["SECRET_KEY", "FAKE_USERNAME", "FAKE_PASSWORD"]
for var in required_env_vars:
    if not os.getenv(var):
        raise RuntimeError(f"Missing environment variable: {var}")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60