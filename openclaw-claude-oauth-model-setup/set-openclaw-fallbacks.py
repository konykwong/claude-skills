#!/usr/bin/env python3
"""Set or update agents.defaults.model.primary and fallbacks in ~/.openclaw/openclaw.json."""
import json
import os

path = os.path.expanduser("~/.openclaw/openclaw.json")
with open(path) as f:
    c = json.load(f)

c.setdefault("agents", {}).setdefault("defaults", {}).setdefault("model", {})
m = c["agents"]["defaults"]["model"]

# Keep existing primary if set, else default
m.setdefault("primary", "anthropic/claude-sonnet-4-5")

# Set fallbacks (only if not already present, so we don't overwrite custom list)
if not m.get("fallbacks"):
    m["fallbacks"] = [
        "anthropic/claude-haiku-4-5",
        "openrouter/deepseek/deepseek-v3.2",
        "openrouter/moonshotai/kimi-k2.5",
    ]
else:
    # Ensure common fallbacks exist
    wanted = ["anthropic/claude-haiku-4-5", "openrouter/deepseek/deepseek-v3.2", "openrouter/moonshotai/kimi-k2.5"]
    for w in wanted:
        if w not in m["fallbacks"]:
            m["fallbacks"].append(w)

with open(path, "w") as f:
    json.dump(c, f, indent=2)

print("primary:", m["primary"])
print("fallbacks:", m["fallbacks"])
