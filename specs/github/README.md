# github

GitHub REST API, repository-scoped: repositories, commits, tags, releases, issues.

- Upstream docs: https://docs.github.com/en/rest
- Endpoints: 6 (6 with recorded examples)
- Coverage: not surveyed against the vendor's documentation; this spec may be a sample
- Source project (core, generated client, tests): https://github.com/truewire-dev/truewire/tree/main/examples/github
- License: CC0-1.0 (spec files and recorded examples)

Use it: `truewire import registry github` inside a Truewire project, or copy `spec/` and the
`[cores]` section of `truewire.toml` by hand. The examples replay through `truewire mock`.
