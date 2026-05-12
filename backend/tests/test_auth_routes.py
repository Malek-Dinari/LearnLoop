"""Integration tests for /api/auth routes."""

import pytest
import jwt as pyjwt

from app.config import settings


@pytest.mark.asyncio
async def test_signup_returns_token_and_user(auth_client):
    resp = await auth_client.post(
        "/api/auth/signup",
        json={"email": "alice@test.com", "password": "longpassword"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "alice@test.com"
    assert data["user"]["role"] == "user"
    payload = pyjwt.decode(
        data["access_token"], settings.jwt_secret, algorithms=[settings.jwt_algorithm]
    )
    assert payload["sub"] == data["user"]["id"]


@pytest.mark.asyncio
async def test_signup_duplicate_email_409(auth_client):
    body = {"email": "dup@test.com", "password": "longpassword"}
    r1 = await auth_client.post("/api/auth/signup", json=body)
    assert r1.status_code == 201
    r2 = await auth_client.post("/api/auth/signup", json=body)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_signup_invalid_email_422(auth_client):
    resp = await auth_client.post(
        "/api/auth/signup", json={"email": "not-an-email", "password": "longpassword"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_short_password_422(auth_client):
    resp = await auth_client.post(
        "/api/auth/signup", json={"email": "a@test.com", "password": "short"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_valid_credentials(auth_client):
    await auth_client.post(
        "/api/auth/signup",
        json={"email": "bob@test.com", "password": "longpassword"},
    )
    resp = await auth_client.post(
        "/api/auth/login",
        json={"email": "bob@test.com", "password": "longpassword"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password_401(auth_client):
    await auth_client.post(
        "/api/auth/signup",
        json={"email": "carol@test.com", "password": "longpassword"},
    )
    resp = await auth_client.post(
        "/api/auth/login",
        json={"email": "carol@test.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert "wrong email or password" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_unknown_email_401_same_message(auth_client):
    """No email-enumeration leak: unknown email returns same status + message."""
    resp = await auth_client.post(
        "/api/auth/login",
        json={"email": "ghost@test.com", "password": "longpassword"},
    )
    assert resp.status_code == 401
    assert "wrong email or password" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_me_requires_token_401(auth_client):
    resp = await auth_client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_returns_user(auth_client, make_user):
    user = await make_user(email="dave@test.com", role="user")
    resp = await auth_client.get("/api/auth/me", headers=user["headers"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "dave@test.com"
    assert body["role"] == "user"


@pytest.mark.asyncio
async def test_me_with_invalid_token_401(auth_client):
    resp = await auth_client.get(
        "/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401
