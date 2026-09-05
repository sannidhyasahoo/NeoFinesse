"""
tests/test_ui.py
Unit tests for NeoFinesse Phase 8 Demo & Audit UI components, data exporter,
server endpoints, and static asset delivery.
"""
from __future__ import annotations

import json
from pathlib import Path
import threading
import time
import urllib.request
import pytest

from neofinesse.ui.data_exporter import export_demo_data_file, generate_ui_demo_payload
from neofinesse.ui.server import run_ui_server


class TestUIDataExporter:
    """Tests for Phase 8 UI payload generation."""

    def test_generate_ui_demo_payload(self):
        payload = generate_ui_demo_payload(seed=42)

        assert "metadata" in payload
        assert "kpis" in payload
        assert "benchmarks" in payload
        assert "demo_cases" in payload
        assert "scenarios" in payload

        # Check KPIs
        kpis = payload["kpis"]
        assert kpis["total_variances"] == 23
        assert kpis["false_closure_rate_pct"] == 0.0

        # Check Demo Cases (exactly 4)
        demos = payload["demo_cases"]
        assert len(demos) == 4
        demo_ids = [d["demo_id"] for d in demos]
        assert demo_ids == ["demo_1", "demo_2", "demo_3", "demo_4"]

        # Check Scenarios (all 23)
        scenarios = payload["scenarios"]
        assert len(scenarios) == 23
        for s in scenarios:
            assert "case_id" in s
            assert "scenario_id" in s
            assert "settlement_id" in s
            assert "expected_outcome" in s
            assert "variance_inr" in s
            assert "evidence_nodes" in s
            assert "constraint_checks" in s
            assert "ai_hypothesis" in s
            assert "verifier_outcome" in s

    def test_export_demo_data_file(self, tmp_path):
        target = tmp_path / "test_demo_data.json"
        out = export_demo_data_file(target)
        assert out.exists()
        assert out.stat().st_size > 1000

        with open(out, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["metadata"]["product_name"] == "NeoFinesse"


@pytest.fixture(scope="module")
def ui_server():
    server, port = run_ui_server(host="127.0.0.1", port=8990, open_browser=False)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.3)
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()


class TestUIServerAndEndpoints:
    """Tests for Phase 8 UI HTTP server and REST endpoints."""


    def test_root_index_html(self, ui_server):
        req = urllib.request.Request(f"{ui_server}/")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert "text/html" in resp.headers.get("Content-Type", "")
            content = resp.read().decode("utf-8")
            assert "NeoFinesse" in content
            assert "Executive Dashboard" in content
            assert "Flagship Provenance Graph" in content
            assert "AI vs. Verifier" in content

    def test_api_health(self, ui_server):
        req = urllib.request.Request(f"{ui_server}/api/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert "application/json" in resp.headers.get("Content-Type", "")
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert data["service"] == "neofinesse-ui"

    def test_api_data_bundle(self, ui_server):
        req = urllib.request.Request(f"{ui_server}/api/data")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert "application/json" in resp.headers.get("Content-Type", "")
            data = json.loads(resp.read().decode("utf-8"))
            assert len(data["scenarios"]) == 23
            assert len(data["demo_cases"]) == 4

    def test_static_css(self, ui_server):
        req = urllib.request.Request(f"{ui_server}/static/css/styles.css")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert "text/css" in resp.headers.get("Content-Type", "")
            css = resp.read().decode("utf-8")
            assert "--bg-primary" in css
            assert "glassmorphism" in css.lower() or "--bg-card" in css

    def test_static_js(self, ui_server):
        req = urllib.request.Request(f"{ui_server}/static/js/app.js")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert "application/javascript" in resp.headers.get("Content-Type", "")
            js = resp.read().decode("utf-8")
            assert "provenance-svg" in js or "renderInvestigationGraph" in js

    def test_not_found(self, ui_server):
        req = urllib.request.Request(f"{ui_server}/nonexistent_endpoint")
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)
        assert exc_info.value.code == 404

    def test_security_directory_traversal_blocked(self, ui_server):
        req = urllib.request.Request(f"{ui_server}/static/../../etc/passwd")
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(req, timeout=5)
        assert exc_info.value.code in (400, 403, 404)
