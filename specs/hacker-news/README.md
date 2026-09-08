# hacker-news

The Hacker News API: items, users, the ranked story lists behind the site's own pages, and
the live-update feed. Public, unauthenticated, read-only, no key.

- Upstream docs: https://github.com/HackerNews/API
- Endpoints: 5 (0 with recorded examples)
- Source project (core, generated client, tests): authored in this repository; there is no
  separate project behind it
- License: CC0-1.0 (spec files and recorded examples)

Use it: `truewire import registry hacker-news` inside a Truewire project, or copy `spec/`
and the `[cores]` section of `truewire.toml` by hand. The examples replay through
`truewire mock`. Everything is served from `https://hacker-news.firebaseio.com`.

## What it shows

- **Responses that are not objects.** `stories.list` answers a bare array of ids and
  `live.max_item` answers a bare integer. There is no envelope, nothing to unwrap, and
  nothing to name: the generated method returns the list, or the number.
- **Epoch seconds.** `item.time` and `user.created` declare `format: epoch-seconds`, the
  other end of the range from a millisecond wire clock.
- **A path template that is not an id.** Six documented endpoints -- `topstories.json`,
  `askstories.json` and four more -- differ only by file name and answer the same shape, so
  they are one operation with the name as an `enum` parameter substituted into the path.
- **A record with optional fields, where a union would have been wrong.** An item is a
  story, a comment, a poll, a poll option or a job, and the API documents which fields are
  *typically* present per kind, never which are forbidden. So `Item` is one record with two
  required fields, and the endpoint's notes say why an `anyOf` of five variants would fail
  on a real item the moment one of them was too strict.

## The API's own shape for "not found"

An unknown item id or username answers `null` with HTTP 200. That is not an object, so it
does not validate against the response schema, and the spec does not pretend otherwise: it
is stated on both endpoints. Turning it into `None`, or into a `NotFound`, is a decision
for the core a caller writes, not something the spec can make for them.

## Recordings

Every endpoint carries request halves and declares `unverified` with reason `not_captured`
until a run of the [Record workflow](../../.github/workflows/record.yml) fills in the
responses. The item and user examples are permanent ids and re-record identically; the
story lists, the max item id and the update feed are live and re-record differently every
time.
