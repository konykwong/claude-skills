# OpenClaw multi-agent + Telegram — Full reference

Use this when implementing either option or when another OpenClaw instance needs a copy-paste guide. Paths use `~/.openclaw`; in Docker the container often uses `/home/node/.openclaw`.

---

## Option A — Single bot (Chief of Staff delegates)

### 1. Telegram config

One bot token. No `accounts` needed unless you add Option B later.

```json5
"channels": {
  "telegram": {
    "enabled": true,
    "botToken": "YOUR_SINGLE_BOT_TOKEN",
    "dmPolicy": "allowlist",
    "allowFrom": ["TELEGRAM_USER_ID"],
    "groupPolicy": "allowlist",
    "groups": { "*": { "requireMention": true } }
  }
}
```

All DMs and allowed groups go to the default agent (main). No bindings required for Telegram.

### 2. agents.list (main + specialists)

Main is default; specialists get their own workspace and optional per-agent `model`.

```json5
"agents": {
  "defaults": {
    "model": { "primary": "anthropic/claude-opus-4-6", "fallbacks": ["moonshot/kimi-k2.5", "orfree/qwen/qwen3-coder:free"] },
    "workspace": "/home/node/.openclaw/workspace"
  },
  "list": [
    { "id": "main", "default": true, "name": "Chief of Staff", "workspace": "/home/node/.openclaw/workspace" },
    {
      "id": "coding",
      "name": "Coding",
      "workspace": "/home/node/.openclaw/workspace-coding",
      "model": { "primary": "moonshot/kimi-k2.5", "fallbacks": ["orfree/qwen/qwen3-coder:free", "orfree/openrouter/free"] }
    },
    {
      "id": "alerts",
      "name": "Alerts",
      "workspace": "/home/node/.openclaw/workspace-alerts",
      "model": { "primary": "orfree/qwen/qwen3-coder:free", "fallbacks": ["moonshot/kimi-k2.5", "orfree/openrouter/free"] }
    },
    {
      "id": "trading",
      "name": "Trading",
      "workspace": "/home/node/.openclaw/workspace-trading",
      "model": { "primary": "moonshot/kimi-k2.5", "fallbacks": ["anthropic/claude-opus-4-6", "orfree/deepseek/deepseek-r1-0528:free"] }
    }
  ]
}
```

Use `provider/model` ids that exist in your `models.providers`. Omit `model` on an agent to use `agents.defaults.model`.

### 3. Chief of Staff delegation

In the **main** workspace, add to `AGENTS.md` (or SOUL.md):

```markdown
## Delegation (Chief of Staff)

You are the Chief of Staff. When a task clearly fits a specialist (coding, alerts, trading, biz, personal, marketing), delegate via `sessions_spawn` to that agent. **Before delegating:** read `docs/agent-roster.md` for when-to-delegate rules, and call `agents_list` to see which agents are configured — only spawn to agents that exist. If an agent isn’t configured, say so and handle what you can yourself or suggest an alternative.
```

Create `docs/agent-roster.md` in the main workspace listing each specialist and when to delegate (see “Roster template” below).

### 4. Workspace and agent dirs per specialist

For each specialist (e.g. coding, alerts, trading):

- **Workspace:** `~/.openclaw/workspace-<id>/` with at least `SOUL.md` and `AGENTS.md` (role and constraints).
- **Agent dir:** `~/.openclaw/agents/<id>/agent/auth-profiles.json` (copy or share credentials from main so the agent can call APIs); `~/.openclaw/agents/<id>/sessions/sessions.json` initially `{}`.

Docker: if the whole `~/.openclaw` is mounted, workspace and agent dirs are visible; no extra volume mounts needed.

### 5. No extra tokens

Option A uses **one** Telegram bot token. The bot can spin off the other agents itself via `sessions_spawn`; no other bots needed.

---

## Option B — Multiple bots

### 1. Create bots and get tokens

In Telegram, BotFather: create one bot per agent (e.g. @YourChiefBot, @YourCodingBot, @YourTradingBot). Copy each token.

### 2. Telegram accounts + bindings

Map each bot (account) to an agent.

```json5
"channels": {
  "telegram": {
    "enabled": true,
    "accounts": {
      "default": { "botToken": "TOKEN_FOR_CHIEF_BOT" },
      "coding":  { "botToken": "TOKEN_FOR_CODING_BOT" },
      "trading":  { "botToken": "TOKEN_FOR_TRADING_BOT" }
    },
    "dmPolicy": "allowlist",
    "groupPolicy": "allowlist",
    "groups": { "*": { "requireMention": true } }
  }
},
"bindings": [
  { "agentId": "main",   "match": { "channel": "telegram", "accountId": "default" } },
  { "agentId": "coding", "match": { "channel": "telegram", "accountId": "coding" } },
  { "agentId": "trading","match": { "channel": "telegram", "accountId": "trading" } }
]
```

Users message or @mention the bot they want; that message is routed to the bound agent. No delegation needed for “talk to X.”

### 3. agents.list

Same as Option A: main + specialists with workspaces and per-agent `model`. Bindings only affect routing; they don’t change the agent list.

### 4. Groups

Add all bots to the same group. In BotFather for each bot: enable “Allow Groups?” and turn off “Group Privacy” so the bot sees messages. Users @CodingBot or @TradingBot to choose who answers.

---

## Per-agent models

Each entry in `agents.list` can have its own `model`:

```json5
"model": {
  "primary": "provider/model-id",
  "fallbacks": ["provider/model-2", "provider/model-3"]
}
```

Agents without `model` use `agents.defaults.model`. Model ids must exist under `models.providers` (e.g. `moonshot`, `orfree`, `anthropic`).

---

## Roster template (for Chief of Staff)

Save as `docs/agent-roster.md` in the main workspace. Chief of Staff reads this before delegating.

```markdown
# Agent Roster — When to Delegate

Only spawn to agents returned by `agents_list`. If an agent isn’t configured, say so.

| User intent / topic        | Delegate to |
|----------------------------|------------|
| Code, scripts, dev, repos  | coding     |
| Markets, backtest, signals | trading    |
| Alerts, cron, "notify when"| alerts     |
| Biz, contracts, ops, legal | biz        |
| Personal, calendar, life   | personal   |
| Content, campaigns, growth | marketing  |
| Everything else / unclear | Handle yourself (main) |

## trading

- **When:** Markets, signals, backtests, strategy. **Constraints:** No real orders or moving funds without explicit user confirmation.
## coding

- **When:** Code, scripts, debugging, devops.
## alerts

- **When:** Cron, monitoring, "tell me when…".
```

Expand with more rows and per-agent notes as needed.

---

## Checklist (either option)

- [ ] `agents.list` has main (default) + specialist ids; each has `workspace`; optional `model` per agent.
- [ ] Each specialist has workspace dir + `agents/<id>/agent/auth-profiles.json` + `agents/<id>/sessions/sessions.json` (e.g. `{}`).
- [ ] Option A: main’s AGENTS.md has delegation section; `docs/agent-roster.md` exists; Chief of Staff uses `agents_list` and `sessions_spawn`.
- [ ] Option B: `channels.telegram.accounts` has one entry per bot; `bindings` map each `accountId` to `agentId`.
- [ ] Gateway restarted or config reloaded after edits.
