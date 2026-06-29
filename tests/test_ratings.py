from app.models import Rating, User


def test_create_and_list_rating(client, auth_headers):
    payload = {
        "item_type": "album",
        "spotify_id": "abc",
        "rating": 8,
        "review": "Great record",
    }
    resp = client.post("/ratings", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["rating"] == 8
    assert body["title"]  # enriched from (mocked) Spotify
    assert body["artist"] == "Test Artist"

    listed = client.get("/ratings", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_duplicate_rating_conflicts(client, auth_headers):
    payload = {"item_type": "album", "spotify_id": "dup", "rating": 7}
    first = client.post("/ratings", json=payload, headers=auth_headers)
    assert first.status_code == 201
    second = client.post("/ratings", json=payload, headers=auth_headers)
    assert second.status_code == 409


def test_rating_out_of_range_is_rejected(client, auth_headers):
    payload = {"item_type": "album", "spotify_id": "abc", "rating": 99}
    resp = client.post("/ratings", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_update_and_delete_rating(client, auth_headers):
    created = client.post(
        "/ratings",
        json={"item_type": "track", "spotify_id": "t1", "rating": 5},
        headers=auth_headers,
    )
    rating_id = created.json()["id"]

    updated = client.patch(
        f"/ratings/{rating_id}", json={"rating": 10}, headers=auth_headers
    )
    assert updated.status_code == 200
    assert updated.json()["rating"] == 10

    deleted = client.delete(f"/ratings/{rating_id}", headers=auth_headers)
    assert deleted.status_code == 204
    assert client.get("/ratings", headers=auth_headers).json() == []


def test_cannot_touch_another_users_rating(client, auth_headers, db_session):
    other = User(spotify_user_id="other", display_name="Other")
    db_session.add(other)
    db_session.commit()
    db_session.refresh(other)
    foreign = Rating(
        user_id=other.id,
        item_type="album",
        spotify_id="z",
        title="t",
        artist="a",
        rating=5,
    )
    db_session.add(foreign)
    db_session.commit()
    db_session.refresh(foreign)

    resp = client.patch(
        f"/ratings/{foreign.id}", json={"rating": 1}, headers=auth_headers
    )
    assert resp.status_code == 404
