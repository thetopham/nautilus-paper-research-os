# Bybit Options Path

Sources:

- <https://nautilustrader.io/docs/latest/tutorials/options_data_bybit/>
- <https://nautilustrader.io/docs/latest/tutorials/delta_neutral_options_bybit/>

## Why these tutorials matter

These tutorials point to a compelling eventual target for Nautilus Paper Research OS: options-aware live paper research, especially BTC options Greeks, option-chain snapshots, and delta-neutral strategy evaluation.

The immediate value is **data and replay/paper research**, not live execution.

## Tutorial takeaways

### Options data and Greeks

The Bybit options data tutorial demonstrates Rust-only NautilusTrader v2 `LiveNode` examples for:

- live Bybit option Greeks;
- aggregated option-chain snapshots;
- `DataActor` callbacks;
- instrument discovery from the cache;
- subscribing to `OptionGreeks` per option contract;
- subscribing to `OptionChainSlice` style expiry-series snapshots.

Bybit ticker updates expose:

- delta;
- gamma;
- vega;
- theta;
- mark IV;
- bid IV;
- ask IV;
- underlying price;
- open interest.

Important implementation pitfall from the tutorial: collect owned instrument data from the cache into a local vector and drop the cache borrow before calling subscription methods. The cache uses interior mutability, and subscription methods may need their own borrow.

### Delta-neutral options strategy

The delta-neutral tutorial demonstrates a live short OTM BTC options strangle on Bybit, hedged with the BTCUSDT linear perpetual.

The strategy:

- selects OTM call/put strikes at startup;
- enters short option legs using Bybit IV-priced limit orders (`order_iv`);
- tracks portfolio delta using Bybit option Greeks;
- hedges with market orders on `BTCUSDT-LINEAR.BYBIT` when delta breaches a threshold;
- hydrates existing positions from cache at startup and continues hedging them.

Portfolio delta formula:

```text
portfolio_delta = call_delta * call_position
                + put_delta * put_position
                + hedge_position
```

Critical warning: the tutorial is a live mainnet strategy. Setting `enter_strangle: false` only disables initial option entry orders. If existing positions are hydrated, the strategy can still submit hedge orders on the perpetual when delta breaches the threshold.

## Safety interpretation for this project

Do **not** run the delta-neutral tutorial as-is inside this project. It is live-mainnet oriented and can trade real money if credentials and existing positions are present.

For Nautilus Paper Research OS, the safe path is:

1. Start with read-only options data ingestion.
2. Persist option Greeks and option-chain snapshots to the local ledger/Supabase-compatible schema.
3. Build Perspective views for option chains, IV, Greeks, and portfolio delta.
4. Implement an internal paper-only simulator for strangle and hedge decisions.
5. Record paper orders/fills/positions using explicit fill models.
6. Let Hermes analyze paper/replay behavior and propose experiments.
7. Keep live execution and broker paper endpoints out of scope until explicitly approved.

## Installed package check

The current Python venv has NautilusTrader with these modules present:

- `nautilus_trader.adapters.bybit`
- `nautilus_trader.model.greeks`
- `nautilus_trader.model.data`

The tutorials themselves are Rust-only v2 examples, so direct reuse may require either:

- cloning the NautilusTrader source repo and running Rust examples; or
- using Python-exposed Bybit/options components where available; or
- treating Nautilus as the installed Python engine for the early ledger/dashboard spine while deferring Rust `LiveNode` integration.

## Proposed project phases for Bybit options

### Phase A — read-only data capture

- Add tables for option Greeks and option-chain snapshots.
- Add a bounded, read-only collector design.
- No trading permissions required.
- No order code.

### Phase B — Perspective options dashboard

Show:

- option chain by expiry/strike;
- mark/bid/ask IV;
- delta/gamma/vega/theta;
- open interest;
- underlying price;
- latest update age.

### Phase C — internal paper delta-neutral simulator

Simulate:

- short call/put selection;
- synthetic entry fills;
- portfolio delta drift;
- hedge paper orders;
- rehedge threshold behavior;
- fees/slippage/latency assumptions.

All orders/fills remain internal paper rows. No Bybit trading API path.

### Phase D — replay and research loop

Hermes reviews:

- hedge frequency;
- delta exposure time;
- PnL by option legs vs hedge;
- IV/risk regimes;
- fill-model sensitivity;
- whether the idea deserves further paper testing.

## V1 deferral

For the current first milestone, keep these tutorials as architecture input only. The immediate implementation remains:

```text
local ledger -> Perspective dashboard -> internal paper spine -> read-only data collectors later
```
