import pytest


@pytest.mark.usefixtures("book_detail_view")
def test_detail_view_success(client):
    response = client.http.get("books/1")
    assert response.status_code == 200
    assert response.json_body["id"] == 1
    assert response.json_body["title"] == "The Very Hungry Caterpillar"


@pytest.mark.usefixtures("book_detail_view")
def test_detail_view_field_mask(client):
    response = client.http.get("books/1", headers={"X-Fields": "{id,title}"})
    assert response.status_code == 200
    assert response.json_body == {"id": 1, "title": "The Very Hungry Caterpillar"}


@pytest.mark.usefixtures("book_detail_view")
def test_detail_view_nested_field_mask(client):
    response = client.http.get(
        "books/2",
        headers={"X-Fields": "{id,title,author{name},created_by{username}}"}
    )
    assert response.status_code == 200
    assert response.json_body == {
        "id": 2,
        "title": "The Shining",
        "author": {"name": "Stephen King"},
        "created_by": {"username": "horse"},
    }


@pytest.mark.usefixtures("book_detail_view")
def test_detail_view_invalid_field_mask(client):
    response = client.http.get("books/1", headers={"X-Fields": "---a---"})
    assert response.status_code == 200
    assert response.json_body == {}


@pytest.mark.usefixtures("book_detail_view")
def test_detail_view_unknown_object(client):
    response = client.http.get("books/99")
    assert response.status_code == 404


@pytest.mark.usefixtures("book_detail_view")
def test_detail_view_invalid_id(client):
    response = client.http.get("books/the-shining")
    assert response.status_code == 404
