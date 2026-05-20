# G48 Benchmark Intake Preflight

Date: 2026-05-20

Verdict:

```text
PASS_BENCHMARK_INTAKE_PREFLIGHT_READY_DATA_BLOCKED_BY_CREDENTIALS
```

Scope:

```text
Preconfigure stronger real-GT benchmark intake for NeRSemble and H3DS while credentials are pending. This checks tools, local raw-data policy, required credentials, and benchmark contracts without creating any method-quality result.
```

Credential state:

| credential | present | target |
| --- | --- | --- |
| NERSEMBLE_BENCHMARK_URL | False | official NeRSemble benchmark toolkit download |
| NERSEMBLE_DATA_URL | False | official NeRSemble v2 full data download |
| H3DS_ACCESS_TOKEN | False | official H3DS v2 encrypted archive download/extract |

Dataset/tool roots:

| key | exists | files | note |
| --- | --- | ---: | --- |
| datasets | True | 2 | local raw-data entry root; only README/access manifest are git-trackable |
| access_manifest | True | 0 | repo-safe access and license manifest |
| facescape_benchmark | True | 2142 | licensed/public FaceScape SVFR local support, not NeRSemble/H3DS substitute |
| nersemble_benchmark | True | 0 | awaits NERSEMBLE_BENCHMARK_URL |
| nersemble_v2 | True | 0 | awaits NERSEMBLE_DATA_URL; large optional full data |
| h3ds_v2 | True | 0 | awaits H3DS_ACCESS_TOKEN |
| tool_nersemble_benchmark | True | 60 | official benchmark downloader clone |
| tool_nersemble_data | True | 52 | official v2 downloader clone |
| tool_h3ds | True | 50 | official H3DS loader/evaluator clone |

Official benchmark contracts:

| benchmark | contract | expected gate use |
| --- | --- | --- |
| NeRSemble benchmark NVS | Official toolkit; 13 training cameras and 3 held-out cameras are used for benchmark metrics. | future native held-out RGB/geometry evaluation only after official URL approval |
| NeRSemble benchmark Mono FLAME Avatar | Single training camera plus held-out sequences/cameras; official 2026 update uses flame2023_tracking_v2. | head-anchored/feed-forward method evaluation, not pseudo-view training |
| NeRSemble benchmark SVFR | 391 images from 20 identities; submitted meshes are evaluated against held-out point clouds. | single-view geometry benchmark once data is official and license-reviewed |
| H3DS v2 | Official h3ds loader returns mesh, images, masks, and cameras; default view configs include 1, 3, 4, 6, 8, 16, and 32 views; evaluator reports comparable scene metrics. | few-shot full-head geometry/RGB support after H3DS_ACCESS_TOKEN and license review |

Git/raw-data policy:

```text
tracked_dataset_files=['datasets/README.md', 'datasets/access_manifest.tsv']
unexpected_tracked_dataset_files=['none']
raw FaceScape/NeRSemble/H3DS images, masks, meshes, pointclouds, archives, and renders must remain ignored/local
repo-safe sync is limited to README/access manifest, metrics, scripts, hashes, and non-identifiable aggregate figures
```

Blocked interpretations:

```text
Do not treat empty credential-gated directories as available benchmarks.
Do not use unofficial HF mirrors as source data without explicit provenance/license review.
Do not substitute FaceScape sample data for NeRSemble/H3DS method-quality claims.
Do not reintroduce experiments/downstream_datasets as training or evaluation data.
Do not publish identifiable benchmark RGB/mesh/pointcloud artifacts without explicit review.
```

Decision:

```text
The benchmark bench is configured enough for immediate intake once credentials arrive: official tool repos are cloned, raw-data roots are ignored, and the preflight records the required contracts. Actual NeRSemble/H3DS method-quality work remains blocked until official credentials/data pass data, VLM, distribution, and artifact gates.
```
