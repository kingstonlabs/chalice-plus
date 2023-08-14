import pytest


@pytest.mark.usefixtures("book_delete_view")
def test_delete_view_success(client):
    response = client.http.delete("books/2")
    assert response.status_code == 204


@pytest.mark.usefixtures("book_delete_view")
def test_delete_view_unknown_object(client):
    response = client.http.delete("books/99")
    assert response.status_code == 404


@pytest.mark.usefixtures("book_delete_view")
def test_delete_view_invalid_id(client):
    response = client.http.delete("books/the-shining")
    assert response.status_code == 404
