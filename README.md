# Truewire registry

API specs with recorded wire examples, one directory per API, CC0. Start a typed client
from evidence instead of from a docs page:

```bash
pip install truewire
truewire init myproject && cd myproject
truewire import registry github        # copies spec/ and the [cores] section
truewire generate python
truewire mock                          # replays the recorded examples locally
```

Every spec here passes `truewire check` and `truewire examples --require-verified` in CI:
each endpoint is backed by a recorded example, or declares why it is not. The table below
says which, per spec, and [Recording](#recording) says how a declaration becomes a
recording.

## Layout

```
registry.json            index: name, description, upstream, transports, counts, status, source
specs/<name>/
  README.md              what it covers, coverage numbers, where it came from
  truewire.toml          [project], [spec] and [cores] (core metadata schemas); no [python]
  spec/
    endpoints/**/endpoint.json, router.json, examples/
    schemas.json         shared shapes
scripts/check_index.py   CI: the index matches the tree
scripts/record.py        records a spec's examples against the live API
scripts/recording_status.py  CI: which specs have evidence, and which have a declaration
.github/workflows/record.yml  runs scripts/record.py on a runner and opens a pull request
```

A spec is only the spec: the schemas, the declared blocks (pagination, envelope, redaction,
push, unverified) and the recordings. Where a spec came out of a working client, the
hand-written core, the generated package and the tests stay in that project, linked from
each `README.md` as `source`; where it was authored here, `source` points back at this
repository and the spec is the whole of it.

## Specs

| Name | Endpoints | Recorded | Coverage | Transports | Status |
| --- | --- | --- | --- | --- | --- |
| `bitstamp` | 5 | 5 | ? | http | recorded |
| `coinbase-exchange` | 6 | 6 | ? | http | recorded |
| `github` | 6 | 6 | ? | http | recorded |
| `hacker-news` | 5 | 5 | ? | http | recorded |
| `kraken` | 75 | 62 | ? | http, ws | partial |
| `open-library` | 3 | 3 | ? | http | recorded |
| `open-meteo` | 7 | 7 | ? | http | recorded |
| `usgs-earthquakes` | 3 | 3 | ? | http | recorded |

(`registry.json` is the source of truth; CI fails if this table's numbers drift from it.)

**Recorded** counts endpoints holding a complete example pair -- a request beside the response
the API actually sent. **Coverage** is endpoints in the spec against endpoints in the vendor's
own documentation, declared per spec as `documented` with a source and a survey date; `?`
means nobody has surveyed the docs yet, so the spec may be a sample of the API rather than
the API. A spec is complete when the two numbers match. **Status** is derived from the tree, never asserted:

| Status | What it means |
| --- | --- |
| `recorded` | Every endpoint has a recorded pair. |
| `partial` | The rest declare `unverified` for a reason a recording run cannot fix: a credential, account state, an effectful call. |
| `unrecorded` | Something still declares `unverified` with reason `not_captured` -- the spec is written and checked, and the recordings are waiting on a run of the Record workflow. |

## Recording

A registry spec is only the spec. It has no core, no generated package and no base URL, so
by itself it cannot call anything -- which is why an endpoint's request half sits here
without its response until something runs the call.

`scripts/record.py` is that something. For one spec it:

1. `truewire init`s a throwaway project, whose default core template is one HTTP transport
   with a base URL and no auth;
2. copies the spec in and splices the spec's own `[cores]` tables over the template's, so
   every endpoint's `meta` validates against the schema it was written for;
3. runs `truewire generate python`;
4. replays every `examples/<id>.request.json` through that client with `truewire capture`,
   which writes `<id>.response.json` beside it and drops the endpoint's now-false
   `unverified` declaration;
5. copies the spec tree back, and refreshes this table and `registry.json` from it.

The base URLs come from the spec's `recording.hosts` in `registry.json`, one entry per
endpoint group, because nothing in a spec states a host. Run it locally with network
access, or from Actions: **Record > Run workflow**, optionally naming one spec. The workflow
re-runs every gate over what it recorded and opens a pull request; nothing is committed to
`main` by a machine.

**Only a spec whose entry says `recording.recordable: true` is ever recorded this way, and
that means two things.** The API is public and credential-free -- the workflow reads no
secret and references no `secrets` context, so a spec needing a key stays unrecorded here
and says why in `recording.reason`, to be recorded in its own source project against a real
credential. And no endpoint declares `envelope.payload`: the throwaway core is a
pass-through that hands the whole body to validation, so a spec whose core is supposed to
unwrap a frame needs that core, and `scripts/check_index.py` refuses the combination rather
than letting the run fail confusingly.

### Listed but unverified

A spec listed `unrecorded` is a spec whose every claim is still a claim. It has been
checked -- `truewire check` holds it to the authoring rules, `scripts/check_index.py` to
its own counts -- and it has been read against the API's documentation. What it has not
been held to is the API itself. Nothing has confirmed that a field it names exists, that a
type it declares is what arrives, or that the endpoint answers at all.

`truewire examples --require-verified` passes on such a spec, and that is deliberate rather
than an oversight: the gate excuses an endpoint that declares `unverified`, which is what
lets a credential-bound endpoint stay in a spec honestly instead of being deleted or faked.
The same excuse is what lets a brand-new spec through with no evidence at all. So the gate
is not tightened; the split is reported instead. The `recorded` CI job prints the table
above, warns on every spec still waiting for a recording run, and fails a spec that claims
`recorded` while its tree says otherwise.

Read a spec's status before you trust it: `recorded` means every endpoint has been called
and its answer kept; `unrecorded` means nobody has called it yet from here.

## Adding a spec

The full path is to build it as a Truewire project first -- a core, a generated client and
tests that pass against `truewire mock` -- and copy the finished spec here. The
[agent skills](https://github.com/truewire-dev/truewire/tree/main/.agents/skills) are the
path from a docs URL to that. A spec for a public, credential-free API can also be authored
here directly and recorded by the workflow; `specs/hacker-news`, `specs/open-library` and
`specs/usgs-earthquakes` were.

1. Copy `spec/` and `truewire.toml` (drop `[python]`) into `specs/<name>/`, or author them
   there. Write `specs/<name>/README.md`: what it covers, the coverage numbers, and a link
   to the source project where there is one.
2. Every endpoint gets at least one example. Give it the request half -- real, reproducible
   parameters -- and, until it has been recorded, an `unverified` block with reason
   `not_captured`. Never write a response half by hand: a response is evidence, and one
   nobody recorded is the thing this registry exists not to publish.
3. Add the entry to `registry.json`, including the `recording` block: `recordable: true`
   with a `hosts` map for a public API, or `recordable: false` with a `reason`. Run
   `python scripts/check_index.py`.
4. Run the Record workflow on the new spec, and merge the pull request it opens. Scrub
   anything the API served that should not be committed -- no credentials, no personal data
   beyond what it serves publicly; `truewire capture --scrub KEY` does it at recording time.
5. Open a pull request. CI runs `check`, the spec-only half of `standards` (which includes
   `examples --require-verified`) and the index checks on every spec.

By contributing a spec you agree to release it under CC0 1.0 (see `LICENSE`).

## License

CC0 1.0 Universal for everything under `specs/`; MIT for `scripts/` and the workflow. The
toolchain that reads these specs is Apache-2.0 at
[truewire-dev/truewire](https://github.com/truewire-dev/truewire).
