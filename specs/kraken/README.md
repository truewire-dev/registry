# kraken

Kraken Spot: REST, WebSocket v2 streams and WebSocket trading RPC.

- Upstream docs: https://docs.kraken.com/api-reference/
- Endpoints: 75 (62 with recorded examples)
- Coverage: not surveyed against the vendor's documentation; this spec may be a sample
- Source project (core, generated client, tests): https://github.com/truewire-dev/truewire/tree/main/examples/kraken
- License: CC0-1.0 (spec files and recorded examples)

Use it: `truewire import registry kraken` inside a Truewire project, or copy `spec/` and the
`[cores]` section of `truewire.toml` by hand. The examples replay through `truewire mock`.
