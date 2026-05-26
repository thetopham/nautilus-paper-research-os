# Quant Math Roadmap

Study leads:

- <https://www.youtube.com/watch?v=A5w-dEgIU1M>
- <https://www.youtube.com/watch?v=KZeIEiBrT_w>

Working interpretation:

- Black-Scholes / dynamic hedging = options pricing and risk replication;
- Markov chains = observable state transition probabilities;
- Hidden Markov Models = latent market-regime inference;
- interest rates = discounting, curves, pricing environment, and macro/regime context.

This roadmap is for product direction, not immediate live trading.

## Practical order

### 1. Markov chains — visible regime transitions

Goal: estimate how often observable market states transition into other states.

Example states:

```text
chop -> chop
chop -> breakout
trend -> trend
trend -> reversal
high_vol -> high_vol
high_vol -> compression
```

Candidate features:

- return sign and magnitude;
- ATR percentile;
- EMA slope;
- distance from VWAP;
- volume percentile;
- efficiency ratio;
- spread/liquidity if available.

Project use:

- regime-conditioned replay reports;
- trade filters by transition probability;
- stop adding strategy rules blindly when transition evidence is weak.

### 2. Hidden Markov Models — latent regime brain

Goal: infer hidden states from observed market data.

Example hidden states:

```text
state_0 = chop / mean-reverting noise
state_1 = low-vol trend
state_2 = high-vol impulse / reversal risk
```

Inputs:

- returns;
- realized volatility;
- ATR percentile;
- EMA slope;
- volume;
- distance from VWAP;
- orderbook imbalance later.

Outputs:

- state probability vector per bar/tick;
- most likely state;
- transition matrix;
- state-conditioned expectancy.

Trading use:

- block trades in chop;
- reduce size in high-vol/reversal state;
- allow trend setups in low-vol trend;
- tag every replay/paper trade with regime state at entry/exit.

Implementation stance:

- start offline and replay-only;
- do not let HMM directly trade;
- require walk-forward validation before paper-live use.

### 3. Dynamic hedging — options risk brain

Goal: understand option PnL and hedging behavior, especially for future IB options paper research.

Core concepts:

- delta: first-order exposure to underlying;
- gamma: how delta changes as underlying moves;
- theta: time decay;
- vega: volatility exposure;
- implied volatility vs realized volatility;
- hedge frequency and transaction cost drag.

Project use:

- paper-only options strategy simulations;
- delta-neutral strategy review;
- risk dashboard cards:
  - net delta;
  - gamma exposure;
  - theta/day;
  - vega exposure;
  - hedge count;
  - hedge slippage;
  - PnL split by option legs vs hedges.

Safety stance:

- no live options execution in v1;
- broker-paper only after internal paper simulator is stable;
- all hedge orders remain paper rows until explicitly approved.

### 4. Interest rates — pricing environment

Goal: add correct pricing context for options/fixed-income later.

Use cases:

- Black-Scholes risk-free rate input;
- discounting future cash flows;
- yield curve state as macro regime feature;
- options/futures carry context.

V1 simplification:

- use configurable flat risk-free rate for option-pricing experiments;
- store rate source/provenance in run metadata;
- do not overbuild curve infrastructure before options data exists.

## First project version: Market Regime Model v1

Scope: offline/replay only.

Input table:

```text
bars or market_features
```

Feature columns:

```text
ts_event
instrument_id
return_1
return_5
atr_percentile
ema_slope
volume_percentile
distance_from_vwap
efficiency_ratio
```

Output table:

```text
regime_states
```

Fields:

```text
id
ts_event
instrument_id
model_version
state_label
state_probabilities
transition_probabilities
features
```

Replay integration:

- annotate each candidate and executed trade with entry regime;
- summarize R by regime;
- compare strategy performance with/without regime filter;
- report state transition counts and sample size.

Hermes review questions:

1. Which regime produced most of the PnL?
2. Which regime produced most drawdown?
3. Does the model block more losers than winners?
4. Is the effect stable out-of-sample?
5. Did the model reduce trade count too far?

## Acceptance gates before paper-live

A regime model can influence paper-live only if:

- it was trained/tested chronologically;
- it survives out-of-sample replay;
- it improves drawdown or expectancy after costs;
- it does not depend on lookahead features;
- it has a fallback state when features are stale/missing;
- Hermes can explain the change in a research note.

## Non-goals for now

- no autonomous HMM-driven execution;
- no live hedging;
- no production options pricing engine;
- no complex yield-curve stack before option-chain data exists.
