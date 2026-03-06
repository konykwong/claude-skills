---
name: openclaw-claude-oauth-model-setup
description: Use when setting up Anthropic Claude as the primary model in openclaw via OAuth token, or when configuring model priority with free-tier fallbacks in openclaw running inside Docker.
---

# OpenClaw: Claude OAuth Setup + Model Priority

## Overview

OpenClaw supports Anthropic as a provider using an OAuth token (the `sk-ant-oat01-` token from Claude Code or Claude.ai). This is the simplest way to use Claude as the primary model without managing an API key. Free-tier fallback models (Kimi K2.5, OpenRouter free) can be chained so the agent degrades gracefully when the primary is unavailable.

## Step 1 — Run the configure wizard

Run this inside the Docker container (interactive TTY required):

```bash
docker exec -it openclaw-gateway node /app/dist/index.js configure
```

When prompted:
- Select **Anthropic** as provider
- Choose **OAuth / token** mode
- Paste your `sk-ant-oat01-` token (from `~/.claude/.credentials.json` on the machine running Claude Code)
- Accept defaults for profile name → `anthropic:default`

The token is saved to:
```
~/.openclaw/agents/main/agent/auth-profiles.json
```

## Step 2 — Add auth profile to openclaw.json

Edit `~/.openclaw/openclaw.json` and add the profile under `auth.profiles`:

```json
{
  "auth": {
    "profiles": {
      "anthropic:default": {
        "provider": "anthropic",
        "mode": "token"
      }
    }
  }
}
```

The `configure` wizard may do this automatically. Verify it's present:

```bash
python3 -c "
import json
cfg = json.load(open('/home/<user>/.openclaw/openclaw.json'))
print(json.dumps(cfg.get('auth', {}), indent=2))
"
```

## Step 3 — Set primary model + fallbacks

Edit `agents.defaults.model` in `~/.openclaw/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-opus-4-6",
        "fallbacks": [
          "moonshot/kimi-k2.5",
          "orfree/qwen/qwen3-coder:free",
          "orfree/openrouter/free",
          "orfree/meta-llama/llama-3.3-70b-instruct:free"
        ]
      }
    }
  }
}
```

Or with a Python script (safer for JSON editing):

```bash
python3 << 'EOF'
import json, shutil

path = "/home/<user>/.openclaw/openclaw.json"
shutil.copy(path, path + ".bak")

with open(path) as f:
    cfg = json.load(f)

cfg["agents"]["defaults"]["model"] = {
    "primary": "anthropic/claude-opus-4-6",
    "fallbacks": [
        "moonshot/kimi-k2.5",
        "orfree/qwen/qwen3-coder:free",
        "orfree/openrouter/free",
        "orfree/meta-llama/llama-3.3-70b-instruct:free"
    ]
}

with open(path, "w") as f:
    json.dump(cfg, f, indent=2)

print("Primary:", cfg["agents"]["defaults"]["model"]["primary"])
print("Fallbacks:", cfg["agents"]["defaults"]["model"]["fallbacks"])
EOF
```

Replace `<user>` with the actual home directory username.

## Step 4 — Restart and verify

```bash
docker restart openclaw-gateway
docker exec openclaw-gateway node /app/dist/index.js doctor
```

Doctor should show no auth errors and confirm the primary model.

## Available Anthropic OAuth Models

| Model ID | Description |
|----------|-------------|
| `anthropic/claude-opus-4-6` | Most capable, highest context |
| `anthropic/claude-opus-4-5` | Previous Opus |
| `anthropic/claude-sonnet-4-5` | Balanced speed/quality |
| `anthropic/claude-haiku-4-5` | Fastest, lowest cost |

## Getting the OAuth Token

The OAuth token is on the machine where Claude Code is installed:

```bash
cat ~/.claude/.credentials.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('oauthToken', d.get('token', 'not found')))"
```

Token format: `sk-ant-oat01-...` (long string). Do **not** use `sk-ant-api01-` (API keys) — they are a different format.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using an API key (`sk-ant-api01-`) instead of OAuth token | Get the OAuth token from `~/.claude/.credentials.json`, format starts with `sk-ant-oat01-` |
| `auth-profiles.json` not found at `~/.openclaw/agents/main/` | Actual path is `~/.openclaw/agents/main/agent/auth-profiles.json` (extra `agent/` subdirectory) |
| `configure` wizard not interactive | Must use `-it` flag: `docker exec -it openclaw-gateway ...` |
| Primary model not switching | Restart gateway after editing config; verify with `doctor` |
| Fallback `orfree/` models not working | These require an OpenRouter free-tier API key configured separately |
