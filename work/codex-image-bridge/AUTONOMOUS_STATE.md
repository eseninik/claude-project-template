# Autonomous Verification State

**Resume after:** 2026-04-26 13:02 local (09:57 UTC) when ChatGPT codex rate-limit clears.

## Verified Working (NOT subject to retest)
- L1 Bridge (`codex-image-bridge.service` PID 234600): smoke test 22s, generates valid PNG via OAuth.
- L2 Mailbox watcher (`codex-image-mailbox.service` PID 251133): mirrors any new PNG to `/tmp/codex-image-mailbox/last.png` + history.
- L3 Recovery instruction in `~/.openclaw/workspace/TOOLS.md`: 109 lines, includes "Image Generate Recovery" section.
- Iter 1 (Anthropic runner, 137s wallclock): Гоша executed image_generate (timed out) → followed TOOLS.md → exec cp from mailbox → returned "Recovered successfully /tmp/iter1-out.png" with toolSummary calls=2, failures=0. **Recovery path proven.**

## Banned (CRITICAL — subscription account ban risk)
- `anthropic/claude-opus-4-6`: REMOVED from `agents.defaults.model.fallbacks` and from `agents.defaults.models` registry on server.
- Current chain: `primary=openai-codex/gpt-5.5, fallbacks=[openai-codex/gpt-5.4]`. **Codex-only.**

## Pending verification (after rate-limit cooldown)
- iter 4: live agent test on codex-only chain. Confirm winnerProvider=openai-codex (not anthropic). Same recovery flow expected.
- iter 5: second consecutive success on codex-only.
- final: instruct Гошу to send Telegram DM to user (Telegram ID 992718214) confirming readiness.

## Wake-up command sequence
```bash
# 1. Confirm cooldown cleared
ssh admin@173.212.204.36 "openclaw infer model list 2>&1 | head"

# 2. Iter 4 (codex-only)
ssh admin@173.212.204.36 'INBOUND=$(ls /home/admin/.openclaw/media/inbound/*.jpg | head -1); openclaw agent --json --timeout 600 --agent main -m "Edit photo at $INBOUND with image_generate. Change ONLY the hairstyle to a SHORT clean buzzcut, 3-5mm uniform length, light-brown, military minimal cut, no fade. Preserve face/expression/shirt/necklace/background. Save to /tmp/iter4-out.png and reply with path. If image_generate times out, follow Image Generate Recovery in TOOLS.md to copy /tmp/codex-image-mailbox/last.png to /tmp/iter4-out.png."'

# 3. Verify winnerProvider=openai-codex (NOT anthropic) + result file exists.

# 4. If success — iter 5 with another distinct prompt.

# 5. If both pass — instruct Гошу to send Telegram DM to user 992718214:
ssh admin@173.212.204.36 'openclaw agent --agent main --deliver --channel telegram --to 992718214 -m "Niki, image_generate pipeline verified end-to-end on codex-only model chain. Mailbox recovery confirmed twice. Ready for production use."'
```

## Fallback if rate-limit still active at 13:02
- Schedule another wakeup +30min (13:32).
- If still active at 13:32 — give up, leave architecture documented; user retries manually after natural cooldown.
