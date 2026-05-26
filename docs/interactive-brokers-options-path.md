# Interactive Brokers Options Path

Sources:

- <https://nautilustrader.io/docs/nightly/integrations/ib/>
- <https://www.interactivebrokers.com/campus/ibkr-quant-news/handling-options-chains/>
- <https://interactivebrokers.github.io/tws-api/option_computations.html>

## Why IB is likely the US-compatible options path

Bybit options are likely unavailable or unsuitable for a US-based user. Interactive Brokers is a more plausible path for US-listed equity/index/options research and paper trading.

IB should be treated as the primary candidate for:

- US equity option-chain discovery;
- live option quotes and Greeks;
- paper-account plumbing later;
- option strategy paper simulation;
- eventual broker-paper validation after internal paper is stable.

## NautilusTrader IB integration notes

NautilusTrader has an Interactive Brokers adapter using TWS API / `ibapi`.

The integration docs state that the adapter supports:

- stocks, options, futures, currencies, bonds, funds, crypto, commodities, indices, and more;
- TWS, IB Gateway, or Dockerized IB Gateway;
- instrument searches/lookups;
- contract validation/verification;
- complex instrument types including options chains and futures chains;
- historical and live data;
- live trading/order flows when execution config and permissions allow it.

Default ports:

```text
TWS paper:       7497
TWS live:        7496
IB Gateway paper: 4002
IB Gateway live:  4001
```

For this project, prefer **read-only** IB Gateway/TWS access first. If using Dockerized IB Gateway later, set `read_only_api=True` until paper-broker execution is explicitly approved.

## Installed package state

The current project venv has the IB extras installed:

```bash
uv pip install --python /home/matt/venvs/nautilus-perspective/bin/python 'nautilus_trader[ib,docker]'
```

Installed support packages include:

- `nautilus-ibapi`
- `docker`
- `requests`

## IB option-chain discovery workflows

There are two likely routes.

### Route A — Nautilus IB adapter

Use NautilusTrader's IB adapter for instrument lookup and chain support where available. This is preferred once we know the Python adapter surface well enough, because it keeps data in Nautilus domain types.

### Route B — IBKR Client Portal WebAPI contract library

IBKR Campus describes a practical option-chain workflow through Client Portal WebAPI. It requires calling security-definition endpoints in this order:

1. `/iserver/secdef/search`
2. `/iserver/secdef/strikes`
3. `/iserver/secdef/info`

The article recommends building a local contract library ahead of trading rather than repeatedly requesting full chains intraday. That fits our ledger-first design.

A safe implementation would:

1. Search an underlying symbol, e.g. `AAPL`.
2. Pick an exchange/listing and retrieve underlying `conid`.
3. Retrieve available option months.
4. Snapshot underlying last price.
5. Retrieve strikes near the underlying price.
6. Retrieve contract details for selected calls/puts.
7. Persist option contracts to a local/Supabase-compatible table.

## Greeks and market data

IB TWS API returns option Greeks when requesting market data for an option contract with `reqMktData()`.

Returned Greeks include:

- delta;
- gamma;
- theta;
- vega.

Relevant option computation tick types:

- `10`: bid option computation;
- `11`: ask option computation;
- `12`: last option computation;
- `13`: model option computation.

Important caveat: live Greek values require market data subscriptions for both the option contract and the underlying contract.

## Safety boundary for this project

For v1, IB usage should be:

- read-only chain discovery;
- read-only quotes/Greeks if subscriptions exist;
- internal paper simulation only;
- no IB order submission;
- no live account order routes;
- no credentials committed to repo or printed in logs.

If/when broker-paper validation is approved, it should be a separate mode:

```text
PAPER_BROKER
```

with explicit config gates, account IDs, read-only disabled deliberately, and a smoke test proving it uses IB paper endpoints only.

## Proposed schema additions

Future migration should add:

```text
option_underlyings
option_contracts
option_chain_snapshots
option_greeks_ticks
paper_option_legs
paper_delta_hedges
```

Minimum fields for `option_contracts`:

```text
id
created_at
source
underlying_symbol
underlying_conid
conid
local_symbol
exchange
currency
right
strike
expiration
multiplier
metadata
```

Minimum fields for `option_greeks_ticks`:

```text
id
created_at
ts_event
contract_id
underlying_price
bid_iv
ask_iv
model_iv
delta
gamma
vega
theta
option_price
payload
```

## Recommended next implementation step

Do not jump directly into IB Gateway credentials. First add offline/local support:

1. Add schema tables for option contracts and Greeks ticks.
2. Add a fixture-based importer for a tiny synthetic option chain.
3. Build a Perspective options-chain dashboard from local fixture data.
4. Only then add a read-only IB chain collector behind an explicit command.

This keeps the UI/data model stable before dealing with IB sessions, market-data entitlements, or gateway auth.
