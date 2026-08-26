import asyncio


async def test_concurrent_updates_one_succeeds_one_gets_conflict(
    client, user_token, make_concurrent_client
):
    create_resp = await client.post(
        "/applications",
        json={
            "company": "Acme Corp",
            "position": "Backend Developer",
            "applied_date": "2025-01-15",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    app_id = create_resp.json()["id"]

    client_a = await make_concurrent_client()
    client_b = await make_concurrent_client()
    headers = {"Authorization": f"Bearer {user_token}"}

    try:
        response_a, response_b = await asyncio.gather(
            client_a.patch(f"/applications/{app_id}", json={"notes": "from A"}, headers=headers),
            client_b.patch(f"/applications/{app_id}", json={"notes": "from B"}, headers=headers),
        )
    finally:
        await client_a.aclose()
        await client_b.aclose()

    statuses = {response_a.status_code, response_b.status_code}
    assert statuses == {200, 409}