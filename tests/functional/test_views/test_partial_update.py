import json
import pytest


@pytest.mark.usefixtures("book_update_view")
def test_partial_update_view_bad_data(client, app):
    response = client.http.patch(
        "books/1",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"bad": "data"})
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_partial_update_view_success(client):
    response = client.http.patch(
        "books/2",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"})
    )
    assert response.status_code == 200
    book = response.json_body
    assert book["id"] == 2
    assert book["title"] == "The Shining (updated)"
    assert book["author"]["id"] == 2


@pytest.mark.usefixtures("book_update_view")
def test_partial_update_view_invalid_related_format(client):
    response = client.http.patch(
        "books/2",
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "title": "The Shining (invalid author)",
            "author": {"id": 1},
        })
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_partial_update_view_not_json_data(client):
    response = client.http.patch(
        "books/2",
        headers={"Content-Type": "application/json"},
        body="..."
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_partial_update_view_related_object_success(client):
    response = client.http.patch(
        "books/2",
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "description": "Updated description",
            "author_id": 1,
        })
    )
    assert response.status_code == 200
    book = response.json_body
    assert book["id"] == 2
    assert book["title"] == "The Shining"
    assert book["description"] == "Updated description"
    assert book["author"]["id"] == 1


@pytest.mark.usefixtures("book_update_view")
def test_partial_update_view_with_field_mask(client):
    response = client.http.patch(
        "books/2",
        headers={
            "Content-Type": "application/json",
            "X-Fields": "{title,description,author{name}}",
        },
        body=json.dumps({
            "description": "Updated description for field mask",
            "author_id": 1,
        })
    )
    assert response.status_code == 200
    assert response.json_body == {
        "title": "The Shining",
        "description": "Updated description for field mask",
        "author": {"name": "Eric Carle"}
    }


@pytest.mark.usefixtures("book_update_view")
def test_partial_update_view_invalid_id(client):
    response = client.http.patch(
        "books/99",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"title": "New title"}),
    )
    assert response.status_code == 404
