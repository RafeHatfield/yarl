📘 MODEL SELECTION GUIDE (Cursor + Codex + ChatGPT)

A practical reference for day-to-day development in rlike

🎯 Purpose

This guide helps choose the right AI model for each development task across:

Cursor

ChatGPT Codex (repo-aware container model)

Grok (Cursor)

GPT models (Cursor)

It optimizes for:

Quality

Cost efficiency

Development speed

Stability

Maintainability

🧭 FLOWCHART: Which model should I use?
                 ┌──────────────────────────┐
                 │    What are you doing?   │
                 └──────────────┬───────────┘
                                │
   ┌────────────────────────────┼─────────────────────────────┐
   │                            │                             │
Small code fix?         Multi-file change?            Understanding why?
(<2 files, local)       (3–10 files, risky)           (architectural Q)
   │                            │                             │
   ▼                            ▼                             ▼
Use **Haiku** non-thinking   Use **Sonnet** non-thinking   Use **Sonnet THINKING**
(Fast, cheap)                (High accuracy, safe)         (Deep reasoning)
                                │
                                ▼
                     Messy/systemic problem?
                   “What is the clean design?”
                                │
                                ▼
              Use **Sonnet THINKING**, then implement
                 with Haiku/Sonnet non-thinking.

                ┌──────────────────────────────┐
                │ Large change? (>10 files)    │
                └──────────────┬───────────────┘
                               ▼
                     Use **Codex** in ChatGPT

                 ┌────────────────────────────┐
                 │ Simple? Non-critical?      │
                 │ Want to save cost?         │
                 └──────────────┬─────────────┘
                                ▼
                        Use **Grok** (free)



🧩 MODEL CHEAT-SHEET (DETAILED)

This is the definitive guide for choosing models across your tools.

🔷 CLAUDE (Cursor)
Haiku 4.5 (non-thinking) — Default for code

Fastest, cheapest, reliable.

Use when:

Small bug fix

Tiny refactor

Editing 1–3 files

Updating tests

Adding small behavior

Low-risk iteration

80–90% of daily tasks

Avoid for:
Complex architectural edits, multi-file systemic changes.

Haiku 4.5 THINKING — Analysis mode

Use for explanation, not code changes.

Use when:

“Explain this subsystem.”

“What’s causing this bottleneck?”

“Map out the renderer flow.”

Do NOT use for code diffs.

Sonnet 4.5 (non-thinking) — High-precision code work

Best model for critical changes.

Use when:

Multi-file diffs (3–10 files)

High-risk systems (renderer, turn engine, AI, soak harness)

Changes span multiple modules

Modifying pipelines or orchestration

Telemetry integration

Bot behavior / auto-explore flow

Anywhere correctness matters

Sonnet 4.5 THINKING — Your senior architect

Only use when planning or reasoning deeply.

Use when:

Designing a subsystem

Large architectural decisions

Understanding brittle code

Decomposing complex behavior

Multi-step strategy design

Then implement with Haiku/Sonnet non-thinking.

🟥 GPT MODELS (Cursor)

GPT-4.1 / 4.1-Mini inside Cursor:

They work

But Claude models outperform them at code

GPT-4.1 is slower, noisier, and more expensive for similar results

Recommendation:
🔶 Avoid GPT in Cursor unless Claude is down.
Use Codex in ChatGPT instead for big work.

💠 Grok (Cursor)

Grok is currently free and useful for:

Tiny edits

Quick patches

Rewriting docstrings

Cleaning up formatting

Extremely local changes

Fast iteration when low-risk

Avoid Grok for:

Anything involving:

rendering

AI/turn mechanics

input pipeline

engine systems

multi-file coordination

If it would annoy you later → use Haiku.

🟦 Codex (ChatGPT)

(Repo-aware, container-based, full-context model)

Codex is:

Cheaper than Sonnet for big tasks

Much deeper reasoning than Haiku

Excellent for whole-repo operations

Ideal for multi-file consistency

Very stable for large diffs

Great for debugging across modules

Perfect for architectural rewrites

Use Codex when:

You have >10 files to touch

You need cross-module consistency

You want to debug multi-step behavior

Cursor context limit is blocking you

You want a cheaper version of Sonnet for big tasks

Examples:

Renderer architecture cleanup

ECS-wide refactor

Game loop/tick overhaul

Save/Load & serialization refactor

Inventory/state manager redesign

Complex pipeline instruments

Multi-module test generation

Cost-effective + accurate = ideal for foundation work.

🧪 WHEN TIRED — the ultra-short guide
➤ Small fix → Haiku (non-thinking)
➤ Medium multi-file change → Sonnet (non-thinking)
➤ Large repo-wide change → Codex (ChatGPT)
➤ Architecture reasoning → Sonnet (thinking)
➤ Tiny/trivial change → Grok
➤ Avoid GPT unless Claude unavailable
📁 Suggested Repo Location

