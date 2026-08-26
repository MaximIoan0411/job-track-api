def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


VALID_PAYLOAD = {
    "company": "Acme Corp",
    "position": "Backend Developer",
    "applied_date": "2025-01-15",
}


async def test_change_status_updates_value_and_creates_audit_entry(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    response = await client.patch(
        f"/applications/{app_id}/status",
        json={"status": "interview"},
        headers=auth_headers(user_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "interview"

    history_resp = await client.get(
        f"/applications/{app_id}/history", headers=auth_headers(user_token)
    )
    history = history_resp.json()
    assert any(
        entry["action"] == "status_changed"
        and entry["changes"]["status"]["old"] == "applied"
        and entry["changes"]["status"]["new"] == "interview"
        for entry in history
    )


async def test_change_status_to_same_value_does_not_duplicate_audit(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    await client.patch(
        f"/applications/{app_id}/status",
        json={"status": "applied"},  # deja e "applied"
        headers=auth_headers(user_token),
    )

    history_resp = await client.get(
        f"/applications/{app_id}/history", headers=auth_headers(user_token)
    )
    status_changes = [e for e in history_resp.json() if e["action"] == "status_changed"]
    assert len(status_changes) == 0


async def test_full_lifecycle_produces_expected_audit_trail(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    await client.patch(
        f"/applications/{app_id}/status",
        json={"status": "interview"},
        headers=auth_headers(user_token),
    )
    await client.delete(f"/applications/{app_id}", headers=auth_headers(user_token))
    await client.post(f"/applications/{app_id}/restore", headers=auth_headers(user_token))

    history_resp = await client.get(
        f"/applications/{app_id}/history", headers=auth_headers(user_token)
    )
    actions = [entry["action"] for entry in history_resp.json()]
    assert actions == ["restored", "soft_deleted", "status_changed", "created"]