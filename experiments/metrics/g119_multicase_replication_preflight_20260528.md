# G119 Multi-Case Replication Preflight

Date: 2026-05-28

Verdict:

```text
PASS_G119_MULTICASE_PREFLIGHT_RECORDED
```

Case readiness:

| source split | complete | missing count | next action |
| --- | --- | ---: | --- |
| 220700191 | True | 0 | already complete as single-case diagnostic; use as case 1 |
| 222200042 | False | 4 | wait for an actually idle GPU, then run source prep, Zero123++, manifest build, direct/frustum guard if needed, and G117-style eval |

GPU status:

```text
gpu 0: used=62497MB util=98 empty=False
gpu 1: used=60339MB util=98 empty=False
gpu 2: used=55887MB util=98 empty=False
gpu 3: used=46421MB util=98 empty=False
gpu 4: used=59497MB util=98 empty=False
gpu 5: used=60919MB util=98 empty=False
gpu 6: used=63633MB util=98 empty=False
gpu 7: used=65987MB util=98 empty=False
```

Decision:

```text
Multi-case replication is not complete: only source 220700191 has the full direct/naive/G110/G117 contract. Source 222200042 has a direct diagnostic but lacks pseudo input, Zero123++ pseudo views, manifests, and G117-style ablations. No empty GPU is available now, so do not launch the missing GPU runs in this turn.
```

Next gate:

```text
G120 should execute source 222200042 replication only when an empty GPU is available, then rerun G118-style aggregation across cases.
```
