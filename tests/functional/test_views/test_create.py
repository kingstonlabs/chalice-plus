import json
import pytest


@pytest.mark.usefixtures("book_create_view")
def test_create_view_bad_data(client):
    response = client.http.post(
        "books",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"bad": "data"})
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_create_view")
def test_create_view_incomplete_data(client):
    response = client.http.post(
        "books",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"title": "The Cat in the Hat"})
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_create_view")
def test_create_view_invalid_related_format(client):
    response = client.http.post(
        "books",
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "title": "The Cat in the Hat",
            "description": "About a cat",
            "author": {"id": 2},
            "created_by_id": 1,
        })
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_create_view")
def test_create_view_not_json_data(client):
    response = client.http.post(
        "books",
        headers={"Content-Type": "application/json"},
        body="..."
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_create_view")
def test_create_view_success(client):
    response = client.http.post(
        "books",
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "title": "The Cat in the Hat",
            "description": "About a cat",
            "author_id": 2,
        })
    )
    assert response.status_code == 201
    book = response.json_body
    assert book["id"] is not None
    assert book["title"] == "The Cat in the Hat"
    assert book["author"]["id"] == 2
    assert book["created_by"]["id"] == 1


@pytest.mark.usefixtures("book_create_view")
def test_create_view_success_with_field_mask(client):
    response = client.http.post(
        "books",
        headers={"Content-Type": "application/json", "X-Fields": "{id,title}"},
        body=json.dumps({
            "title": "A Horse Of Course",
            "description": "About a horse",
            "author_id": 2,
        })
    )
    assert response.status_code == 201
    assert set(response.json_body.keys()) == set(["id", "title"])
    assert response.json_body["title"] == "A Horse Of Course"
