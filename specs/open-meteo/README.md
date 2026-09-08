# open-meteo

Open-Meteo: weather forecasts, historical weather (ERA5), air quality, marine and flood
forecasts, geocoding and elevation. Free for non-commercial use, no key.

- Upstream docs: https://open-meteo.com/en/docs
- Endpoints: 7 (7 with recorded examples)
- Source project (core, generated client, tests): https://github.com/truewire-dev/open-meteo
- License: CC0-1.0 (spec files and recorded examples)

Use it: `truewire import registry open-meteo` inside a Truewire project, or copy `spec/` and
the `[cores]` section of `truewire.toml` by hand. The examples replay through `truewire mock`.

## Hosts

Open-Meteo is one API style spread over several hosts, so a core built on this spec holds one
transport per endpoint group rather than a host per endpoint. `registry.json` carries the same
map for the Record workflow:

| Group | Host |
| --- | --- |
| `weather` | `https://api.open-meteo.com` |
| `archive` | `https://archive-api.open-meteo.com` |
| `geocoding` | `https://geocoding-api.open-meteo.com` |
| `air_quality` | `https://air-quality-api.open-meteo.com` |
| `marine` | `https://marine-api.open-meteo.com` |
| `flood` | `https://flood-api.open-meteo.com` |

The commercial tier serves the same paths from `customer-*.open-meteo.com` with an `apikey`
query parameter, which every endpoint declares `redacted`. Nothing here needs it.

## Recordings

Every endpoint carries the request half of at least one example -- real coordinates, a real
date range -- and the response the free hosts sent when those parameters were replayed
through a client generated from this spec. The
[Record workflow](../../.github/workflows/record.yml) is what replays them: it builds that
client, records with `truewire capture` and opens a pull request with what came back.

A forecast is a forecast, so re-recording moves every number. What it must not move is the
*shape*: `truewire check` replays each recording against its endpoint's response schema, so
a re-record is also a test that this spec still describes what Open-Meteo sends.

## What it shows

- **Series are maps, not records.** `hourly`, `daily` and `current` are typed as maps keyed
  by the variable names the request asked for, because the API offers several hundred and
  adds more; a record would have had to guess them.
- **A wire type the caller chooses.** `timeformat` switches the series' `time` axis between
  zone-less local ISO strings and Unix seconds, so a column is a union of a string array and
  a numeric one, and the `*_units` map beside each series says which arrived. `unixtime.request.json`
  on `weather.forecast` records that second reading.
- **Query parameters that are lists.** `hourly=temperature_2m,precipitation` is one
  comma-joined parameter, spec'd as an array.
