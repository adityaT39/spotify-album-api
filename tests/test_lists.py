def test_create_list_add_items_and_read_back(client, auth_headers):
    created = client.post(
        "/lists",
        json={"name": "Faves", "description": "My favourites"},
        headers=auth_headers,
    )
    assert created.status_code == 201
    list_id = created.json()["id"]

    album = client.post(
        f"/lists/{list_id}/items",
        json={"item_type": "album", "spotify_id": "a1"},
        headers=auth_headers,
    )
    assert album.status_code == 201

    track = client.post(
        f"/lists/{list_id}/items",
        json={"item_type": "track", "spotify_id": "t1"},
        headers=auth_headers,
    )
    assert track.status_code == 201

    detail = client.get(f"/lists/{list_id}", headers=auth_headers)
    assert detail.status_code == 200
    body = detail.json()
    assert body["name"] == "Faves"
    assert len(body["items"]) == 2


def test_duplicate_item_conflicts(client, auth_headers):
    list_id = client.post(
        "/lists", json={"name": "L"}, headers=auth_headers
    ).json()["id"]
    item = {"item_type": "album", "spotify_id": "a1"}
    first = client.post(f"/lists/{list_id}/items", json=item, headers=auth_headers)
    assert first.status_code == 201
    second = client.post(f"/lists/{list_id}/items", json=item, headers=auth_headers)
    assert second.status_code == 409


def test_missing_list_returns_404(client, auth_headers):
    assert client.get("/lists/999", headers=auth_headers).status_code == 404
