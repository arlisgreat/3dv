# G47 Benchmark Dataset Access Download

Date: 2026-05-20

Verdict:

```text
PARTIAL_ACCESS_PREFLIGHT_ONLY_NO_BENCHMARK_CLAIM
```

Downloaded/extracted locally:

| Dataset | Local path | Status |
| --- | --- | --- |
| FaceScape SVFR benchmark | `datasets/facescape_benchmark` | downloaded/extracted, 707M |
| FaceScape sample | `datasets/facescape_sample` | already downloaded/extracted, 95M |

Official tools cloned through `ghfast.top`:

| Tool | Local path | Commit |
| --- | --- | --- |
| NeRSemble benchmark | `external/nersemble-benchmark` | `e15f204dfc7cd8f822eac69a37383ce24628da5f` |
| NeRSemble v2 data | `external/nersemble-data` | `4a2430e7c9fd101e1e3d0662a9fa380a17bee732` |
| H3DS | `external/h3ds` | `987122657dcfbe0ca42b15f8804718d85add4dde` |

Credential-gated blockers:

| Dataset | Required credential |
| --- | --- |
| NeRSemble benchmark | `NERSEMBLE_BENCHMARK_URL` |
| NeRSemble v2 full dataset | `NERSEMBLE_DATA_URL` |
| H3DS v2 | `H3DS_ACCESS_TOKEN` |
| Full FaceScape release | official license/share link from FaceScape maintainers |

HuggingFace mirror scan:

| Candidate | Status | Reason |
| --- | --- | --- |
| `xzw123/NeRSemble` | not downloaded | 139GB public mirror listing, but no dataset card/license/provenance |
| `MahdiGhafourian/rendered_mini_FaceScape_db` | not downloaded | 694M and marked MIT, but FaceScape-derived provenance/redistribution policy is unclear |

Download policy:

```text
Avoid local SSH reverse HTTP/HTTPS proxy. Use ghfast.top for GitHub clones and
hf-mirror.com for HuggingFace candidates. Raw licensed face/head data remains
ignored by git.
```

Claim boundary:

```text
G47 is only access/download/tooling preflight. Empty NeRSemble/H3DS directories,
FaceScape sample data, and unofficial mirrors are not PASS_REAL_GT_BENCHMARK.
NeRSemble/H3DS method-quality claims remain blocked until official credentials
arrive and a later data/VLM/distribution/artifact gate passes.
```

Retry command:

```bash
bash scripts/download_benchmark_access_datasets.sh
```
