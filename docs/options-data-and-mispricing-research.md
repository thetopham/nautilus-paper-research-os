# Options Data And Mispricing Research

Purpose: choose data sources and build a research path for finding option dislocations without jumping straight into live trading.

## What we actually need

"Options history" is only the raw material. The research target is:

```text
edge = model_price - market_price
```

or, at the volatility level:

```text
edge = forecast_realized_vol_or_fair_iv - market_implied_vol
```

Useful scans are usually about:

- implied volatility dislocations
- realized-volatility vs implied-volatility gaps
- skew and wing anomalies
- term-structure weirdness
- earnings/event IV overpricing
- put/call asymmetry
- convexity mispricing
- liquidity/fillability problems
- flow/dealer-positioning proxies

## Data tiers

### Tier 0 — fastest place to test ideas

#### QuantConnect

Use when we want to backtest SPY/SPX/equity/index options quickly without building the entire data lake first.

Pros:

- Integrated historical options in LEAN.
- Option universe filters by expiration, delta, IV, OI, strategy shape, etc.
- Good for proving whether an idea has any backtest signal.

Cons:

- Less ideal if we want full ownership of raw OPRA/microstructure data.
- Research is inside the QuantConnect/LEAN ecosystem unless exported.

Best use here:

- Prototype simple spread/collar/strangle rules.
- Validate whether a mispricing signal is worth building in our own stack.

### Tier 1 — practical API data for our own stack

#### MarketData.app

Best for easy chain ingestion and lightweight research.

Observed features from docs:

- REST API and Google Sheets add-on.
- Real-time OPRA options quotes.
- Historical end-of-day quotes.
- Full option chains, expirations, strikes, lookup.
- Real-time quotes include IV and Greeks.
- Chain endpoint has useful filters: expiration, weekly/quarterly, delta ranges, bid/ask bounds, spread filters, volume, and open interest.

Caveat:

- Their own docs indicate historical EOD Greeks/IV support may be limited or evolving. Verify before depending on historical Greeks.

Best use here:

- First local chain downloader.
- Watchlist scans for SPY/QQQ/AAPL/MSFT/etc.
- Simple EOD quote/chain snapshots.

#### Alpaca historical options API

Best if we already use Alpaca and want simple onboarding.

Observed features from docs:

- `OptionHistoricalDataClient`.
- Historical option bars.
- Historical trades up to a documented lag.
- Latest quote/trade.
- Option snapshots include latest trade/quote plus IV/Greeks for current snapshots.

Caveat:

- Verify exact historical IV/Greeks depth before building research around it.
- Better for convenience than institutional-grade vol-surface history.

Best use here:

- Simple current chain/snapshot ingestion.
- Broker-adjacent paper experiments.

#### Polygon.io / Massive

Candidate for retail-quant friendly options APIs.

Expected/useful shape:

- Historical option chains.
- Snapshots with Greeks/IV.
- Minute/tick data depending on plan.
- Popular Python/API ecosystem.

Caveat:

- Verify plan-level access, history depth, OPRA licensing, and whether Greeks are historical or snapshot-only.

Best use here:

- Retail-friendly API prototype if plan economics are acceptable.

#### ThetaData

Best retail/prosumer source for richer OPRA-like historical options data.

Observed docs/site claims:

- Complete OPRA coverage since 2012.
- Trade and quote data with IV calculations.
- 1st/2nd/3rd order Greeks: delta, vega, theta, rho, gamma, vanna, charm, speed, zomma, color.
- Tick, 1-second, 1-minute, and EOD granularities.

Caveat:

- More data volume and more implementation complexity than simple chain APIs.

Best use here:

- Serious local research once the schema and scanners are ready.

#### Databento OPRA.PILLAR

Best for quant-grade raw/normalized microstructure.

Observed docs/site facts:

- `OPRA.PILLAR` is consolidated last sale and NBBO across U.S. equity options exchanges.
- Historical availability from `2013-04-01 UTC`.
- 1.6M+ symbols.
- 18 U.S. equity options venues.
- Schemas include trades, OHLCV, definitions, statistics, 1s/1m CBBO, and other normalized data.
- Supports DBN, JSON, CSV.
- Full dataset can be terabytes/day at high granularity.

Caveat:

- Great if we want to build our own pricing/surface/microstructure engine.
- Overkill for first idea validation.
- Must control data scope tightly: one underlying, one date range, filtered expiries/strikes.

Best use here:

- SPY/QQQ/SPX focused research with real quote/trade microstructure.
- Fillability/spread/slippage studies.

### Tier 2 — vol analytics / precomputed surfaces

#### ORATS

Best for precomputed option analytics and vol-surface research.

Observed docs/site facts:

- Live, delayed, and historical EOD options data back to 2007.
- 5,000+ symbols and 500+ indicators.
- Strike-level fields include bid/ask, IV, Greeks, volume, OI, theoretical values, smoothed market values, forecast vol/slope fields, earnings effects, and more.
- ORATS docs explicitly frame edge as comparing implied surface parameters / market values to forecast parameters / theoretical values.

Best use here:

- Mispricing scans without building all surface smoothing from scratch.
- Skew, term structure, earnings IV, and theoretical-value comparisons.

#### IVolatility

Best for historical IV/Greeks datasets and API access.

Observed search/doc snippets:

- Historical options data with IV and Greeks for strikes/expirations.
- Data Cloud API with full chains, IV, Greeks, earnings calendars, and quality filters.

Best use here:

- Similar role to ORATS, likely more processed than Databento but less DIY.

### Tier 3 — institutional / academic

#### OptionMetrics IvyDB

Gold standard for academic/institutional historical options research.

Observed docs/search facts:

- Historical daily option prices, implied volatility, and Greeks.
- IvyDB US is used by hundreds of institutions.
- Decades of EOD options data.

Caveat:

- Likely expensive and sales/academic-license oriented.

Best use here:

- If CU/library access exists, this is ideal for academic-style research.

#### OPRA direct

The source feed.

Caveat:

- Massive and expensive.
- Not the first path for a solo research stack.

Best use here:

- Not v1. Use Databento/ThetaData unless direct OPRA becomes necessary.

## Recommended stack for Matt

### Phase 0 — no subscription yet

- Use QuantConnect for a first strategy sanity check.
- Build local schema and scanners with synthetic/sample option chains.
- Implement Black-Scholes, realized volatility, IV rank, skew slope, term structure, and liquidity filters.

### Phase 1 — easiest owned-data MVP

Pick one of:

1. MarketData.app if we want simple chain snapshots quickly.
2. Alpaca if we want broker-adjacent convenience.
3. Polygon if its plan has the needed historical chains/Greeks at acceptable cost.

Build:

- SQLite/Postgres options database.
- Daily chain snapshots for a small universe: SPY, QQQ, AAPL, MSFT, TSLA, maybe SPX if supported.
- Realized volatility engine.
- Black-Scholes fair-value engine.
- IV rank/percentile.
- Skew and term-structure tracker.
- Perspective dashboard.

### Phase 2 — serious data

Add one of:

- ORATS for processed vol-surface/theoretical-value research.
- ThetaData for deeper OPRA historical quote/trade/Greeks coverage.
- Databento for normalized raw microstructure and fillability studies.

### Phase 3 — research signals

Scans to implement:

#### A. Realized vs implied volatility

```text
if implied_vol >> realized_vol_forecast:
    option/vol may be expensive
```

Use with caution: high IV may be justified by earnings, macro event, borrow/dividend issues, or crash demand.

#### B. Surface anomaly scan

Build/interpolate surface:

```text
IV(strike, expiry)
```

Flag local residuals:

```text
surface_residual = contract_iv - fitted_surface_iv
```

Candidate anomalies:

- isolated IV spike
- broken skew monotonicity
- wing overpriced vs neighbors
- term structure kink

#### C. Model price vs market price

Models:

- Black-Scholes as baseline.
- Dividend/borrow adjusted BS for equities/ETFs.
- Heston/local vol later.
- ML volatility surface later.

Candidate score:

```text
mispricing = market_mid - model_price
edge_after_spread = abs(mispricing) - half_spread - fees/slippage_buffer
```

No trade candidate if edge does not survive spread.

#### D. Earnings/event IV crush

Features:

- days to earnings
- current IV rank
- implied move
- historical post-earnings realized move
- term-structure kink around earnings expiry

Target:

- probability that IV crush exceeds realized move.

#### E. Dealer/flow proxies

Start simple:

- open-interest changes
- volume / OI ratio
- put/call volume asymmetry
- gamma exposure estimate by strike
- vanna/charm proxy if data supports it
- unusual sweep flow only if a data source provides it

## Minimal schema

Tables:

- `option_underlyings`
- `option_contracts`
- `option_chain_snapshots`
- `option_quotes`
- `option_greeks`
- `underlying_bars`
- `realized_volatility`
- `iv_surface_points`
- `surface_fit_runs`
- `mispricing_candidates`
- `research_runs`

Important fields for candidate scoring:

- symbol, expiration, strike, right
- bid, ask, mid, spread_pct
- volume, open_interest
- underlying_price
- iv, delta, gamma, theta, vega
- fitted_iv, surface_residual
- realized_vol_10d, realized_vol_20d, realized_vol_60d
- iv_rank, iv_percentile
- model_price, market_mid, edge, edge_after_spread
- event flags: earnings, ex-dividend, macro/FOMC/CPI if available

## First build recommendation

Do not buy a giant dataset first.

Build this sequence:

1. Add synthetic/sample option-chain fixture to `nautilus-paper-research-os`.
2. Implement Black-Scholes + IV solver.
3. Implement realized-volatility calculator.
4. Implement `scan-options` CLI over fixture/CSV data.
5. Add Perspective dashboard for chain + mispricing candidates.
6. Then test one provider: MarketData.app or Alpaca for easy chain snapshots.
7. Upgrade to ORATS/ThetaData/Databento only after the scanner proves useful.

## Safety rule

Every options idea stays research/paper-only until:

- data source quality is verified
- spreads/liquidity are modeled
- survivorship and event bias are addressed
- edge survives transaction costs
- tail risk is explicitly capped
- results are replayed across multiple regimes
- any live/broker path is separately approved
