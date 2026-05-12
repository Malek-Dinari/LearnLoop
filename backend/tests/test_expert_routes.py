"""Integration tests for /api/expert routes."""

import pytest


SAMPLE_CORRECTED = {
    "type": "mcq",
    "question": "What is photosynthesis?",
    "options": ["Light → energy", "Heat → work", "Mass → volume", "Sound → noise"],
    "correct_answer": "Light → energy",
    "explanation": "Photosynthesis converts light to chemical energy.",
    "difficulty": "easy",
}


@pytest.mark.asyncio
async def test_submit_anonymous_401(auth_client):
    resp = await auth_client.post(
        "/api/expert/corrections",
        json={"corrected_question": SAMPLE_CORRECTED, "topic_tags": ["photosynthesis"]},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_submit_regular_user_403(auth_client, make_user):
    user = await make_user(role="user")
    resp = await auth_client.post(
        "/api/expert/corrections",
        json={"corrected_question": SAMPLE_CORRECTED, "topic_tags": ["photosynthesis"]},
        headers=user["headers"],
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_submit_expert_creates_unapproved(auth_client, make_user):
    expert = await make_user(role="expert")
    resp = await auth_client.post(
        "/api/expert/corrections",
        json={"corrected_question": SAMPLE_CORRECTED, "topic_tags": ["Photosynthesis", "BIOLOGY"]},
        headers=expert["headers"],
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["approved"] is False
    assert body["topic_tags"] == ["biology", "photosynthesis"]
    assert body["expert_id"] == expert["id"]


@pytest.mark.asyncio
async def test_admin_submit_auto_approved(auth_client, make_user):
    admin = await make_user(role="admin")
    resp = await auth_client.post(
        "/api/expert/corrections",
        json={"corrected_question": SAMPLE_CORRECTED, "topic_tags": ["x"]},
        headers=admin["headers"],
    )
    assert resp.status_code == 201
    assert resp.json()["approved"] is True


@pytest.mark.asyncio
async def test_submit_invalid_corrected_422(auth_client, make_user):
    expert = await make_user(role="expert")
    resp = await auth_client.post(
        "/api/expert/corrections",
        json={"corrected_question": {"type": "mcq"}, "topic_tags": []},
        headers=expert["headers"],
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_expert_sees_own_only(auth_client, make_user):
    e1 = await make_user(role="expert")
    e2 = await make_user(role="expert")
    await auth_client.post(
        "/api/expert/corrections",
        json={"corrected_question": SAMPLE_CORRECTED, "topic_tags": ["a"]},
        headers=e1["headers"],
    )
    await auth_client.post(
        "/api/expert/corrections",
        json={"corrected_question": SAMPLE_CORRECTED, "topic_tags": ["b"]},
        headers=e2["headers"],
    )
    resp = await auth_client.get("/api/expert/corrections", headers=e1["headers"])
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["expert_id"] == e1["id"]


@pytest.mark.asyncio
async def test_list_admin_sees_all(auth_client, make_user):
    e = await make_user(role="expert")
    admin = await make_user(role="admin")
    await auth_client.post(
        "/api/expert/corrections",
        json={"corrected_question": SAMPLE_CORRECTED, "topic_tags": ["a"]},
        headers=e["headers"],
    )
    resp = await auth_client.get("/api/expert/corrections", headers=admin["headers"])
    assert resp.status_code == 200
    # admin sees expert's row + their own (none) → at least 1
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_approve_expert_403(auth_client, make_user):
    expert = await make_user(role="expert")
    other = await make_user(role="expert")
    create = await auth_client.post(
        "/api/expert/corrections",
        json={"corrected_question": SAMPLE_CORRECTED, "topic_tags": ["a"]},
        headers=expert["headers"],
    )
    cid = create.json()["id"]
    resp = await auth_client.patch(
        f"/api/expert/corrections/{cid}/approve",
        headers=other["headers"],
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_approve_admin_succeeds(auth_client, make_user):
    expert = await make_user(role="expert")
    admin = await make_user(role="admin")
    create = await auth_client.post(
        "/api/expert/corrections",
        json={"corrected_question": SAMPLE_CORRECTED, "topic_tags": ["a"]},
        headers=expert["headers"],
    )
    cid = create.json()["id"]
    resp = await auth_client.patch(
        f"/api/expert/corrections/{cid}/approve",
        headers=admin["headers"],
    )
    assert resp.status_code == 200
    assert resp.json()["approved"] is True

    # Idempotent: approving twice doesn't error
    again = await auth_client.patch(
        f"/api/expert/corrections/{cid}/approve",
        headers=admin["headers"],
    )
    assert again.status_code == 200
