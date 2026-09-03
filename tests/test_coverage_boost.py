import os
from pathlib import Path
from unittest import mock

import pytest

from neofinesse.agentic_investigation.benchmark import run_standalone_agentic_benchmark
from neofinesse.agentic_investigation.live_benchmark import run_standalone_live_benchmark
from neofinesse.agentic_investigation.llm_client import GenericLLMClient, LiveMockMode, MockLLMClient
from neofinesse.ai_investigation.benchmark import run_standalone_ai_benchmark
from neofinesse.investigation.benchmark import main as investigation_benchmark_main
from neofinesse.retrieval.benchmark import main as retrieval_benchmark_main


def test_standalone_live_benchmark_cli(tmp_path, monkeypatch):
    """Tests run_standalone_live_benchmark execution for coverage."""
    monkeypatch.chdir(tmp_path)
    run_standalone_live_benchmark()
    assert (Path("experiments/phase7/live/results.json")).exists()
    assert (Path("experiments/phase7/live/results.csv")).exists()
    assert (Path("experiments/phase7/live/scenario_audit.csv")).exists()


def test_standalone_agentic_benchmark_cli(tmp_path, monkeypatch):
    """Tests run_standalone_agentic_benchmark execution for coverage."""
    monkeypatch.chdir(tmp_path)
    run_standalone_agentic_benchmark()
    assert (Path("experiments/phase7/results.json")).exists()
    assert (Path("experiments/phase7/results.csv")).exists()


def test_standalone_ai_benchmark_cli(tmp_path, monkeypatch):
    """Tests run_standalone_ai_benchmark execution for coverage."""
    monkeypatch.chdir(tmp_path)
    run_standalone_ai_benchmark()
    assert (Path("experiments/phase6/results.json")).exists()


def test_standalone_investigation_benchmark_cli(tmp_path, monkeypatch):
    """Tests run_standalone_investigation_benchmark execution for coverage."""
    monkeypatch.chdir(tmp_path)
    investigation_benchmark_main()
    assert (Path("experiments/phase5/results.json")).exists()


def test_standalone_retrieval_benchmark_cli(tmp_path, monkeypatch):
    """Tests run_standalone_retrieval_benchmark execution for coverage."""
    monkeypatch.chdir(tmp_path)
    retrieval_benchmark_main()
    assert (Path("experiments/phase4/results.json")).exists()


def test_generic_llm_client_additional_paths(monkeypatch):
    """Tests uncovered branches in GenericLLMClient."""
    # Test key detection for groq and openai
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test123")
    c_groq = GenericLLMClient(provider="groq")
    assert c_groq.provider_name == "groq"
    assert c_groq._api_key == "gsk_test123"

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
    c_openai = GenericLLMClient(provider="openai")
    assert c_openai.provider_name == "openai"
    assert c_openai._api_key == "sk-test123"

    # Test fallback triggered attributes
    c_gem = GenericLLMClient(provider="gemini", model="gemini-3.7-flash")
    assert c_gem.requested_model == "gemini-3.7-flash"
    assert c_gem.effective_model == "gemini-3.7-flash"
    assert c_gem.fallback_triggered is False
    assert c_gem.fallback_reason is None

    diag = c_gem.format_diagnostic()
    assert "Requested Model:" in diag
    assert "Effective Model:" in diag
    assert "Fallback Triggered:" in diag
