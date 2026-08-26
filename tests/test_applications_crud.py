def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


VALID_PAYLOAD = {
    "company": "Acme Corp",
    "position": "Backend Developer",
    "applied_date": "2025-01-15",
    "notes": "Applied through referral",
}


async def test_create_application_success(client, user_token):
    response = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    assert response.status_code == 201
    data = response.json()
    assert data["company"] == "Acme Corp"
    assert data["status"] == "applied"
    assert data["version"] == 1
    assert data["deleted_at"] is None


async def test_create_application_missing_required_field(client, user_token):
    payload = {"company": "Acme Corp"}  
    response = await client.post(
        "/applications", json=payload, headers=auth_headers(user_token)
    )
    assert response.status_code == 422


async def test_create_application_custom_fields_too_many_keys(client, user_token):
    payload = {
        **VALID_PAYLOAD,
        "custom_fields": {f"field_{i}": i for i in range(11)},  
    }
    response = await client.post(
        "/applications", json=payload, headers=auth_headers(user_token)
    )
    assert response.status_code == 422


async def test_create_application_custom_fields_invalid_value_type(client, user_token):
    payload = {**VALID_PAYLOAD, "custom_fields": {"nested": {"a": 1}}}
    response = await client.post(
        "/applications", json=payload, headers=auth_headers(user_token)
    )
    assert response.status_code == 422


async def test_list_applications(client, user_token):
    await client.post("/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token))
    await client.post(
        "/applications",
        json={**VALID_PAYLOAD, "company": "Other Co"},
        headers=auth_headers(user_token),
    )
    response = await client.get("/applications", headers=auth_headers(user_token))
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert "next_cursor" in data
    assert "has_more" in data


async def test_get_application_by_id(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    response = await client.get(f"/applications/{app_id}", headers=auth_headers(user_token))
    assert response.status_code == 200
    assert response.json()["id"] == app_id


async def test_get_application_not_found(client, user_token):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/applications/{fake_id}", headers=auth_headers(user_token))
    assert response.status_code == 404


async def test_update_application_partial(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    response = await client.patch(
        f"/applications/{app_id}",
        json={"notes": "Updated notes"},
        headers=auth_headers(user_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Updated notes"
    assert data["company"] == "Acme Corp"  
    assert data["version"] == 2 


async def test_update_application_no_real_change_does_not_bump_version(client, user_token):
    create_resp = await client.post(
        "/applications", json=VALID_PAYLOAD, headers=auth_headers(user_token)
    )
    app_id = create_resp.json()["id"]

    response = await client.patch(
        f"/applications/{app_id}",
        json={"company": "Acme Corp"},  
        headers=auth_headers(user_token),
    )
    assert response.status_code == 200
    assert response.json()["version"] == 1