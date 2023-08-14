import json
import pytest


@pytest.mark.usefixtures("book_update_view")
def test_update_view_existing_object_bad_data(client, app):
    response = client.http.put(
        "books/1",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"bad": "data"})
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_update_view_existing_object_incomplete_data(client):
    response = client.http.put(
        "books/2",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"})
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_update_view_existing_object_success(client):
    response = client.http.put(
        "books/2",
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "title": "The Shining (PUT)",
            "description": "New description",
            "author_id": 2,
        })
    )
    assert response.status_code == 200
    book = response.json_body
    assert book["id"] is not None
    assert book["title"] == "The Shining (PUT)"
    assert book["author"]["id"] == 2


@pytest.mark.usefixtures("book_update_view")
def test_update_view_existing_object_invalid_related_format(client):
    response = client.http.put(
        "books/2",
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "title": "The Shining (invalid author)",
            "author": {"id": 1},
        })
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_update_view_existing_object_not_json_data(client):
    response = client.http.put(
        "books/2",
        headers={"Content-Type": "application/json"},
        body="..."
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_update_view_existing_object_with_field_mask(client):
    response = client.http.put(
        "books/1",
        headers={
            "Content-Type": "application/json",
            "X-Fields": "{title,description,author{name}}",
        },
        body=json.dumps({
            "title": "The Very Hungry Caterpillar",
            "description": "New description (with field mask)",
            "author_id": 1,
        })
    )
    assert response.status_code == 200
    assert response.json_body == {
        "title": "The Very Hungry Caterpillar",
        "description": "New description (with field mask)",
        "author": {"name": "Eric Carle"}
    }


@pytest.mark.usefixtures("book_update_view")
def test_update_view_new_object_bad_data(client, app):
    response = client.http.put(
        "books/50",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"bad": "data"})
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_update_view_new_object_incomplete_data(client):
    response = client.http.put(
        "books/50",
        headers={"Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"})
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_update_view_new_object_success(client):
    response = client.http.put(
        "books/50",
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "title": "The Pig with a Fig",
            "description": "New description",
            "author_id": 1,
        })
    )
    assert response.status_code == 201
    book = response.json_body
    assert book["id"] == 50
    assert book["title"] == "The Pig with a Fig"
    assert book["author"]["id"] == 1


@pytest.mark.usefixtures("book_update_view")
def test_update_view_new_object_invalid_related_format(client):
    response = client.http.put(
        "books/50",
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "title": "The Shining (invalid author)",
            "author": {"id": 1},
        })
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_update_view_new_object_not_json_data(client):
    response = client.http.put(
        "books/50",
        headers={"Content-Type": "application/json"},
        body="..."
    )
    assert response.status_code == 400


@pytest.mark.usefixtures("book_update_view")
def test_update_view_new_object_with_field_mask(client):
    response = client.http.put(
        "books/50",
        headers={
            "Content-Type": "application/json",
            "X-Fields": "{id,title,description,author{name}}",
        },
        body=json.dumps({
            "title": "The Very Hungry Caterpillar",
            "description": "New description (with field mask)",
            "author_id": 1,
        })
    )
    assert response.status_code == 201
    assert response.json_body == {
        "id": 50,
        "title": "The Very Hungry Caterpillar",
        "description": "New description (with field mask)",
        "author": {"name": "Eric Carle"}
    }
