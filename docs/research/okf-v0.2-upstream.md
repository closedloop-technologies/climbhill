# OKF v0.2 upstream source

Research date: 2026-08-19. Sources below are first-party Google Cloud or the
upstream GoogleCloudPlatform repository.

## Finding

The authoritative upstream is
[`GoogleCloudPlatform/knowledge-catalog`](https://github.com/GoogleCloudPlatform/knowledge-catalog).
Google Cloud's v0.2 announcement identifies that repository's `okf/` directory
as the location of the v0.2 spec, samples, and reference implementation, while
the upstream README links `okf/SPEC.md` specifically as the "Open Knowledge
Format v0.2 specification." ([announcement](https://cloud.google.com/blog/products/data-analytics/okf-v0-2-adds-trust-signals/),
[README at the pin](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/README.md))

Use this immutable pin:

- Version declared by the document: `0.2`.
- Commit: [`3fcbb9f828c2f23d109c855ee403c3a4c81f3a96`](https://github.com/GoogleCloudPlatform/knowledge-catalog/commit/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96).
- Commit date: `2026-07-24T09:45:43-07:00`.
- That commit changes the heading from `Version 0.2 (Draft)` to `Version 0.2`;
  its parent, `780fe9d30b5bbca8931256edf1d0290d6bda5462`, is the initial v0.2 migration.

As checked on the research date, `main` was
`e7e4660d14586e6bf39a94ec47de6fb1c43b8dfd` and still contained the identical
spec blob. The earlier finalization commit is the clearer semantic pin.

## Complete vendored set

The complete **normative specification is one file**. The spec says it is
self-contained and specifies everything needed to produce and consume OKF
v0.2; the README separately describes the agent and visualizer as proofs of
concept. Therefore sample bundles, source code, tests, and `okf/README.md` are
informative, not parts of the normative specification.
([spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/SPEC.md),
[README](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/README.md))

| Role | Upstream path | Raw immutable URL | SHA-256 | Git blob | Bytes |
| --- | --- | --- | --- | --- | ---: |
| Normative spec | `okf/SPEC.md` | [raw](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/SPEC.md) | `5a3311d270bebb16d558010e75064f5b75323f284992641732b1c8097511f948` | `a516d50128f5aa1f5746d1464661a39f7143e875` | 37,544 |
| License accompaniment | `okf/LICENSE.md` | [raw](https://raw.githubusercontent.com/GoogleCloudPlatform/knowledge-catalog/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/LICENSE.md) | `8c6db340475136df3c1201d458fa5755698eace76e510471ecc9d857d6083dac` | `6b0b1270ff0ca8f03867efcd09ba6ddb6392b1e1` | 11,359 |

The license is [Apache License 2.0](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/3fcbb9f828c2f23d109c855ee403c3a4c81f3a96/okf/LICENSE.md).
At the pin, root `LICENSE.md` is byte-identical to `okf/LICENSE.md`, and there is
no `NOTICE` file. Include `okf/LICENSE.md` when redistributing the vendored spec,
but do not label it as normative specification content.

## Vendoring ambiguity and recommendation

Upstream publishes no Git tag and no GitHub release for v0.2
([tag refs](https://api.github.com/repos/GoogleCloudPlatform/knowledge-catalog/git/matching-refs/tags/),
[releases](https://api.github.com/repos/GoogleCloudPlatform/knowledge-catalog/releases)).
Consequently, `v0.2` or `main` alone is not a reproducible source identifier.
Vendor the two files above from commit
`3fcbb9f828c2f23d109c855ee403c3a4c81f3a96`, preserve their bytes, and record
the version, commit, raw URLs, retrieval date, and checksums in a separate
manifest rather than modifying `SPEC.md`. Any copied README, samples, or tools
should be explicitly marked informative.

Checksums were verified both from the Git blobs and by downloading the pinned
raw URLs and running `sha256sum`.
