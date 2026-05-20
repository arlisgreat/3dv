# Benchmark Dataset Access Root

This directory is the local entry point for stronger real-GT benchmark access.
Raw face/head assets are intentionally kept out of git.

Current local links:

- `facescape_benchmark` -> official FaceScape SVFR benchmark data downloaded under `external/facescape/benchmark/data`
- `facescape_sample` -> official FaceScape sample data downloaded under `external/facescape/samples`
- `_tools/nersemble-benchmark` -> official NeRSemble benchmark downloader cloned through `ghfast.top`
- `_tools/nersemble-data` -> official NeRSemble v2 downloader cloned through `ghfast.top`
- `_tools/h3ds` -> official H3DS loader/evaluator cloned through `ghfast.top`

Credential-gated data targets:

- `nersemble_benchmark`: official NeRSemble benchmark data after `NERSEMBLE_BENCHMARK_URL` is available.
- `nersemble_v2`: official NeRSemble v2 dataset after `NERSEMBLE_DATA_URL` is available.
- `h3ds_v2`: official H3DS v2 dataset after `H3DS_ACCESS_TOKEN` is available.

Empty credential-gated directories are placeholders only. They are not valid
benchmark data and must not be used in claims until a data/VLM/distribution gate
passes after the official credentials arrive.

Use `scripts/download_benchmark_access_datasets.sh` from the repo root to retry
downloads without local SSH reverse proxy settings.
