import pytest


@pytest.mark.usefixtures("book_list_view")
def test_list_view_success(client):
    response = client.http.get("books")
    assert response.status_code == 200
    books = response.json_body
    assert len(books) == 3
    book_titles = [b["title"] for b in books]
    assert book_titles == ["The Very Hungry Caterpillar", "The Shining", "Carrie"]
    assert books[0] == {
        "id": 1,
        "title": "The Very Hungry Caterpillar",
        "description": "The story of a very hungry caterpillar",
        "author": {
            "id": 1,
            "name": "Eric Carle",
            "description": "Writer and illustrator",
            "created_by": {"id": 1, "username": "monkey"},
        },
        "created_by": {"id": 1, "username": "monkey"},
    }


@pytest.mark.usefixtures("book_list_view")
def test_list_view_field_mask(client):
    response = client.http.get("books", headers={"X-Fields": "{title}"})
    assert response.status_code == 200
    assert response.json_body == [
        {"title": "The Very Hungry Caterpillar"},
        {"title": "The Shining"},
        {"title": "Carrie"}
    ]


@pytest.mark.usefixtures("book_list_view")
def test_list_view_nested_field_mask(client):
    response = client.http.get(
        "books",
        headers={"X-Fields": "{id,title,author{name},created_by{username}}"}
    )
    assert response.status_code == 200
    books = response.json_body
    assert books == [
        {
            "id": 1,
            "title": "The Very Hungry Caterpillar",
            "author": {"name": "Eric Carle"},
            "created_by": {"username": "monkey"},
        }, {
            "id": 2,
            "title": "The Shining",
            "author": {"name": "Stephen King"},
            "created_by": {"username": "horse"},
        }, {
            "id": 3,
            "title": "Carrie",
            "author": {"name": "Stephen King"},
            "created_by": {"username": "monkey"},
        },
    ]


@pytest.mark.usefixtures("book_list_view")
def test_list_view_unknown_field_mask(client):
    response = client.http.get("books", headers={"X-Fields": "{title,sdflhdsflh}"})
    assert response.status_code == 200
    books = response.json_body
    assert books == [
        {"title": "The Very Hungry Caterpillar"},
        {"title": "The Shining"},
        {"title": "Carrie"},
    ]


@pytest.mark.usefixtures("book_list_view")
def test_list_view_invalid_field_mask(client):
    response = client.http.get("books", headers={"X-Fields": "{{{/aaa/s*"})
    assert response.status_code == 400
