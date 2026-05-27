# G52 NeRSemble Download Integrity Gate

Date: 2026-05-27

Premise:

```text
The downloaded NeRSemble v2 and official benchmark folders are real licensed benchmark inputs, not generated pseudo-view candidate pools. This gate checks presence and manifest integrity only; it does not authorize training or reconstruction-quality interpretation.
```

Verdict:

```text
PASS_NERSEMBLE_OFFICIAL_DATA_PRESENT_WITH_404_EXCLUSIONS
```

Directory summary:

| directory | exists | files | size | key suffix counts |
| --- | ---: | ---: | ---: | --- |
| `datasets/nersemble_v2` | True | 155432 | 1.4TB | mp4=147908, jpg=6685, json=836 |
| `datasets/nersemble_benchmark` | True | 828 | 3.2GB | mp4=310, png=391, pcd=5, npz=110 |

Manifest summary:

| field | value |
| --- | ---: |
| rows | 156339 |
| unique_paths | 156339 |
| ok_final_paths | 156260 |
| failed_final_rows | 79 |
| failed_final_existing_paths | 0 |
| retry_recovered_paths | 0 |

Metadata summary:

| field | value |
| --- | ---: |
| metadata_participants_exists | True |
| metadata_sequences_exists | True |
| metadata_participant_rows | 418 |
| metadata_sequence_rows | 418 |
| camera_params_json_count | 418 |
| color_calibration_json_count | 418 |

Failed final rows by participant:

```text
546: 26
548: 26
545: 25
056: 1
179: 1
```

Failed final rows by serial:

```text
222200041: 77
222200042: 1
220700191: 1
```

Representative failed final paths:

```text
/data1/workspace/airulan/3dv/datasets/nersemble_v2/056/sequences/SEN-04-two_plus_seven/images/cam_222200042.mp4
/data1/workspace/airulan/3dv/datasets/nersemble_v2/179/sequences/EXP-9-jaw-2/images/cam_220700191.mp4
/data1/workspace/airulan/3dv/datasets/nersemble_v2/545/sequences/BACKGROUND/image_222200041.jpg
/data1/workspace/airulan/3dv/datasets/nersemble_v2/545/sequences/GLASSES/images/cam_222200041.mp4
/data1/workspace/airulan/3dv/datasets/nersemble_v2/545/sequences/EXP-1-head/images/cam_222200041.mp4
/data1/workspace/airulan/3dv/datasets/nersemble_v2/545/sequences/EXP-3-cheeks+nose/images/cam_222200041.mp4
/data1/workspace/airulan/3dv/datasets/nersemble_v2/545/sequences/EXP-5-mouth/images/cam_222200041.mp4
/data1/workspace/airulan/3dv/datasets/nersemble_v2/545/sequences/EXP-6-tongue-1/images/cam_222200041.mp4
/data1/workspace/airulan/3dv/datasets/nersemble_v2/545/sequences/EXP-7-tongue-2/images/cam_222200041.mp4
/data1/workspace/airulan/3dv/datasets/nersemble_v2/545/sequences/EXP-8-jaw-1/images/cam_222200041.mp4
/data1/workspace/airulan/3dv/datasets/nersemble_v2/545/sequences/EXP-9-jaw-2/images/cam_222200041.mp4
/data1/workspace/airulan/3dv/datasets/nersemble_v2/545/sequences/HAIR/images/cam_222200041.mp4
```

Decision:

```text
Official NeRSemble data is locally present enough to start compact-case and benchmark adapter preflights, but it is not a full-complete download claim. Exclude the 79 final HTTP-404 paths, especially participant 545/546/548 cam_222200041, from any case selection or metric table.
```

Next gate:

```text
Run G53 official benchmark/compact-case preflight with local VLM/manual visual audit before any method run. Keep identifiable RGB/video frames outside GitHub unless explicitly reviewed.
```
