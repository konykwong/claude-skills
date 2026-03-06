---
name: openclaw-telegram-thinking
description: Use when the openclaw Telegram bot is not showing thinking/reasoning output, thinking tokens are missing from bot replies, or you want to configure how much the agent thinks by default when responding via Telegram.
---

# OpenClaw Telegram Bot Thinking Configuration

## Overview

OpenClaw has two separate controls for thinking in Telegram:

1. **`thinkingDefault`** (config-level) — how much the agent thinks by default: `off`, `minimal`, `low`, `medium`, `high`, `xhigh`
2. **`thinkingLevel`** (per-session directive) — whether thinking tokens are streamed live: `off`, `on`, `stream`

These are independent. Setting `thinkingDefault` enables reasoning; `thinkingLevel: stream` streams the `<think>` blocks live in chat.

## Symptoms This Fixes

- Bot replies but shows no reasoning/thinking
- `thinkingLevel` is `"off"` in session logs
- Thinking tokens were visible before but stopped appearing
- Agent sessions show `"thinking_level_change"` → `"off"` entries in history

## Fix 1 — Enable thinking by default (config-level)

Edit `~/.openclaw/openclaw.json` and add `thinkingDefault` to `agents.defaults`:

```json
{
  "agents": {
    "defaults": {
      "thinkingDefault": "medium"
    }
  }
}
```

**Valid values:** `off` | `minimal` | `low` | `medium` | `high` | `xhigh`

Then restart the gateway:

```bash
docker restart openclaw-gateway
```

Validate config:

```bash
docker exec openclaw-gateway node /app/dist/index.js doctor
# Should show no config errors
```

## Fix 2 — Stream thinking tokens live in Telegram

`thinkingDefault` controls the *amount* of thinking, not whether tokens are shown. To stream `<think>` blocks live in the TG chat, use the per-session directive inside the bot chat:

```
/think stream
```

This sets `thinkingLevel: stream` for the current session — the agent emits live `<think>` tokens as it reasons.

**Other values:**
- `/think on` — think but don't show reasoning tokens
- `/think off` — disable thinking entirely for this session

The per-session level overrides `thinkingDefault` from the config.

## streamMode Is Not the Issue

The `channels.telegram.streamMode` setting controls how *regular responses* are delivered:

| Value | Behavior |
|-------|----------|
| `off` | Send full response when complete |
| `partial` | Stream incrementally as tokens arrive (default) |
| `block` | Send complete blocks at a time |

`streamMode` does **not** control thinking token visibility. Keep it as `"partial"` for best responsiveness.

## Config Quick Reference

```json
{
  "agents": {
    "defaults": {
      "thinkingDefault": "medium"
    }
  },
  "channels": {
    "telegram": {
      "streamMode": "partial"
    }
  }
}
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Setting `streamMode: "full"` | Not a valid value — will break the gateway. Valid: `off`, `partial`, `block` |
| Setting `thinkingDefault: "stream"` | Not valid at config level. Use `/think stream` in chat |
| Expecting thinking without enabling it | Set `thinkingDefault` to anything except `off` |
| Thinking shows in some sessions but not others | Per-session `thinkingLevel` overrides config default; use `/think stream` to re-enable |
