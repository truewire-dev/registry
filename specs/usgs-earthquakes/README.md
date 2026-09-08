# usgs-earthquakes

USGS earthquake data: the real-time GeoJSON summary feeds, and the FDSN event service for
querying the ANSS Comprehensive Catalog. Public, no key.

- Upstream docs: https://earthquake.usgs.gov/fdsnws/event/1/
- Endpoints: 3 (0 with recorded examples)
- Source project (core, generated client, tests): authored in this repository; there is no
  separate project behind it
- License: CC0-1.0 (spec files and recorded examples)

Use it: `truewire import registry usgs-earthquakes` inside a Truewire project, or copy
`spec/` and the `[cores]` section of `truewire.toml` by hand. The examples replay through
`truewire mock`. Everything is served from `https://earthquake.usgs.gov`.

## What it shows

- **A positional row, twice.** A GeoJSON point's `coordinates` is `[longitude, latitude,
  depth]` and a FeatureCollection's `bbox` is six numbers, both declared with `prefixItems`
  and bounded by `minItems`/`maxItems` so a row that loses a column stops validating.
- **Epoch milliseconds.** `properties.time`, `properties.updated` and `metadata.generated`
  all declare `format: epoch-millis`, so they render as `datetime` rather than as an `int`
  nobody converts.
- **An envelope kept, not unwrapped.** The response schema is the whole FeatureCollection.
  `metadata.count`, `metadata.generated` and `bbox` are things a caller wants, so this is
  authoring rule 6's "keep the envelope" branch: no `envelope` block, and the generated
  method returns the frame.
- **Pagination that cannot be declared, said out loud.** `events.query` paginates, and
  carries no `pagination` block: its `offset` counts from 1 where the `offset` strategy
  starts at 0, and `metadata.count` disappears from the response the moment `limit` is sent,
  which would make a `total` terminator raise on every page of a walk. The endpoint's
  `notes` say so, so nobody later completes the block from the parameter names alone.
- **Enums that are real, and strings that stay strings.** `status` and `alert` have
  documented closed vocabularies and are `enum`s; `magType` and the event `type` do not, and
  are left plain, because a guessed `Literal` rejects valid responses.

## Recordings

Every endpoint carries request halves with real, reproducible parameters -- a week of the
2024 Noto Peninsula sequence, a month around Grindavik -- and declares `unverified` with
reason `not_captured` until a run of the
[Record workflow](../../.github/workflows/record.yml) fills in the responses.

The two summary-feed examples are the exception to "reproducible": a feed regenerates every
minute, so re-recording `significant_week` records a different week. That is the endpoint,
not a defect in the example.
