from uuid import uuid4


def signup(client, restaurant_name="Test Cafe"):
    email = f"owner-{uuid4().hex[:8]}@example.com"
    response = client.post(
        "/api/signup",
        data={
            "restaurant_name": restaurant_name,
            "email": email,
            "password": "secret123",
        },
    )
    assert response.status_code == 200
    return email


def create_menu(client, title="Lunch"):
    response = client.post(
        "/api/menus",
        data={"title": title, "currency": "$"},
    )
    assert response.status_code == 201
    return response.json()


def test_auth_required_for_dashboard(client):
    response = client.get("/api/menus")
    assert response.status_code == 401


def test_signup_sets_session_and_me_returns_owner(client):
    email = signup(client)

    response = client.get("/api/me")

    assert response.status_code == 200
    assert response.json()["email"] == email


def test_owner_can_create_menu_category_and_item(client):
    signup(client)
    menu = create_menu(client)

    category_response = client.post(
        f"/api/menus/{menu['id']}/categories",
        data={"name": "Mains"},
    )
    assert category_response.status_code == 201
    category = category_response.json()

    item_response = client.post(
        f"/api/categories/{category['id']}/items",
        data={"name": "Burger", "details": "House sauce", "price": "12"},
    )
    assert item_response.status_code == 201

    edit_response = client.get(f"/api/menus/{menu['id']}")
    assert edit_response.status_code == 200
    edit_menu = edit_response.json()
    assert edit_menu["categories"][0]["name"] == "Mains"
    assert edit_menu["categories"][0]["items"][0]["name"] == "Burger"


def test_owner_can_delete_item(client):
    signup(client)
    menu = create_menu(client)

    category_response = client.post(
        f"/api/menus/{menu['id']}/categories",
        data={"name": "Mains"},
    )
    assert category_response.status_code == 201
    category = category_response.json()

    item_response = client.post(
        f"/api/categories/{category['id']}/items",
        data={"name": "Burger", "details": "House sauce", "price": "12"},
    )
    assert item_response.status_code == 201
    item = item_response.json()

    delete_response = client.delete(f"/api/items/{item['id']}")
    assert delete_response.status_code == 204

    edit_response = client.get(f"/api/menus/{menu['id']}")
    assert edit_response.status_code == 200
    assert edit_response.json()["categories"][0]["items"] == []


def test_public_menu_and_dynamic_qr(client):
    signup(client, restaurant_name="QR Cafe")
    menu = create_menu(client, title="Dinner")

    public_response = client.get(f"/api/m/{menu['slug']}")
    assert public_response.status_code == 200
    assert public_response.json()["title"] == "Dinner"
    assert public_response.json()["restaurant_name"] == "QR Cafe"

    qr_response = client.get(f"/api/menus/{menu['id']}/qr")
    assert qr_response.status_code == 200
    assert qr_response.headers["content-type"] == "image/png"
    assert qr_response.content.startswith(b"\x89PNG\r\n\x1a\n")

    menus_response = client.get(f"/api/restaurants/{menu['owner_id']}/menus")
    assert menus_response.status_code == 200
    assert menus_response.json()[0]["slug"] == menu["slug"]


def test_optional_images_and_background_upload(client):
    signup(client)
    menu = create_menu(client)

    background_bytes = b"fake-background-image"
    category_bytes = b"fake-category-image"

    update_response = client.put(
        f"/api/menus/{menu['id']}",
        data={"title": menu["title"], "currency": "$", "is_published": "true"},
        files={"background_image": ("background.png", background_bytes, "image/png")},
    )
    assert update_response.status_code == 200
    background_path = update_response.json()["background_image_path"]
    assert background_path.startswith("/api/images/")
    background_response = client.get(background_path)
    assert background_response.status_code == 200
    assert background_response.content == background_bytes

    category_response = client.post(
        f"/api/menus/{menu['id']}/categories",
        data={"name": "Desserts"},
        files={"image": ("category.png", category_bytes, "image/png")},
    )
    assert category_response.status_code == 201
    category_path = category_response.json()["image_path"]
    assert category_path.startswith("/api/images/")
    category_image_response = client.get(category_path)
    assert category_image_response.status_code == 200
    assert category_image_response.content == category_bytes

    item_response = client.post(
        f"/api/categories/{category_response.json()['id']}/items",
        data={"name": "Cake", "details": "", "price": "8"},
    )
    assert item_response.status_code == 201
    assert item_response.json()["image_path"] is None


def test_hidden_menu_is_not_public(client):
    signup(client)
    menu = create_menu(client)

    response = client.put(
        f"/api/menus/{menu['id']}",
        data={"title": menu["title"], "currency": "$", "is_published": "false"},
    )
    assert response.status_code == 200

    public_response = client.get(f"/api/m/{menu['slug']}")
    assert public_response.status_code == 404
