# Downstream Candidate Pool Semantics

Date: 2026-05-19

## Correction

`experiments/downstream_datasets/` is a historical path name. Semantically it is
not a validated training dataset.

It should be read as:

```text
pseudo-view candidate pools exported in a downstream-friendly layout
```

Likewise, `experiments/ri3d_datasets/` should be read as:

```text
RI3D-readable exports of those candidate pools for controlled ablations
```

## Why This Matters

The current screening metrics are useful but weak:

```text
CLIP/reliability scores catch some bad views but miss identity drift.
trusted-region masks catch background/photo-frame failures but do not prove geometry correctness.
face identity filtering separates identity_supervision / geometry_only / reject roles, but does not prove 3D usefulness.
```

G8-G14 downstream results show that filtered candidates can still produce
fragmented/card-like RI3D reconstructions. Therefore these directories are
candidate pools and diagnostic exports, not evidence that the contained views
are already suitable reconstruction supervision.

## Repository Rule

Keep the directory names for compatibility with existing scripts and historical
results, but use the following language in new docs:

```text
candidate pool
candidate export
RI3D-readable candidate scene
not a validated training set
```

Avoid language such as:

```text
validated downstream dataset
proved training set
ready reconstruction dataset
```

## Impact On G15

G15 should not scale the candidate pools as if they were training data. It
should first audit candidate quality across first10:

```text
reliability / CLIP score distribution
trusted-mask acceptance and reject reasons
identity filter roles
failure labels by sample group
small selected reconstruction examples only as diagnostics
```

The paper claim should remain failure-aware pseudo-view diagnosis unless a
stronger head-specific reconstruction backbone later validates a candidate
subset.
