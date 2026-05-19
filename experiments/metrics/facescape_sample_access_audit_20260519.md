# FaceScape Sample Access Audit

Date: 2026-05-19

Gate verdict:

```text
PASS_METADATA_ACCESS
BLOCKED_REPO_IMAGE_EXPORT
BLOCKED_RECONSTRUCTION_CASE_UNTIL_LICENSED_DATA_OR_SAMPLE_POLICY_IS_RESOLVED
```

Local sample:

```text
/data1/workspace/airulan/3dv/external/facescape/samples
sample_tar_bytes: 37597885
mview_tuple: 4_anger
mview_param_views: 58
mview_valid_views: 52
available_mview_images: 2
keypoint3d_rows: 68
```

Available image metadata only:

| file | width | height | bytes |
| --- | ---: | ---: | ---: |
| 49.jpg | 2896 | 4344 | 1891233 |
| 50.jpg | 2896 | 4344 | 2056450 |

Interpretation:

```text
The sample confirms the intended GT route: calibrated camera parameters, valid flags,
high-resolution images, and a corresponding mesh are available in FaceScape format.
However, the sample readme explicitly says not to distribute it, so raw images,
mesh files, thumbnails, or rendered face figures stay out of git.
```

Next action:

```text
Use this only as a local parser/access check. For publishable reconstruction
validation, obtain licensed FaceScape access and use publishable-list subjects,
or use an alternate dataset with redistributable demo data.
```
