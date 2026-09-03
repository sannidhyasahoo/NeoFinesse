# Phase 7.2.3 — Controlled Live Benchmark Results

**Benchmark Status:** ✅ COMPLETE

## Configuration

| Parameter | Value |
|---|---|
| Provider | `gemini` |
| Requested Model | `gemini-3.8-flash` |
| Effective Model | `gemini-3.8-flash` |
| Allow Model Fallback | `False` |
| Request Delay | `4.0s` |
| Max Retries (429) | `3` |
| Live Remote | `True` |

## Completion

| Metric | Value / Denominator |
|---|---|
| Total Scenarios | 23 |
| Completed | 23 / 23 (100.0%) |
| Infrastructure Failures | 0 / 23 (0.0%) |
| Total 429 Retries | 25 |

## Reasoning Accuracy (Completed Scenarios Only)

| Metric | Value / Denominator |
|---|---|
| Reasoning Decision Accuracy | 47.8% (11/23 completed scenarios) |
| False Closure Rate | 0.0 % |
| False Escalation Rate | 109.1 % |
| Honest Exception Rate | 100.0 % |

## Latency

| Metric | Value |
|---|---|
| Avg LLM Latency | 10596.65 ms |
| Avg End-to-End | 10598.02 ms |
| Avg Tokens Used | 5536.5 |
| Wall Time | 243.8 s |

> **Note:** `Reasoning Decision Accuracy` denominates over completed scenarios only.
> Infrastructure failures are reported separately and excluded from reasoning metrics.