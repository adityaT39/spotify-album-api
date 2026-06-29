def test_album_search(client, auth_headers):
    resp = client.get("/albums/search?q=test", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()[0]["name"]


def test_track_search(client, auth_headers):
    resp = client.get("/tracks/search?q=test", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()[0]["name"]
