# G53 NeRSemble Benchmark And Compact Case Gate

Date: 2026-05-27

Premise:

```text
NeRSemble must enter the project as a real licensed benchmark with explicit protocol constraints. Official benchmark assets configure NVS/Mono/SVFR tasks; full v2 videos only provide compact local multi-view cases after a visual/VLM gate.
```

Verdict:

```text
PASS_NERSEMBLE_COMPACT_CASE_LOCAL_VISUAL_AUDIT
```

Official benchmark protocol preflight:

| task | status | local files checked | missing files | interpretation |
| --- | --- | ---: | ---: | --- |
| NVS | pass | 140 | 0 | train cameras + first pointcloud local; official holdouts hidden |
| Mono FLAME Avatar | pass | 295 | 0 | single-camera train + FLAME tracking local |
| SVFR | pass | 391 pngs | 0 participants missing | official single-view input; hidden GT metrics |

Compact local candidates:

| rank | participant | sequence | input serial | eval serials | all 16 cams |
| ---: | --- | --- | --- | --- | ---: |
| 1 | 017 | EXP-1-head | 222200037 | 222200046, 220700191, 222200039 | 16 |
| 2 | 017 | FREE | 222200037 | 222200046, 220700191, 222200039 | 16 |
| 3 | 017 | EMO-1-shout+laugh | 222200037 | 222200046, 220700191, 222200039 | 16 |
| 4 | 017 | SEN-09-frown_events_bad | 222200037 | 222200046, 220700191, 222200039 | 16 |
| 5 | 018 | EXP-1-head | 222200037 | 222200046, 220700191, 222200039 | 16 |
| 6 | 018 | FREE | 222200037 | 222200046, 220700191, 222200039 | 16 |
| 7 | 018 | EMO-1-shout+laugh | 222200037 | 222200046, 220700191, 222200039 | 16 |
| 8 | 018 | SEN-09-frown_events_bad | 222200037 | 222200046, 220700191, 222200039 | 16 |
| 9 | 024 | EXP-1-head | 222200037 | 222200046, 220700191, 222200039 | 16 |
| 10 | 024 | FREE | 222200037 | 222200046, 220700191, 222200039 | 16 |

Local visual audit:

```text
{
  "audit_sheet": {
    "local_only_reason": "Contains licensed identifiable NeRSemble face frames; keep under 3dv_work and do not commit without explicit artifact review.",
    "path": "/data1/workspace/airulan/3dv_work/nersemble_audits/g53_nersemble_compact_case_audit_20260527.png",
    "serials": [
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200037",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200037.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200046",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200046.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "220700191",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_220700191.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200039",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200039.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200042",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200042.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200044",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200044.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200040",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200040.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200036",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200036.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200048",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200048.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200041",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200041.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200038",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200038.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200047",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200047.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200043",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200043.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200049",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200049.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "222200045",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_222200045.mp4"
      },
      {
        "frame_count": 647,
        "frame_index": 0,
        "serial": "221501007",
        "video": "/data1/workspace/airulan/3dv/datasets/nersemble_v2/017/sequences/EXP-1-head/images/cam_221501007.mp4"
      }
    ],
    "sha256": "b8a33ba28b3c08fb671c6c3a2ffe13e704e50a1c83b84b793a9cda2009c0933d"
  },
  "notes": "Local VLM/manual audit sheet shows one consistent participant across all 16 cameras at frame 0; views are real captured synchronized camera views, not generated pseudo views; no split-card, body-only, rotated-photo, or obvious multi-identity distortion observed. Licensed identifiable sheet remains local under 3dv_work.",
  "verdict": "PASS_NERSEMBLE_COMPACT_CASE_LOCAL_VISUAL_AUDIT"
}
```

Decision:

```text
Official benchmark protocols are locally configured and the selected compact v2 case passed local visual audit. This authorizes adapter/dataloader implementation, not a reconstruction-quality result.
```

Next gate:

```text
Implement a NeRSemble adapter that consumes only the selected audited case/protocol, keeps raw RGB local, declares train/test distribution, and evaluates held-out cameras before any method-quality claim.
```

Selected first compact case:

```text
participant=017 sequence=EXP-1-head input=222200037 eval=222200046,220700191,222200039
```
