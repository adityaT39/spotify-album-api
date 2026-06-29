def test_login_redirects_to_spotify(client):
    resp = client.get("/auth/spotify/login", follow_redirects=False)
    assert resp.status_code == 307
    assert "accounts.spotify.com/authorize" in resp.headers["location"]


def test_protected_endpoint_requires_auth(client):
    # No bearer token -> rejected (401 Unauthorized / 403 Forbidden).
    resp = client.get("/ratings")
    assert resp.status_code in (401, 403)


def test_bad_token_rejected(client):
    resp = client.get("/ratings", headers={"Authorization": "Bearer nonsense"})
    assert resp.status_code == 401
