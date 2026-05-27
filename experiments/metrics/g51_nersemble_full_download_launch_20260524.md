# G51 NeRSemble Full Download Launch

Date: 2026-05-24

Verdict:

```text
FULL_DOWNLOAD_IN_PROGRESS
```

Scope:

```text
NeRSemble benchmark v1:
  - SVFR
  - NVS
  - mono_flame_avatar

NeRSemble dataset v2:
  - README and metadata CSVs
  - all participant camera/color calibrations
  - all participant background images
  - all available sequence videos for all listed cameras
```

Official URLs:

```text
NERSEMBLE_DATA_URL=https://kaldir.vc.cit.tum.de/nersemble/v2
NERSEMBLE_BENCHMARK_URL=https://kaldir.vc.cit.tum.de/nersemble/benchmark_v1
```

Runtime:

```text
pid file: /data1/workspace/airulan/3dv_work/status/nersemble_full_download.pid
log: /data1/workspace/airulan/3dv_work/logs/nersemble_full_setsid_20260525_000223.log
manifest: datasets/nersemble_full_manifest.tsv
workers: 128
```

Launch check:

```text
process: running
manifest rows observed: 464 including header
failures observed: 0
active curl workers observed: 128
```

Network policy:

```text
HTTP_PROXY, HTTPS_PROXY, ALL_PROXY and lowercase variants are unset for the
download process; NO_PROXY is set to "*".
```
