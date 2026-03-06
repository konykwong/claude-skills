---
name: openclaw-docker-gateway-pairing
description: Use when openclaw agent inside Docker can't connect to the gateway and logs show "pairing required", "gateway closed (1008)", or "Error: pairing required". Also use when setting up openclaw in a Docker/VM environment for the first time and the agent is blocked from using gateway tools.
---

# OpenClaw Docker Gateway Pairing Fix

## Overview

When openclaw runs inside Docker, the internal agent subprocess connects back to the gateway via WebSocket. The gateway requires device pairing before accepting these connections. On a fresh install or after container recreation, the agent's pairing request lands in `pending.json` but is never approved — leaving it stuck with "pairing required" errors forever.

## Symptoms

- Gateway logs: `gateway connect failed: Error: pairing required`
- Gateway logs: `gateway closed (1008): pairing required`
- Agent tools fail silently or with gateway errors
- Telegram bot responds but can't execute tools
- `~/.openclaw/devices/paired.json` is `{}`
- `~/.openclaw/devices/pending.json` has an entry

## Root Cause

The agent's keypair is persisted at `~/.openclaw/identity/device.json` (mounted into Docker via the `~/.openclaw` volume). On first connection, the agent sends a pairing request which is written to `pending.json`. Without UI approval or manual intervention, it stays pending indefinitely.

## Fix

### Step 1 — Verify the problem

```bash
cat ~/.openclaw/devices/paired.json   # should be {}
cat ~/.openclaw/devices/pending.json  # should have one entry
cat ~/.openclaw/identity/device.json  # confirm deviceId matches pending entry
```

### Step 2 — Approve the pairing

```bash
python3 << 'EOF'
import json, time

with open("/home/<user>/.openclaw/devices/pending.json") as f:
    pending = json.load(f)

approved = {}
for req_id, device in pending.items():
    device["pairedAt"] = int(time.time() * 1000)
    approved[device["deviceId"]] = device

with open("/home/<user>/.openclaw/devices/paired.json", "w") as f:
    json.dump(approved, f, indent=2)

print("Approved:", list(approved.keys()))
EOF
```

Replace `<user>` with the actual home directory user.

### Step 3 — Restart the gateway

```bash
docker restart openclaw-gateway
```

### Step 4 — Verify

```bash
docker logs openclaw-gateway --tail 20
# Should NOT show "pairing required"
# Should show: [gateway] listening on ws://0.0.0.0:18789
```

## Why This Works

- `identity/device.json` is on the mounted volume — the same keypair is reused every container restart
- Approving once is permanent: the same `deviceId` is always used
- `paired.json` is keyed by `deviceId`; the gateway checks it on every connection attempt

## Docker Compose Notes

The `~/.openclaw` directory must be mounted into the container:

```yaml
volumes:
  - ~/.openclaw:/home/node/.openclaw
```

This ensures the keypair and approved pairing persist across container restarts.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Restarting container without approving first | Approve pairing, then restart |
| Deleting `~/.openclaw/identity/device.json` | Agent generates a new keypair; a new pairing request will be created and must be approved again |
| Editing `paired.json` with wrong key format | Key must be `deviceId` (the long hex string), not `requestId` |
| Approving on host but gateway reads container path | Both map to same path via volume mount — it's fine |
