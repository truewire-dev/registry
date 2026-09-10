# bitstamp

Bitstamp's public v2 REST market data: the tradable market list, per-market tickers, order
books, the trade tape and OHLC candles -- for both the spot markets and the USD-margined
perpetual futures Bitstamp added alongside them. Public, no key.

- Upstream docs: https://www.bitstamp.net/api/
- Endpoints: 5 (5 with recorded examples)
- Coverage: not surveyed against the vendor's documentation; this spec may be a sample
- Source project (core, generated client, tests): authored in this repository; there is no
  separate project behind it
- License: CC0-1.0 (spec files and recorded examples)

Use it: `truewire import registry bitstamp` inside a Truewire project, or copy `spec/` and
the `[cores]` section of `truewire.toml` by hand. The examples replay through `truewire
mock`. Everything is served from `https://www.bitstamp.net`.

## What it shows

- **A discriminated union, twice, on the same tag.** `market_data.list_markets` and
  `market_data.get_ticker` both return `SPOT`/`PERPETUAL` variants of one shape, tagged by
  `market_type` -- a perpetual carries the contract terms (`max_leverage`, `mark_price`,
  `open_interest`, ...) a spot pair has none of. Verified by calling both variants of the
  ticker live (`btcusd` and `btcusd-perp`), not by reading the two shapes apart in prose.
- **A positional row.** An order book level is `[price, amount]`, declared once in
  `schemas.json` as `OrderBookLevel` and `$ref`'d from both `bids` and `asks`, bounded by
  `minItems`/`maxItems` so a row that lost its amount would stop validating.
- **A closed set found by asking the API, not by reading a docs page.** `asset_class` on a
  perpetual market is enumerated from every value the live market list carries today
  (`CRYPTO`, `FX`, `COMMODITIES`, `ETF`) -- Bitstamp trades perpetuals on more than crypto --
  rather than from a vocabulary Bitstamp publishes as closed.
- **String-wire timestamps.** `timestamp`, `date` and the OHLC candle's own `timestamp` are
  Unix seconds sent as a JSON *string*, not a number, and still declare `format:
  'epoch-seconds'` -- the format applies to the wire shape, not to whichever JSON type
  happens to carry it.
- **A documented parameter that does nothing, said out loud instead of declared.**
  `market_data.get_ohlc`'s `start`/`end`/`limit` look exactly like a `window` pagination
  walk. Called directly, `start` turned out to have no effect on the response at all once
  `end` and `limit` are both set -- verified live, following the authoring guide's own
  advice to probe before declaring bound inclusivity. No `pagination` block is declared;
  the endpoint's `notes` say why, so nobody completes it from the parameter names alone.

## Recordings

Every endpoint carries request halves with real parameters and declares `unverified`
(`not_captured`): this spec was authored directly against the live API from this
repository, not copied from a working client, so it has no recordings of its own yet. The
[Record workflow](../../.github/workflows/record.yml) generates a throwaway client from
this spec and replays these requests against `https://www.bitstamp.net` to capture them.

Market data is not reproducible byte-for-byte -- a re-recorded ticker or order book is a
different snapshot of a live market. That is the endpoint, not a defect in the example; the
schema is what a recording is checked against, not the exact numbers.
