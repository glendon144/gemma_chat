import pytest

import app as gemma_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(gemma_app, "DB_PATH", tmp_path / "gemma_chat.db")
    monkeypatch.setattr(gemma_app, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(gemma_app, "AUDIO_CACHE_DIR", tmp_path / "data" / "audio_cache")
    monkeypatch.setattr(gemma_app, "EXPORT_DIR", tmp_path / "data" / "exports")
    gemma_app.init_db()
    gemma_app.app.config.update(TESTING=True)
    return gemma_app.app.test_client()


@pytest.mark.parametrize("value", ["fast", None, True, float("nan"), float("inf")])
def test_chat_rejects_invalid_response_length(client, value):
    response = client.post("/chat", json={"message": "hello", "response_length": value})

    assert response.status_code == 400
    assert response.is_json
    assert "response_length" in response.json["error"]


@pytest.mark.parametrize("value", [0, 6, 2.5])
def test_chat_rejects_out_of_range_or_fractional_response_length(client, value):
    response = client.post("/chat", json={"message": "hello", "response_length": value})

    assert response.status_code == 400
    assert response.is_json


@pytest.mark.parametrize("value", ["many", None, True, float("nan"), 127, 8193, 512.5])
def test_chat_rejects_invalid_max_tokens(client, value):
    response = client.post("/chat", json={"message": "hello", "max_tokens": value})

    assert response.status_code == 400
    assert response.is_json
    assert "max_tokens" in response.json["error"]


@pytest.mark.parametrize("query", ["rate=fast", "rate=nan", "rate=0.5", "rate=2"])
def test_audio_export_rejects_invalid_rate_before_message_lookup(client, query):
    response = client.get(f"/api/messages/999/audio?{query}")

    assert response.status_code == 400
    assert response.is_json
    assert "rate" in response.json["error"]


@pytest.mark.parametrize(
    "payload, parameter",
    [
        ({"pacing_cps": "fast"}, "pacing_cps"),
        ({"pacing_cps": 17}, "pacing_cps"),
        ({"pacing_cps": 76}, "pacing_cps"),
        ({"pause_seconds": "long"}, "pause_seconds"),
        ({"pause_seconds": 0}, "pause_seconds"),
        ({"pause_seconds": 2}, "pause_seconds"),
    ],
)
def test_podcast_export_rejects_invalid_numeric_parameters(client, payload, parameter):
    response = client.post("/api/chats/999/podcast", json=payload)

    assert response.status_code == 400
    assert response.is_json
    assert parameter in response.json["error"]


def test_speak_rejects_fractional_message_id(client):
    response = client.post("/speak", json={"message_id": 1.5})

    assert response.status_code == 400
    assert response.is_json
    assert "message_id" in response.json["error"]


def test_runtime_openai_key_is_kept_in_process_memory(client, monkeypatch):
    monkeypatch.setattr(gemma_app, "RUNTIME_OPENAI_API_KEY", None)
    response = client.post("/api/openai-key", json={"api_key": "sk-test-value"})

    assert response.status_code == 200
    assert response.json == {"ok": True, "stored": "process_memory"}
    assert gemma_app.RUNTIME_OPENAI_API_KEY == "sk-test-value"


def test_runtime_openai_key_rejects_empty_value(client):
    response = client.post("/api/openai-key", json={"api_key": "  "})

    assert response.status_code == 400
    assert "key" in response.json["error"].lower()


def test_speech_uses_direct_http_request_without_sdk(monkeypatch):
    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return b"mp3-data"

    captured = {}
    def fake_urlopen(req, timeout):
        captured["req"] = req
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(gemma_app, "RUNTIME_OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(gemma_app, "urlopen", fake_urlopen)

    assert gemma_app.create_speech_audio("marin", "Hello") == b"mp3-data"
    assert captured["req"].full_url == "https://api.openai.com/v1/audio/speech"
    assert captured["req"].headers["Authorization"] == "Bearer sk-test"
    assert captured["timeout"] == 120


@pytest.mark.parametrize("url", ["http://127.0.0.1:8080", "http://localhost:8081/v1"])
def test_local_llm_url_accepts_supported_loopback_ports(monkeypatch, url):
    monkeypatch.setattr(gemma_app, "LOCAL_LLM_BASE_URL", url)

    assert gemma_app.local_llm_url() == url.rstrip("/") + ("" if url.endswith("/v1") else "/v1")


@pytest.mark.parametrize("url", ["http://127.0.0.1:8082", "http://example.com:8080", "file://127.0.0.1:8080"])
def test_local_llm_url_rejects_non_loopback_or_unsupported_ports(monkeypatch, url):
    monkeypatch.setattr(gemma_app, "LOCAL_LLM_BASE_URL", url)

    with pytest.raises(RuntimeError, match="port 8080 or 8081"):
        gemma_app.local_llm_url()
