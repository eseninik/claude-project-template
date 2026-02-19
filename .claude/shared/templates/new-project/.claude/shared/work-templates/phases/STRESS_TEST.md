# Phase Template: STRESS_TEST

> Run load and performance tests against deployed service, verify thresholds.

## Metadata
- Default Mode: SOLO
- Gate Type: AUTO
- Loop Target: none
- Max Attempts: 1
- Checkpoint: pipeline-checkpoint-STRESS_TEST

## Phase Context Loading
Before starting this phase, load:
- Deploy results (service URL, health check status)
- Performance baselines (if they exist from previous runs)
- Query Graphiti: `search_memory_facts(query="performance benchmarks and optimization", max_facts=10)`

## Inputs
- Running deployed service (from DEPLOY phase)
- `work/{feature}/tech-spec.md` (performance requirements if any)
- `locustfile.py` or `k6.js` (load test script, create if missing)

## Process
1. Verify service is reachable:
   ```bash
   ssh user@server "curl -sf http://localhost:8080/health"
   ```
2. If no load test script exists, create `locustfile.py` based on API endpoints
3. Run load test:
   ```bash
   locust -f locustfile.py --headless \
     -u 100 -r 10 --run-time 60s \
     --host http://server:8080 \
     --csv=work/{feature}/perf
   ```
4. Collect metrics from CSV output:
   - Response time p50, p95, p99
   - Requests per second
   - Error rate
   - Max concurrent users sustained
5. Write report to `work/{feature}/performance-report.md`
6. Compare against thresholds: p95 < 500ms, error rate < 1%

## Outputs
- `work/{feature}/performance-report.md` (metrics, charts, verdict)
- `work/{feature}/perf_stats.csv` (raw locust data)

## Quality Gate
Parse locust CSV output for threshold violations.

### Verdicts
- PASS: p95 < 500ms AND error_rate < 1%
- CONCERNS: p95 < 1000ms AND error_rate < 5% (acceptable but not ideal)
- REWORK: Thresholds exceeded — identify bottleneck, optimize, redeploy
- FAIL: Service crashes under load or error_rate > 10%

## Context Recovery
After compaction, re-read:
- `work/PIPELINE.md` (find current phase)
- `work/{feature}/performance-report.md` (if exists — see results)
- `locustfile.py` (load test configuration)
