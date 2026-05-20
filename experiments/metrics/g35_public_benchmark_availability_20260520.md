# G35 Public Benchmark Availability

Date: 2026-05-20

Verdict:

```text
BLOCKED_NO_ADDITIONAL_READY_REAL_GT_BENCHMARK
```

Scope:

```text
Audit whether another public or local real-GT head benchmark is immediately
ready after G33.
```

Route matrix:

| Route | Status | Reason | Source |
| --- | --- | --- | --- |
| H3DS v2 | blocked | Local wheel/config only; no `H3DS_ACCESS_TOKEN` or dataset files available. | https://pypi.org/project/h3ds/ |
| FaceScape | blocked | Toolkit/sample metadata exists locally, but sample has limited images and redistribution is blocked; full licensed case is required. | https://nju-3dv.github.io/projects/FaceScape/ |
| Multiface | current route only | Local debug compact case is already the G21-G33 route; it is not a new benchmark and G33 shows no quality gain. | https://github.com/facebookresearch/multiface |
| NeRSemble | blocked | No compact local dataset found; access/download is required before a gate. | https://tobias-kirschstein.github.io/nersemble/ |
| Wikimedia/Blender CC0 head | positive-control only | Repo-safe synthetic plumbing control, not a real-capture benchmark. | https://commons.wikimedia.org/wiki/File:Head_(Sculpting)_-_Realistic_by_Dan_Ulrich_(CC0).stl |

Monitor report:

```text
/data1/workspace/airulan/3dv_work/agent_reports/benchmark_availability_g35_20260520.md
```

Decision:

```text
No additional ready real-GT quality benchmark is available locally. A new quality
milestone requires H3DS token/access, licensed FaceScape/NeRSemble data, or
another audited real-capture dataset.
```

Artifact policy:

```text
No new media was generated for this benchmark availability gate.
```
