import base64
import json
import pytest


TOKEN_DATA_TEMPLATE = {
    "scope": "aws.cognito.signin.user.admin",
    "sub": "",
    "token_use": "access",
}


def get_token(user_id=None):
    token_data = TOKEN_DATA_TEMPLATE.copy()
    if user_id:
        token_data["sub"] = user_id
    token_segment = base64.urlsafe_b64encode(json.dumps(token_data).encode("utf-8")).decode("utf-8")
    return f"Bearer X.{token_segment}"


@pytest.mark.usefixtures("author_detail_view_is_authenticated")
def test_is_authenticated_no_token(client):
    response = client.http.get("authors/1")
    assert response.status_code == 403
    assert response.json_body["Message"] == "User is not authenticated"


@pytest.mark.usefixtures("author_detail_view_is_authenticated")
def test_is_authenticated_unknown_user(client):
    token = get_token(user_id=99)
    response = client.http.get("authors/1", headers={"Authorization": token})
    assert response.status_code == 403
    assert response.json_body["Message"] == "User is not authenticated"


@pytest.mark.usefixtures("author_detail_view_is_authenticated")
def test_is_authenticated_valid_token(client):
    token = get_token(user_id=1)
    response = client.http.get("authors/1", headers={"Authorization": token})
    assert response.status_code == 200
    assert response.json_body["name"] == "Eric Carle"


@pytest.mark.usefixtures("book_create_view_is_admin")
def test_is_admin_permission_unknown_user(client):
    bad_token = get_token(user_id=99)
    response = client.http.post(
        "books",
        headers={"Authorization": bad_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "IT", "author_id": 2}),
    )
    assert response.status_code == 403


@pytest.mark.usefixtures("book_create_view_is_admin")
def test_is_admin_permission_non_admin_user(client):
    non_admin_token = get_token(user_id=2)
    response = client.http.post(
        "books",
        headers={"Authorization": non_admin_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "IT", "author_id": 2}),
    )
    assert response.status_code == 403
    assert response.json_body["Message"] == "User is not admin"


@pytest.mark.usefixtures("book_create_view_is_admin")
def test_is_admin_permission_admin_user(client):
    admin_token = get_token(user_id=1)
    response = client.http.post(
        "books",
        headers={"Authorization": admin_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "IT", "description": "Clown", "author_id": 2}),
    )
    assert response.status_code == 201


@pytest.mark.usefixtures("book_update_view_is_owner")
def test_is_owner_permission_unknown_user(client):
    bad_token = get_token(user_id=99)
    response = client.http.patch(
        "books/2",
        headers={"Authorization": bad_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"}),
    )
    assert response.status_code == 403


@pytest.mark.usefixtures("book_update_view_is_owner")
def test_is_owner_permission_non_owner(client):
    non_owner_token = get_token(user_id=2)
    response = client.http.patch(
        "books/1",
        headers={"Authorization": non_owner_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"}),
    )
    assert response.status_code == 403
    assert response.json_body["Message"] == "User is not owner"


@pytest.mark.usefixtures("book_update_view_is_owner")
def test_is_owner_permission_owner(client):
    owner_token = get_token(user_id=2)
    response = client.http.patch(
        "books/2",
        headers={"Authorization": owner_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"}),
    )
    assert response.status_code == 200


@pytest.mark.usefixtures("book_update_view_is_owner_or_admin")
def test_is_owner_or_admin_permission_unknown_user(client):
    bad_token = get_token(user_id=99)
    response = client.http.patch(
        "books/2",
        headers={"Authorization": bad_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"}),
    )
    assert response.status_code == 403


@pytest.mark.usefixtures("book_update_view_is_owner_or_admin")
def test_is_owner_or_admin_permission_non_owner_non_admin(client):
    non_owner_token = get_token(user_id=2)
    response = client.http.patch(
        "books/1",
        headers={"Authorization": non_owner_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"}),
    )
    assert response.status_code == 403
    assert response.json_body["Message"] == "User is not owner or admin"


@pytest.mark.usefixtures("book_update_view_is_owner_or_admin")
def test_is_owner_or_admin_permission_non_owner_admin(client):
    non_owner_token = get_token(user_id=1)
    response = client.http.patch(
        "books/2",
        headers={"Authorization": non_owner_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"}),
    )
    assert response.status_code == 200


@pytest.mark.usefixtures("book_update_view_is_owner_or_admin")
def test_is_owner_or_admin_permission_owner_non_admin(client):
    non_owner_token = get_token(user_id=2)
    response = client.http.patch(
        "books/2",
        headers={"Authorization": non_owner_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"}),
    )
    assert response.status_code == 200


@pytest.mark.usefixtures("book_update_view_is_owner_or_admin")
def test_is_owner_or_admin_permission_owner_admin(client):
    owner_token = get_token(user_id=1)
    response = client.http.patch(
        "books/1",
        headers={"Authorization": owner_token, "Content-Type": "application/json"},
        body=json.dumps({"title": "The Shining (updated)"}),
    )
    assert response.status_code == 200


@pytest.mark.usefixtures("author_create_list_view_is_admin")
def test_permissions_per_http_method(client):
    response = client.http.get("authors")
    assert response.status_code == 200

    bad_token = get_token(user_id=99)
    response = client.http.get("authors", headers={"Authorization": bad_token})
    assert response.status_code == 200

    response = client.http.post("authors")
    assert response.status_code == 403

    response = client.http.post("authors", headers={"Authorization": bad_token})
    assert response.status_code == 403

    good_token = get_token(user_id=1)
    response = client.http.post(
        "authors",
        headers={"Authorization": good_token, "Content-Type": "application/json"},
        body=json.dumps({"name": "Dr Seuss", "description": "Author"}),
    )
    assert response.status_code == 201
    assert response.json_body["name"] == "Dr Seuss"
    assert response.json_body["created_by"] == {"id": 1, "username": "monkey"}
