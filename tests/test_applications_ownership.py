def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


VALID_PAYLOAD = {
    "company": "Acme Corp",
    "position": "Backend Developer",
    "applied_date": "2025-01-15",
}


async def test_user_cannot_get_other_users_application(client, user_token, user2_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    response = await client.get(f"/applications/{app_id}", headers=auth_headers(user2_token))
    assert response.status_code == 404


async def test_user_cannot_update_other_users_application(client, user_token, user2_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    response = await client.patch(
        f"/applications/{app_id}",
        json={"notes": "hacked"},
        headers=auth_headers(user2_token),
    )
    assert response.status_code == 404


async def test_user_cannot_delete_other_users_application(client, user_token, user2_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    response = await client.delete(f"/applications/{app_id}", headers=auth_headers(user2_token))
    assert response.status_code == 404


async def test_user_cannot_change_status_of_other_users_application(
    client, user_token, user2_token
):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    response = await client.patch(
        f"/applications/{app_id}/status",
        json={"status": "interview"},
        headers=auth_headers(user2_token),
    )
    assert response.status_code == 404


async def test_user_only_sees_own_applications_in_list(client, user_token, user2_token):
    await client.post("/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token))
    await client.post(
        "/applications",
        json={**VALID_PAYLOAD, "company": "User2 Co"},
        headers=auth_headers(user2_token),
    )

    response = await client.get("/applications", headers=auth_headers(user_token))
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["company"] == "Acme Corp"


async def test_user_cannot_see_other_users_application_history(
    client, user_token, user2_token
):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    response = await client.get(
        f"/applications/{app_id}/history", headers=auth_headers(user2_token)
    )
    assert response.status_code == 404