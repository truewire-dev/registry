# open-library

Open Library, the Internet Archive's open catalogue of books: search over works, and the
work and author records behind the results. Read access is public and needs no key.

- Upstream docs: https://openlibrary.org/developers/api
- Endpoints: 3 (3 with recorded examples)
- Coverage: not surveyed against the vendor's documentation; this spec may be a sample
- Source project (core, generated client, tests): authored in this repository; there is no
  separate project behind it
- License: CC0-1.0 (spec files and recorded examples)

Use it: `truewire import registry open-library` inside a Truewire project, or copy `spec/`
and the `[cores]` section of `truewire.toml` by hand. The examples replay through
`truewire mock`. Everything is served from `https://openlibrary.org`.

## What it shows

- **Declared pagination, with a terminator chosen rather than assumed.** `search.books`
  declares a `page` walk whose index starts at 1, sized by `limit`, ending on a short page.
  `numFound` is right there and is *not* used as a `total`: `numFoundExact` exists because
  the count is sometimes an estimate, and a walk that raises when its declared total moves
  is the wrong thing to hang on an estimate. The endpoint's notes say so, so the choice
  reads as a decision rather than an oversight.
- **A field that is genuinely two shapes.** A work's `description` and an author's `bio`
  are a bare string on some records and `{"type": "/type/text", "value": ...}` on others,
  because Open Library's editors have written both. Both are an `anyOf` of the two.
- **A frame kept, and the pagination paths that follow from it.** `numFound` and
  `numFoundExact` are things the caller asked for, so there is no `envelope` block and the
  method returns the frame; `done.rows` is therefore `docs`, read from the frame's root.
- **A map where the keys are open-ended.** An author's `remote_ids` is
  `additionalProperties`, not a record: the catalogues an author is linked to grow as
  editors add them.
- **Two fields deliberately left out.** `first_publish_date` on a work and
  `birth_date`/`death_date` on an author are free-form human text (`8 October 1920`), not
  dates. Declaring a date format on them would promise a conversion that fails, so they are
  absent and the endpoints' notes say why.

## Recordings

Every endpoint carries a request half -- a two-page search walk with `page` sent explicitly
on both, one work whose description is a string and one whose description is a typed value
-- and the response Open Library sent when it was replayed through a client generated from
this spec, by the [Record workflow](../../.github/workflows/record.yml). Every example names
a permanent key, so re-recording changes what the catalogue holds, not which records come
back: the string-versus-typed-value pair keeps testing both halves of that union.
