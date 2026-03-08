---
name: openclaw-multi-agent-telegram
description: Documents how to set up multiple OpenClaw agents with Telegram (single bot vs multiple bots), Chief of Staff delegation, per-agent models, and roster. Use when configuring OpenClaw multi-agent, adding specialist agents, or choosing between one bot or several bots for Telegram.
---

# OpenClaw multi-agent + Telegram

Two ways to run multiple agents with Telegram. Use this skill when setting up or explaining the setup to another OpenClaw instance.

---

## The two options

| | **Option A — Single bot** | **Option B — Multiple bots** |
|---|---------------------------|------------------------------|
| **Tokens** | One Telegram bot token | One token per agent (e.g. @ChiefBot, @CodingBot, @TradingBot) |
| **Who answers** | Chief of Staff (main) answers every message; delegates to specialists via `sessions_spawn` | User picks agent by messaging or @mentioning the right bot |
| **Best for** | One main contact; you’re fine with the Chief triaging and delegating | Direct access to a specific agent without going through the Chief |
| **Complexity** | Simpler: one bot, one token, no extra bindings | More: several bots in BotFather, `channels.telegram.accounts`, bindings per account |
| **In groups** | One bot in the group; Chief delegates in the background | Several bots in the group; users @CodingBot vs @TradingBot to choose |

**Recommendation:** Start with **Option A**. Add Option B only if you want explicit “this bot = this agent” and don’t mind managing multiple tokens and bindings.

---

## Option A — Single bot (Chief of Staff delegates)

1. **One bot, one token** in `channels.telegram.botToken` (or `channels.telegram.accounts.default.botToken`).
2. **agents.list** includes main (default) + specialists (e.g. coding, alerts, trading). All use the same gateway and same bot.
3. **All Telegram traffic** goes to main (Chief of Staff). Main uses `agents_list` to see which agents exist and `sessions_spawn` to hand off tasks to coding/alerts/trading.
4. **Chief of Staff instructions:** In main’s `AGENTS.md` (or SOUL.md), add: before delegating, read the roster (e.g. `docs/agent-roster.md`) and call `agents_list`; only spawn to agents that exist.
5. **No extra bindings** for Telegram — default routing is “all DMs → main.”

Per-agent models: set `agents.list[].model` (primary + fallbacks) per agent; main can use `agents.defaults.model`.

---

## Option B — Multiple bots

1. **Create one bot per agent** in BotFather; get a token for each.
2. **Config:** Under `channels.telegram.accounts` add an entry per bot (e.g. `default`, `coding`, `trading`) with `botToken` for each.
3. **Bindings:** In `bindings`, map each Telegram account to an agent, e.g. `{ "agentId": "main", "match": { "channel": "telegram", "accountId": "default" } }`, `{ "agentId": "coding", "match": { "channel": "telegram", "accountId": "coding" } }`.
4. **Groups:** Add all bots to the same group; users @mention the bot they want. Each bot only sees messages to it (and group messages if group privacy is off).
5. **No delegation required** for “talk to X” — user chooses by which bot they message or @mention.

Per-agent models: same as Option A; each agent can have its own `model` in `agents.list`.

---

## Quick checklist (either option)

- [ ] `agents.list` has main (default) + specialist ids; each has `workspace` (and optionally `model`).
- [ ] Each specialist has its own workspace dir and `agents/<id>/agent/` (e.g. auth-profiles, sessions).
- [ ] Option A: main’s AGENTS.md/SOUL.md tells Chief of Staff to read roster + `agents_list` before delegating; roster doc lists when to delegate to whom.
- [ ] Option B: `channels.telegram.accounts` has one entry per bot; `bindings` map each `accountId` to an `agentId`.
- [ ] Gateway restarted (or config hot-reloaded) after changes.

---

## Full reference

Step-by-step config, `agents.list` and binding examples, per-agent model snippets, roster template, and workspace layout are in [reference.md](reference.md). Read it when implementing or when another OpenClaw instance needs a full copy-paste guide.
