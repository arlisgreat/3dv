# G50 NeRSemble Official Intake

Date: 2026-05-24

Verdict:

```text
PARTIAL_PASS_SVFR_AND_V2_METADATA_READY
```

Official access URLs used:

```text
NERSEMBLE_DATA_URL=https://kaldir.vc.cit.tum.de/nersemble/v2
NERSEMBLE_BENCHMARK_URL=https://kaldir.vc.cit.tum.de/nersemble/benchmark_v1
```

Downloaded locally:

| Scope | Local path | Files | Size | Status |
| --- | --- | ---: | ---: | --- |
| SVFR benchmark RGB inputs | `datasets/nersemble_benchmark/svfr` | 391 | 128M | complete, manifest has 0 failures |
| NeRSemble v2 README/metadata/calibrations | `datasets/nersemble_v2` | 839 | 12M | complete, 418 camera params + 418 color calibration JSONs |
| NVS benchmark video/metadata | `datasets/nersemble_benchmark/nvs` | 18 | 53M | partial only; paused due low official-server throughput |

Manifests:

```text
datasets/nersemble_svfr_manifest.tsv
datasets/nersemble_v2_calibrations_manifest.tsv
```

Network policy:

```text
Local SSH reverse proxy variables were unset for the downloads.
```

Notes:

```text
SVFR benchmark access provides official input images for the submission task; it
does not provide local GT meshes. NVS/mono benchmark videos are resumable through
scripts/download_nersemble_official.py, but full video intake should be run as a
long background/data-transfer task because the official server was slow from
this host.
```
