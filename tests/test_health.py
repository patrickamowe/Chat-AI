def test_root_serves_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_profile_page_loads(client):
    response = client.get("/profile")
    assert response.status_code == 200


def test_static_files_mounted(client):
    # Confirms StaticFiles mount didn't break app boot; 404 is fine, 500 is not
    response = client.get("/static/CSS/home-page.css")
    assert response.status_code in (200, 404)