# Task Decomposition Examples

## Example 1: High Confidence

**Task:** "Add a notification system"

1. **Parse:** keyword "notification" matches Notifications pattern
2. **Subtasks (from pattern):**
   - Notification model (models/)
   - API endpoints (api/)
   - Email service (services/)
   - Push notification (services/)
   - Webhook integration (webhooks/)
   - Tests (tests/)
3. **Independence:** all different files -> INDEPENDENT
4. **Waves:**
   - Wave 1: [1,2,3,4,5] (parallel)
   - Wave 2: [6] (tests depend on all)
5. **Confidence:** 50% + 30% (pattern) + 10% (files) = 90% -> HIGH
6. **Recommendation:** propose parallel execution confidently, ~80% time savings

## Example 2: Medium Confidence

**Task:**
```
Need to:
- Add logging
- Update README
- Write smoke tests
```

1. **Parse:** 3-item list, no pattern match
2. **Subtasks:** logging (code), README (docs), smoke tests (tests/)
3. **Independence:** different files -> INDEPENDENT, but tests may depend on logging (uncertain)
4. **Waves:**
   - Option A: Wave 1: [1,2,3] (all parallel, if independent)
   - Option B: Wave 1: [1,2], Wave 2: [3] (if tests depend on logging)
5. **Confidence:** 50% + 20% (list) + 10% (files) - 20% (uncertain) = 60% -> MEDIUM
6. **Recommendation:** present subtasks, ask "Do smoke tests depend on the logging changes?"

## Example 3: Low Confidence

**Task:** "Improve performance"

1. **Parse:** keyword "performance" partially matches Performance Optimization
2. **Problem:** unclear WHICH optimizations, which files, needs profiling first
3. **Confidence:** 50% + 10% (partial) - 40% (unclear) = 20% -> LOW
4. **Recommendation:** ask specifics — which parts are slow? Known bottlenecks? Suggest starting with profiling.
