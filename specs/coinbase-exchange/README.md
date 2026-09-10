# coinbase-exchange

Coinbase Exchange market data: the traded products, their tickers and trailing stats, the
trade tape, and OHLC candles. Public, no key, no passphrase, no signature.

- Upstream docs: https://docs.cdp.coinbase.com/exchange/reference
- Endpoints: 6 (6 with recorded examples)
- Coverage: not surveyed against the vendor's documentation; this spec may be a sample
- Source project (core, generated client, tests): authored in this repository; there is no
  separate project behind it
- License: CC0-1.0 (spec files and recorded examples)

Use it: `truewire import registry coinbase-exchange` inside a Truewire project, or copy
`spec/` and the `[cores]` section of `truewire.toml` by hand. The examples replay through
`truewire mock`. Everything is served from `https://api.exchange.coinbase.com`.

Only the public half of the API is here. The signed half — accounts, orders, transfers — is
HMAC-authenticated, and a spec nothing in this repository can record is a spec nobody should
trust, so it is left out rather than written from documentation.

## What it shows

- **`seek` pagination, for the first time in this registry.** `products.get_trades` is
  walked by the `trade_id` of the *last row of the previous page*, not by a token the API
  hands back — which is the whole distinction between `seek` and `token`. The cursor is a
  genuine per-row id, unique and monotonic per product, so no `overlap` is declared and the
  plain shape applies: `cursor.from: "[-1].trade_id"`, and the walk ends on an empty page.
  `done.rows` is omitted because the payload is itself the collection — the response is a
  bare array.
- **`window` pagination beside it.** `products.get_candles` is walked by moving a time
  range rather than a cursor. Both bounds are inclusive, so `step` is one second: a window
  whose `end` equalled the previous window's `start` would re-read the candle on the
  boundary. Checked against the live API rather than read off the documentation —
  `start=00:00Z&end=05:00Z` at hourly granularity returns six candles, not five.
- **A positional row that is not in the order you expect.** A candle is
  `[time, low, high, open, close, volume]` — low and high *before* open and close, which is
  not the usual OHLC order and is exactly the sort of thing a hand-written client gets
  wrong once and nobody notices until a chart looks odd. Declared with `prefixItems` and
  bounded by `minItems`/`maxItems`, so a row that loses a column stops validating.
- **Money as decimals, not floats.** Every price, size and volume outside the candles is a
  string on the wire and carries `format: decimal-string`, so it renders as a `Decimal`
  rather than a `float`. The candles are the exception, and are bare numbers on the wire;
  the schema says so rather than pretending otherwise.
- **A parameter whose name means the opposite of what it says.** `after` on the trade tape
  means *later in the walk*, which is *earlier in time*, because the tape is served newest
  first. The description says so, because that is where a caller will read it.

## The cap, measured

`products.get_candles` declares no `size`, so no truncation guard is generated for its walk.
That would be a real hole if the exchange truncated an over-wide range silently — the loss
Part 3 of the pagination series is about. It does not. It refuses:

```
$ …/candles?granularity=3600&start=2026-01-01T00:00:00Z&end=2026-01-13T12:00:00Z   # 301 candles
[ … 301 rows … ]
$ …/candles?granularity=3600&start=2026-01-01T00:00:00Z&end=2026-01-13T13:00:00Z   # 302 candles
{"message": "granularity too small for the requested time range.
             Count of aggregations requested exceeds 300"}
```

So a caller asking for too much finds out loudly, and there is nothing for a guard to catch.

This note previously said the opposite — that the exchange caps at 300 and says nothing —
which was assumed from the documented limit rather than measured. It is left corrected
rather than quietly rewritten, because the correction is the interesting part: whether an
endpoint truncates or refuses decides whether its client needs a guard at all, and the
documentation says neither.

## Recordings

Every endpoint carries the request half of at least one example and the response the
exchange sent when it was replayed through a client generated from this spec.

These recordings do not go stale, which is unusual and deliberate. A `trade_id` only ever
grows, so `after=1090000000` keeps returning the same page forever, and a candle window in
the past is permanent. Only `get_ticker` and `get_stats` move between runs, and both are
meant to — they are "right now" endpoints, and a re-recording that returned the same
numbers would mean the exchange had stopped.
