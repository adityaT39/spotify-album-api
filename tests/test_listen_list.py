def test_listen_list_add_list_remove(client, auth_headers):
    added = client.post(
        "/listen-list",
        json={"item_type": "track", "spotify_id": "x1"},
        headers=auth_headers,
    )
    assert added.status_code == 201
    item_id = added.json()["id"]

    listed = client.get("/listen-list", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    removed = client.delete(f"/listen-list/{item_id}", headers=auth_headers)
    assert removed.status_code == 204
    assert client.get("/listen-list", headers=auth_headers).json() == []
