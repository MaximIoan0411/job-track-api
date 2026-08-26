def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


async def test_search_finds_matching_application(client, user_token):
    await client.post(
        "/applications",
        json={
            "company": "Acme Corp",
            "position": "Backend Developer",
            "applied_date": "2025-01-15",
            "notes": "Fully remote position, great team culture",
        },
        headers=auth_headers(user_token),
    )
    await client.post(
        "/applications",
        json={
            "company": "Other Co",
            "position": "Frontend Developer",
            "applied_date": "2025-01-16",
            "notes": "On-site, fast-paced startup",
        },
        headers=auth_headers(user_token),
    )

    response = await client.get("/applications/search?q=remote", headers=auth_headers(user_token))
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["company"] == "Acme Corp"


async def test_search_no_match_returns_empty(client, user_token):
    await client.post(
        "/applications",
        json={
            "company": "Acme Corp",
            "position": "Backend Developer",
            "applied_date": "2025-01-15",
        },
        headers=auth_headers(user_token),
    )

    response = await client.get(
        "/applications/search?q=blockchain", headers=auth_headers(user_token)
    )
    data = response.json()
    assert data["items"] == []
    assert data["has_more"] is False


async def test_cursor_pagination_walks_through_all_pages(client, user_token):
    for i in range(3):
        await client.post(
            "/applications",
            json={
                "company": f"Company {i}",
                "position": "Developer",
                "applied_date": "2025-01-15",
            },
            headers=auth_headers(user_token),
        )

    page1 = await client.get("/applications?limit=2", headers=auth_headers(user_token))
    page1_data = page1.json()
    assert len(page1_data["items"]) == 2
    assert page1_data["has_more"] is True

    page2 = await client.get(
        f"/applications?limit=2&cursor={page1_data['next_cursor']}",
        headers=auth_headers(user_token),
    )
    page2_data = page2.json()
    assert len(page2_data["items"]) == 1
    assert page2_data["has_more"] is False

    page1_ids = {item["id"] for item in page1_data["items"]}
    page2_ids = {item["id"] for item in page2_data["items"]}
    assert page1_ids.isdisjoint(page2_ids)  