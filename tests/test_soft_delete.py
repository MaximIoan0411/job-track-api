def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


VALID_PAYLOAD = {
    "company": "Acme Corp",
    "position": "Backend Developer",
    "applied_date": "2025-01-15",
}


async def test_soft_delete_hides_from_default_list(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/applications/{app_id}", headers=auth_headers(user_token)
    )
    assert delete_resp.status_code == 204

    list_resp = await client.get("/applications", headers=auth_headers(user_token))
    assert list_resp.json()["items"] == []


async def test_soft_delete_visible_with_include_deleted(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]
    await client.delete(f"/applications/{app_id}", headers=auth_headers(user_token))

    list_resp = await client.get(
        "/applications?include_deleted=true", headers=auth_headers(user_token)
    )
    items = list_resp.json()["items"]
    assert len(items) == 1
    assert items[0]["deleted_at"] is not None


async def test_delete_already_deleted_application_fails(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]
    await client.delete(f"/applications/{app_id}", headers=auth_headers(user_token))

    second_delete = await client.delete(
        f"/applications/{app_id}", headers=auth_headers(user_token)
    )
    assert second_delete.status_code == 400


async def test_update_on_deleted_application_fails(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]
    await client.delete(f"/applications/{app_id}", headers=auth_headers(user_token))

    update_resp = await client.patch(
        f"/applications/{app_id}",
        json={"notes": "should fail"},
        headers=auth_headers(user_token),
    )
    assert update_resp.status_code == 400


async def test_status_change_on_deleted_application_fails(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]
    await client.delete(f"/applications/{app_id}", headers=auth_headers(user_token))

    status_resp = await client.patch(
        f"/applications/{app_id}/status",
        json={"status": "interview"},
        headers=auth_headers(user_token),
    )
    assert status_resp.status_code == 400


async def test_restore_brings_application_back(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]
    await client.delete(f"/applications/{app_id}", headers=auth_headers(user_token))

    restore_resp = await client.post(
        f"/applications/{app_id}/restore", headers=auth_headers(user_token)
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["deleted_at"] is None

    list_resp = await client.get("/applications", headers=auth_headers(user_token))
    assert len(list_resp.json()["items"]) == 1


async def test_restore_non_deleted_application_fails(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    restore_resp = await client.post(
        f"/applications/{app_id}/restore", headers=auth_headers(user_token)
    )
    assert restore_resp.status_code == 400