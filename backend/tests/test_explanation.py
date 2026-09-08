import json

from fastapi.testclient import TestClient

from app import explanation
from app.main import app

client = TestClient(app)


def evidence():
    return {
        "method": "welch",
        "sample_sizes": [5, 5],
        "statistic": -3.0,
        "p_value": 0.02,
        "interpretation": "Evidence against the stated null.",
        "limitations": ["Synthetic test evidence; not a biological result."],
        "provenance": {"code_revision": "synthetic-test"},
    }


def test_status_and_endpoint_are_honest_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    status = client.get("/api/research/explain/status")
    assert status.status_code == 200
    assert status.json()["available"] is False
    response = client.post("/api/research/explain", json={
        "analysis_type": "statistical_analysis", "evidence": evidence()})
    assert response.status_code == 503
    assert "server-side OpenAI API access is not configured" in response.json()["detail"]


def test_raw_observations_and_oversized_evidence_are_rejected(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    raw = client.post("/api/research/explain", json={
        "analysis_type": "statistical_analysis", "evidence": {"inputs": {"groups": [[1, 2], [3, 4]]}}})
    assert raw.status_code == 422
    large = client.post("/api/research/explain", json={
        "analysis_type": "statistical_analysis", "evidence": {"interpretation": "x" * 50_001}})
    assert large.status_code == 422


def test_verified_structured_explanation_uses_exact_evidence(monkeypatch):
    captured = {}
    generated = {
        "summary": {"statement": "Welch analysis returned p = 0.02.",
                    "evidence_ids": ["method", "p_value"]},
        "findings": [{"statement": "The submitted statistic is -3.0.",
                      "evidence_ids": ["statistic"]}],
        "caveats": [{"statement": "This is not a biological result.",
                     "evidence_ids": ["limitations.0"]}],
    }
    upstream = {"id": "resp_test", "output": [{"content": [
        {"type": "output_text", "text": json.dumps(generated)}]}]}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return json.dumps(upstream).encode()

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(explanation.urllib.request, "urlopen", fake_urlopen)
    response = client.post("/api/research/explain", json={
        "analysis_type": "statistical_analysis", "evidence": evidence()})
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "gpt-6-astra"
    assert body["response_id"] == "resp_test"
    assert body["summary"]["evidence_ids"] == ["method", "p_value"]
    assert len(body["evidence_sha256"]) == 64
    assert captured["body"]["store"] is False
    assert captured["body"]["reasoning"] == {"effort": "low"}
    assert captured["body"]["text"]["format"]["strict"] is True
    assert captured["timeout"] == 45


def test_untraceable_claim_is_rejected(monkeypatch):
    generated = {
        "summary": {"statement": "The result contains 999 participants.",
                    "evidence_ids": ["sample_sizes.0"]},
        "findings": [{"statement": "The method was Welch.", "evidence_ids": ["method"]}],
        "caveats": [{"statement": "This is not a biological result.",
                     "evidence_ids": ["limitations.0"]}],
    }
    upstream = {"id": "resp_bad", "output_text": json.dumps(generated)}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return json.dumps(upstream).encode()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(explanation.urllib.request, "urlopen", lambda *_args, **_kwargs: Response())
    response = client.post("/api/research/explain", json={
        "analysis_type": "statistical_analysis", "evidence": evidence()})
    assert response.status_code == 503
    assert "could not be verified" in response.json()["detail"]
