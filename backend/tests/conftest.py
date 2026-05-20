import os
import time

# Set env vars before any app imports so Settings() initialisation doesn't fail.
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-32-chars-padded!!")

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from unittest.mock import MagicMock

TEST_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]
TEST_USER_ID = "user-abc-123"


def make_token(user_id: str = TEST_USER_ID) -> str:
    return jwt.encode(
        {"sub": user_id, "aud": "authenticated", "exp": int(time.time()) + 3600},
        TEST_JWT_SECRET,
        algorithm="HS256",
    )


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def client(mock_db, monkeypatch):
    import app.routers.jobs as jobs_module
    import app.auth as auth_module

    monkeypatch.setattr(jobs_module, "get_db", lambda: mock_db)
    monkeypatch.setattr(auth_module.settings, "supabase_jwt_secret", TEST_JWT_SECRET)

    from app.main import app
    return TestClient(app)
