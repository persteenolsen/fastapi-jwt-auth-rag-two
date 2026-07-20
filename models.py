from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# -----------------------------
# MODELS
# -----------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PromptRequest(BaseModel):
    prompt: str

class URLRequest(BaseModel):
    url: str
