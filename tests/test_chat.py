from unittest.mock import MagicMock


def _fake_gemini_response(content_text="Paris is the capital of France."):
    """Builds a fake response.text matching AssistantResponse's expected JSON shape."""
    import json
    fake = MagicMock()
    fake.text = json.dumps({"content": content_text, "title": "Capitals"})
    return fake


def test_guest_chat_message(client, monkeypatch):
    from backend.utils.gemini import client as gemini_client
    monkeypatch.setattr(
        gemini_client.models, "generate_content", lambda *a, **kw: _fake_gemini_response()
    )

    response = client.post(
        "/chat/message",
        json={"user_prompt": "What is the capital of France?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"]["user_prompt"] == "What is the capital of France?"
    assert body["content"]["AI_response"] == "Paris is the capital of France."
    assert body["content"]["conversation_title"] is None


def _signup_and_login(client, username="chatuser"):
    client.post(
        "/users/signup",
        json={"username": username, "email": f"{username}@example.com", "password": "StrongPass123!"},
    )
    login = client.post(
        "/auth/signin",
        json={"username": username, "password": "StrongPass123!"},
    )
    return login.json()["content"]["access_token"]


def test_authenticated_chat_creates_conversation(client, monkeypatch):
    from backend.utils.gemini import client as gemini_client
    monkeypatch.setattr(
        gemini_client.models, "generate_content", lambda *a, **kw: _fake_gemini_response()
    )

    token = _signup_and_login(client)
    response = client.post(
        "/chat/message",
        json={"user_prompt": "What is the capital of France?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"]["conversation_id"] is not None
    assert body["content"]["conversation_title"]
    assert body["content"]["sender"] == "chatuser"