# Phase 7.2.3 — Controlled Live Benchmark Results (FROZEN)

**Benchmark Status:** ⚠️ INCOMPLETE (FROZEN)

> **Phase 7.2 Freeze Directive:**
> The live controlled benchmark was halted and marked **INCOMPLETE**. The run was infrastructure-limited by external API free-tier quotas. 
> Per architectural directive: **AI investigates. Evidence constrains. Deterministic verification decides.**
> The primary benchmark authority remains the **Phase 7 Controlled Agent (23/23 correct, 0% false closure, 0% false escalation, 100% honest exception)** in `experiments/phase7/agentic/`.

## Configuration

| Parameter | Value |
|---|---|
| Provider | `gemini` |
| Requested Model | `gemini-3.8-flash` / `gemini-3.7-flash` |
| Effective Model | `gemini-3.8-flash` / `gemini-3.7-flash` |
| Allow Model Fallback | `False` (strict single-model) |
| Request Delay | `4.0s` |
| Max Retries (429/503) | `3` |
| Live Remote | `True` |

## Benchmark Outcome Summary

| Metric | Status | Note |
|---|---|---|
| Benchmark Completion | **INCOMPLETE** | Halted due to external free-tier quota exhaustion |
| False Closure Rate | **0.0%** (0 / 12) | **Zero financial loss invariant verified** across all runs |
| Fallback Status | **False** | Strict single-model isolation enforced |
| Primary Benchmark Reference | **Phase 7 Controlled (100% - 23/23)** | Frozen synthetic environment |

## Architectural Takeaway

The system's core safety boundary worked as designed: when the LLM hit external quota exhaustion, the controller safely aborted to **fail-safe escalation** rather than hallucinating financial resolutions. At no point did the external LLM possess financial closure authority.