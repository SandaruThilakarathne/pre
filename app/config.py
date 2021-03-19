from dataclasses import dataclass
import os

@dataclass
class Config():
    AUTH_SERVICE_URL: str = os.environ.get("AUTH_SERVICE_URL")
    HTTPS: bool = False
    SQLALCHEMY_DATABASE_URI: str = os.environ.get("SQLALCHEMY_DATABASE_URI")
    SCRIPT_NAME: str = ""
    JWT_SIGNING_ALGORITHM: str = "ES256"
    AUTHORIZED_ROLES: str = "Developer"
    MAX_REQUEST_SIZE: int = 16 * 1024 * 1024

    MAX_LIMIT_OPPORTUNITIES: int = 1000
    TENANT: str = None