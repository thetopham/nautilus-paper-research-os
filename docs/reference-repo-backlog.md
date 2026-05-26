# Reference Repo Backlog

Purpose: keep starred trading/AI repos as a **reference shelf**, not a distraction from the build.

North-star stack remains:

```text
NautilusTrader + Perspective + Supabase/Postgres + Hermes/Agents
```

Everything below is for patterns to study, not wholesale adoption.

## Build-on / core stack

### NautilusTrader

Role: core replay/live-paper execution engine.

Why:

- serious event-driven trading engine;
- research-to-live parity;
- multi-asset/multi-venue support;
- Interactive Brokers adapter gives a plausible US options path.

Action:

- keep as engine boundary;
- do not reimplement order/account/portfolio semantics in Hermes or Supabase.

### Perspective

Repo: <https://github.com/perspective-dev/perspective>

Metadata snapshot:

- description: data visualization and analytics component for large/streaming datasets;
- license: Apache-2.0;
- active/mature;
- about 10.9k stars at review time;
- Rust/WebAssembly/JavaScript/Python/Jupyter ecosystem.

Role: real-time replay/paper dashboard.

Study/build items:

- streaming table update patterns;
- user-configurable views;
- chart + grid layouts for trade/event feeds;
- Python server integration.

Priority: **highest UI reference**.

## Strong architecture references

### Freqtrade

Repo: <https://github.com/freqtrade/freqtrade>

Metadata snapshot:

- description: free, open-source crypto trading bot;
- Python;
- GPL-3.0;
- about 50.8k stars;
- default branch: `develop`;
- mature ecosystem with WebUI/Telegram/backtesting/strategy workflows.

Role: mature bot operations reference.

Study items:

- config structure;
- strategy lifecycle;
- backtest reports;
- risk/money-management UX;
- operator controls and Telegram/WebUI patterns.

Caution:

- GPL-3.0: study patterns, avoid copying code into this repo unless license implications are intentional.

### Jesse

Repo: <https://github.com/jesse-ai/jesse>

Metadata snapshot:

- description: advanced crypto trading bot written in Python;
- MIT;
- about 7.9k stars;
- active;
- strategy research/backtest/live crypto focus.

Role: cleaner crypto strategy research reference.

Study items:

- strategy class ergonomics;
- backtest/optimization workflow;
- report outputs;
- developer experience.

Priority: below Freqtrade for maturity, above older ML bot repos for cleanliness.

## AI researcher / agent references

### TradingAgents

Repo: <https://github.com/TauricResearch/TradingAgents>

Metadata snapshot:

- description: multi-agent LLM financial trading framework;
- Python;
- Apache-2.0;
- about 79.8k stars;
- homepage/paper: arXiv link;
- topics: agent, finance, llm, multiagent, trading.

Role: AI brain pattern reference.

Study items:

- role decomposition among agents;
- debate/review loops;
- market/news/fundamental/technical analyst separation;
- how to adapt ideas into a **single Hermes researcher loop first**, not a swarm.

Caution:

- do not import multi-agent complexity into v1;
- use as pattern library for prompts/evaluation workflows.

### anthropics/financial-services

Repo: <https://github.com/anthropics/financial-services>

Metadata snapshot:

- Python;
- Apache-2.0;
- about 27.8k stars;
- no description in repo metadata;
- active.

Role: serious financial workflow agent templates.

Study items:

- agent guardrails;
- financial-services workflow examples;
- evaluation patterns;
- auditability and tool-use boundaries.

Priority: high for Hermes workflow design, not trading execution.

### ai-quant-researcher

Repo: <https://github.com/zostaff/ai-quant-researcher>

Metadata snapshot:

- Python;
- created 2026;
- about 87 stars;
- license is `NOASSERTION`/Other.

Role: early research-automation idea reference.

Study items:

- high-level product flow only;
- avoid code reuse until license is understood.

Priority: lower than TradingAgents and Anthropic.

## Quant/risk/data references

### gs-quant

Repo: <https://github.com/goldmansachs/gs-quant>

Metadata snapshot:

- description: Python toolkit for quantitative finance;
- Apache-2.0;
- about 10.5k stars;
- topics: derivatives, risk-management, trading-strategies.

Role: institutional quant/risk reference.

Study items:

- derivatives/risk terminology;
- pricing/risk abstractions;
- options/risk reports;
- portfolio analytics patterns.

Priority: medium/high for options risk brain; not v1 infrastructure.

### finvizfinance

Repo: <https://github.com/lit26/finvizfinance>

Metadata snapshot:

- description: Finviz analysis Python library;
- MIT;
- about 1.4k stars;
- stock screener/news/fundamental/technical scraping.

Role: auxiliary US equities data/screener source.

Study/use items:

- quick universe filters;
- news/fundamental enrichment;
- possible offline research feed.

Priority: low for core infrastructure.

### intelligent-trading-bot

Repo: <https://github.com/asavinov/intelligent-trading-bot>

Metadata snapshot:

- description: automatically generating signals and trading based on ML/feature engineering;
- Python;
- MIT;
- about 1.7k stars;
- crypto/ML signal focus.

Role: older ML feature/signal reference.

Study items:

- feature engineering examples;
- ML signal pipeline shape.

Priority: lower; avoid adopting operational structure before proven useful.

## Review order

1. Perspective dashboard integration patterns.
2. Nautilus IB/options integration docs/examples.
3. Freqtrade operations/reporting UX.
4. Jesse strategy/backtest developer ergonomics.
5. TradingAgents agent-role patterns.
6. anthropics/financial-services guardrails/evals.
7. gs-quant derivatives/risk abstractions.
8. ai-quant-researcher product/research loop ideas.
9. finvizfinance auxiliary screener data.
10. intelligent-trading-bot ML feature reference.

## Rule for this repo

Any reference pulled from these projects must answer one of these questions before implementation:

1. Does it improve the replay engine?
2. Does it improve the paper-live ledger?
3. Does it improve the Perspective dashboard?
4. Does it improve Hermes research review quality?
5. Does it improve safety, auditability, or reproducibility?

If not, it stays in the backlog.
