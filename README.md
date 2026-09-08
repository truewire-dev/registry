# Truewire registry

Verified API specs with recorded wire examples, one directory per API, CC0. Start a typed
client from evidence instead of from a docs page:

```bash
pip install truewire
truewire init myproject && cd myproject
truewire import registry github        # copies spec/ and the [cores] section
truewire generate python
truewire mock                          # replays the recorded examples locally
```

Every spec here passes `truewire check` and `truewire examples --require-verified` in CI:
each endpoint is backed by a recorded example, or declares why it is not.

## Layout

```
registry.json            index: name, description, upstream, transports, counts, source
specs/<name>/
  README.md              what it covers, coverage numbers, where it came from
  truewire.toml          [project], [spec] and [cores] (core metadata schemas); no [python]
  spec/
    endpoints/**/endpoint.json, router.json, examples/
    schemas.json         shared shapes
scripts/check_index.py   CI: the index matches the tree
```

A spec is only the spec: the schemas, the declared blocks (pagination, envelope, redaction,
push, unverified) and the recordings. The hand-written core, the generated client and the
tests live in the project that produced it, linked from each `README.md` as `source`.

## Specs

| Name | Endpoints | Recorded | Transports | Status |
| --- | --- | --- | --- | --- |
| `github` | 6 | 6 | http | recorded |
| `hacker-news` | 5 | 0 | http | unrecorded |
| `kraken` | 75 | 62 | http, ws | partial |
| `open-library` | 3 | 0 | http | unrecorded |
| `open-meteo` | 7 | 0 | http | unrecorded |
| `usgs-earthquakes` | 3 | 0 | http | unrecorded |

(`registry.json` is the source of truth; CI fails if this table's numbers drift from it.)

**Recorded** counts endpoints holding a complete example pair -- a request beside the response
the API actually sent. **Status** is derived from the tree, never asserted:

| Status | What it means |
| --- | --- |
| `recorded` | Every endpoint has a recorded pair. |
| `partial` | The rest declare `unverified` for a reason a recording run cannot fix: a credential, account state, an effectful call. |
| `unrecorded` | Something still declares `unverified` with reason `not_captured` -- the spec is written and checked, and the recordings are waiting on a run of the Record workflow. |

## Adding a spec

1. Build it as a Truewire project first, with a core, a generated client and tests that
   pass against `truewire mock`. The [agent skills](https://github.com/truewire-dev/truewire/tree/main/.agents/skills)
   are the path from a docs URL to that.
2. Copy `spec/` and `truewire.toml` (drop `[python]`) into `specs/<name>/`; write
   `specs/<name>/README.md` with the coverage numbers from `truewire examples` and a link to
   the source project.
3. Add the entry to `registry.json`; run `python scripts/check_index.py`.
4. Scrub every recording: no credentials, no personal data beyond what the API serves
   publicly. `truewire capture --scrub KEY` does it at recording time.
5. Open a pull request. CI runs `check` and `examples --require-verified` on every spec.

By contributing a spec you agree to release it under CC0 1.0 (see `LICENSE`).

## License

CC0 1.0 Universal for everything under `specs/`; MIT for `scripts/` and the workflow. The
toolchain that reads these specs is Apache-2.0 at
[truewire-dev/truewire](https://github.com/truewire-dev/truewire).
