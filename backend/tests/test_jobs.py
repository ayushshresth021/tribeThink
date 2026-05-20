from unittest.mock import MagicMock, patch

from tests.conftest import make_token, TEST_USER_ID


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {make_token()}"}


# ── Issue #1: Auth ──────────────────────────────────────────────────────────

def test_create_job_unauthenticated_returns_401(client):
    resp = client.post("/jobs", json={"video_storage_path": f"{TEST_USER_ID}/vid.mp4", "duration_seconds": 10})
    assert resp.status_code == 401


def test_create_job_invalid_token_returns_401(client):
    resp = client.post(
        "/jobs",
        json={"video_storage_path": f"{TEST_USER_ID}/vid.mp4", "duration_seconds": 10},
        headers={"Authorization": "Bearer not.a.real.token"},
    )
    assert resp.status_code == 401


# ── Issue #2: Video Upload → Job Created ────────────────────────────────────

def test_create_job_returns_job_id_with_pending_status(client, mock_db):
    fake_job_id = "job-uuid-001"
    mock_db.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": fake_job_id, "status": "pending"}
    ]

    resp = client.post(
        "/jobs",
        json={"video_storage_path": f"{TEST_USER_ID}/vid.mp4", "duration_seconds": 10},
        headers=_auth_headers(),
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["job_id"] == fake_job_id
    # Verify the insert was called with status=pending
    insert_call = mock_db.table.return_value.insert.call_args[0][0]
    assert insert_call["status"] == "pending"
    assert insert_call["user_id"] == TEST_USER_ID


def test_create_job_rejects_video_over_30_seconds(client):
    resp = client.post(
        "/jobs",
        json={"video_storage_path": f"{TEST_USER_ID}/long.mp4", "duration_seconds": 30.1},
        headers=_auth_headers(),
    )
    assert resp.status_code == 422


def test_create_job_rejects_path_outside_user_prefix(client):
    resp = client.post(
        "/jobs",
        json={"video_storage_path": "other-user/vid.mp4", "duration_seconds": 10},
        headers=_auth_headers(),
    )
    assert resp.status_code == 403


def test_get_job_returns_job_data_for_owner(client, mock_db):
    fake_job = {
        "id": "job-uuid-001",
        "status": "pending",
        "video_storage_path": f"{TEST_USER_ID}/vid.mp4",
        "created_at": "2026-05-19T00:00:00",
        "completed_at": None,
        "error_message": None,
    }
    (
        mock_db.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .single.return_value
        .execute.return_value
        .data
    ) = fake_job

    resp = client.get("/jobs/job-uuid-001", headers=_auth_headers())

    assert resp.status_code == 200
    assert resp.json()["id"] == "job-uuid-001"
    assert resp.json()["status"] == "pending"


def test_get_job_returns_404_when_not_found(client, mock_db):
    (
        mock_db.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .single.return_value
        .execute.return_value
        .data
    ) = None

    resp = client.get("/jobs/nonexistent", headers=_auth_headers())

    assert resp.status_code == 404


# ── Issue #3: TribeV2 Inference Worker ──────────────────────────────────────

def _mock_db_for_create(mock_db, job_id: str = "job-uuid-001"):
    mock_db.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": job_id, "status": "pending"}
    ]


def test_create_job_spawns_inference(client, mock_db):
    _mock_db_for_create(mock_db)

    with patch("app.routers.jobs.spawn_inference_job") as mock_spawn:
        resp = client.post(
            "/jobs",
            json={"video_storage_path": f"{TEST_USER_ID}/vid.mp4", "duration_seconds": 15.0},
            headers=_auth_headers(),
        )

    assert resp.status_code == 201
    mock_spawn.assert_called_once_with("job-uuid-001", f"{TEST_USER_ID}/vid.mp4")


def test_create_job_spawns_with_correct_job_id(client, mock_db):
    specific_id = "specific-job-xyz"
    _mock_db_for_create(mock_db, job_id=specific_id)

    with patch("app.routers.jobs.spawn_inference_job") as mock_spawn:
        client.post(
            "/jobs",
            json={"video_storage_path": f"{TEST_USER_ID}/clip.mp4", "duration_seconds": 10.0},
            headers=_auth_headers(),
        )

    job_id_passed = mock_spawn.call_args[0][0]
    assert job_id_passed == specific_id


def test_create_job_returns_job_id_even_when_spawn_raises(client, mock_db):
    _mock_db_for_create(mock_db)

    with patch("app.routers.jobs.spawn_inference_job", side_effect=Exception("Modal unavailable")):
        resp = client.post(
            "/jobs",
            json={"video_storage_path": f"{TEST_USER_ID}/vid.mp4", "duration_seconds": 10.0},
            headers=_auth_headers(),
        )

    assert resp.status_code == 201
    assert "job_id" in resp.json()
